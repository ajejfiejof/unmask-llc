"""FastAPI API routes for UnmaskLLC frontend and web integration."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
import pandas as pd
import io

from unmask_llc.data.sample_generator import generate_sample_data
from unmask_llc.core.resolver import EntityResolver
from unmask_llc.core.graph import LandlordGraphBuilder
from unmask_llc.core.organizer import TenantOrganizingPlanner
from unmask_llc.core.models import Property, CorporateEntity, BeneficialOwnerCluster
from unmask_llc.core.normalizer import normalize_address, normalize_company_name

router = APIRouter(prefix="/api/v1")

# Global in-memory data store for live app
properties_store, entities_store = generate_sample_data()
resolver = EntityResolver()
clusters_store = resolver.resolve_clusters(properties_store, entities_store)


def refresh_clusters():
    global clusters_store
    clusters_store = resolver.resolve_clusters(properties_store, entities_store)


@router.get("/summary")
def get_summary():
    total_props = sum(c.total_properties for c in clusters_store)
    total_units = sum(c.total_units for c in clusters_store)
    total_evictions = sum(c.total_evictions for c in clusters_store)
    monopolistic_count = sum(1 for c in clusters_store if c.risk_level in ("Monopolistic", "High"))

    return {
        "status": "success",
        "metrics": {
            "total_properties": total_props,
            "total_housing_units": total_units,
            "total_clusters": len(clusters_store),
            "monopolistic_landlords_count": monopolistic_count,
            "total_evictions_3yr": total_evictions,
        },
        "top_clusters": [
            {
                "cluster_id": c.cluster_id,
                "canonical_name": c.canonical_name,
                "units": c.total_units,
                "properties": c.total_properties,
                "monopoly_score": c.monopoly_score,
                "risk_level": c.risk_level,
            }
            for c in clusters_store[:5]
        ],
    }


@router.get("/clusters")
def get_clusters():
    return {"clusters": [c.model_dump() for c in clusters_store]}


@router.get("/clusters/{cluster_id}")
def get_cluster_detail(cluster_id: str):
    for c in clusters_store:
        if c.cluster_id == cluster_id:
            return c.model_dump()
    raise HTTPException(status_code=404, detail="Cluster not found")


@router.get("/graph/{cluster_id}")
def get_cluster_graph(cluster_id: str):
    target_cluster: Optional[BeneficialOwnerCluster] = None
    for c in clusters_store:
        if c.cluster_id == cluster_id:
            target_cluster = c
            break

    if not target_cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    builder = LandlordGraphBuilder()
    g = builder.build_cluster_graph(target_cluster)
    return builder.export_vis_js_format(g)


@router.get("/search")
def search_entities(q: str = Query(..., min_length=2)):
    query = q.lower()
    matches = []

    for c in clusters_store:
        matched_props = [
            p.model_dump()
            for p in c.properties
            if query in p.address.lower() or query in p.city.lower() or query in p.zip_code
        ]
        matched_shells = [
            e.model_dump() for e in c.shell_entities if query in e.legal_name.lower()
        ]

        if matched_props or matched_shells or query in c.canonical_name.lower():
            matches.append(
                {
                    "cluster_id": c.cluster_id,
                    "parent_name": c.canonical_name,
                    "monopoly_score": c.monopoly_score,
                    "risk_level": c.risk_level,
                    "matched_properties": matched_props,
                    "matched_shells": matched_shells,
                    "total_portfolio_units": c.total_units,
                }
            )

    return {"query": q, "total_matches": len(matches), "results": matches}


@router.get("/organize/{cluster_id}")
def generate_organizing_packet(cluster_id: str, address: Optional[str] = None):
    target_cluster = None
    for c in clusters_store:
        if c.cluster_id == cluster_id:
            target_cluster = c
            break

    if not target_cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    planner = TenantOrganizingPlanner()
    target_addr = address or (target_cluster.properties[0].address if target_cluster.properties else "Target Property")
    packet = planner.generate_packet(target_cluster, target_addr)
    return packet.model_dump()


from fastapi.responses import Response
from unmask_llc.core.pdf_exporter import PDFDossierExporter
from unmask_llc.data.live_ingestor import fetch_live_sf_data


@router.get("/dossier/pdf/{cluster_id}")
def download_pdf_dossier(cluster_id: str, address: Optional[str] = None):
    target_cluster = None
    for c in clusters_store:
        if c.cluster_id == cluster_id:
            target_cluster = c
            break

    if not target_cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    planner = TenantOrganizingPlanner()
    target_addr = address or (target_cluster.properties[0].address if target_cluster.properties else "Target Property")
    packet = planner.generate_packet(target_cluster, target_addr)

    exporter = PDFDossierExporter()
    pdf_bytes = exporter.generate_pdf_bytes(packet)

    headers = {"Content-Disposition": f"attachment; filename=UnmaskLLC_Dossier_{cluster_id}.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/ingest/live/sf")
def ingest_live_sf_data(limit: int = 50):
    global properties_store, entities_store
    new_props, new_entities = fetch_live_sf_data(limit=limit)
    if new_props:
        properties_store.extend(new_props)
        entities_store.extend(new_entities)
        refresh_clusters()

    return {
        "status": "success",
        "fetched_properties": len(new_props),
        "total_clusters": len(clusters_store),
    }


@router.post("/ingest/csv")
async def ingest_csv(file: UploadFile = File(...)):
    global properties_store, entities_store
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    new_props = []
    new_entities = []

    for idx, row in df.iterrows():
        prop_id = f"custom_p_{idx}"
        ent_id = f"custom_e_{idx}"
        addr = str(row.get("address", f"Property {idx}"))
        city = str(row.get("city", "San Francisco"))
        state = str(row.get("state", "CA"))
        zip_code = str(row.get("zip_code", "94102"))
        units = int(row.get("units", 1))
        owner = str(row.get("recorded_owner_name", f"LLC {idx}"))
        agent_addr = str(row.get("registered_agent_address", "450 MISSION ST, SAN FRANCISCO, CA"))

        p = Property(
            id=prop_id,
            parcel_id=f"PARCEL-{idx}",
            address=addr,
            normalized_address=normalize_address(addr),
            city=city,
            state=state,
            zip_code=zip_code,
            units=units,
            recorded_owner_name=owner,
            normalized_owner_name=normalize_company_name(owner),
        )
        e = CorporateEntity(
            id=ent_id,
            legal_name=owner,
            normalized_name=normalize_company_name(owner),
            entity_type="LLC",
            state_of_inc=state,
            registered_agent_address=agent_addr,
        )
        new_props.append(p)
        new_entities.append(e)

    properties_store.extend(new_props)
    entities_store.extend(new_entities)
    refresh_clusters()

    return {
        "status": "success",
        "imported_properties": len(new_props),
        "imported_entities": len(new_entities),
        "total_clusters": len(clusters_store),
    }
