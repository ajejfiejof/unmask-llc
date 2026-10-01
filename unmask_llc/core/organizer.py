"""Tenant union organizing packet generator and strategic action planner."""

from typing import List
from unmask_llc.core.models import BeneficialOwnerCluster, Property, TenantOrganizingPacket


class TenantOrganizingPlanner:
    """Generates tactical organizing packets and campaign strategies for tenant unions."""

    def generate_packet(
        self, cluster: BeneficialOwnerCluster, target_address: str
    ) -> TenantOrganizingPacket:
        """Generates an organizing packet centered around a target property."""
        target_prop = None
        sister_props: List[Property] = []

        for p in cluster.properties:
            if target_address.lower() in p.address.lower() or target_address.lower() in p.normalized_address.lower():
                target_prop = p
            else:
                sister_props.append(p)

        if not target_prop:
            if cluster.properties:
                target_prop = cluster.properties[0]
                sister_props = cluster.properties[1:]
            else:
                # Mock property fallback
                target_prop = Property(
                    id="target_001",
                    parcel_id="PARCEL-001",
                    address=target_address,
                    normalized_address=target_address.upper(),
                    city="San Francisco",
                    state="CA",
                    zip_code="94103",
                    units=24,
                    recorded_owner_name=cluster.canonical_name,
                    normalized_owner_name=cluster.canonical_name.upper(),
                )

        shell_names = [e.legal_name for e in cluster.shell_entities]
        agents_and_officers = cluster.shared_registered_agents + cluster.shared_addresses

        action_plan = [
            f"1. Form Building Committee at {target_prop.address}: Canvas all {target_prop.units} units to identify shared issues (e.g. rent hikes, delayed repairs).",
            f"2. Cross-Building Outreach: Establish contact with tenant committees at sister properties ({', '.join([p.address for p in sister_props[:3]])}).",
            f"3. Joint Demand Submission: Serve a unified demand letter to parent entity '{cluster.canonical_name}' representing all {cluster.total_units} total housing units.",
            "4. Escalate to Collective Bargaining: Leverage multi-building tenant density for rent cap negotiations or rent strike authorization.",
            "5. File Public Record Complaints: Request joint inspection sweeps by Housing Code Enforcement across all identified portfolio addresses.",
        ]

        sample_demand_letter = self._build_sample_demand_letter(cluster, target_prop, sister_props)

        risk_summary = {
            "monopoly_score": cluster.monopoly_score,
            "risk_level": cluster.risk_level,
            "total_portfolio_units": cluster.total_units,
            "evictions_3yr": cluster.total_evictions,
            "building_violations": cluster.total_violations,
        }

        return TenantOrganizingPacket(
            cluster_id=cluster.cluster_id,
            parent_company_name=cluster.canonical_name,
            target_property=target_prop,
            sister_properties=sister_props,
            total_portfolio_units=cluster.total_units,
            total_portfolio_properties=cluster.total_properties,
            shell_company_web=shell_names,
            shared_agents_and_officers=agents_and_officers,
            organizing_action_plan=action_plan,
            sample_demand_letter=sample_demand_letter,
            risk_summary=risk_summary,
        )

    def _build_sample_demand_letter(
        self, cluster: BeneficialOwnerCluster, target_prop: Property, sister_props: List[Property]
    ) -> str:
        sisters_text = "\n".join([f"  - {p.address} ({p.units} units)" for p in sister_props[:5]])
        return f"""TENANT UNION FORMAL NOTICE & COLLECTIVE DEMAND LETTER

DATE: [Current Date]
TO BENEFICIAL OWNER / PARENT MANAGEMENT: {cluster.canonical_name}
ASSOCIATED SHELL ENTITIES: {', '.join([e.legal_name for e in cluster.shell_entities[:4]])}

RE: Collective Grievance & Demands for Property: {target_prop.address} ({target_prop.units} Units)
AND CO-SIGNING TENANTS FROM SISTER PORTFOLIO PROPERTIES:
{sisters_text}

To the Management of {cluster.canonical_name},

We, the tenants of {target_prop.address}, writing in solidarity with tenants across your portfolio of {cluster.total_units} total housing units, hereby serve formal notice of our collective tenant association.

Our investigation has revealed that despite operating under separate LLC shell entities, our properties are managed under the unified ownership of {cluster.canonical_name}.

WE HEREBY DEMAND THE FOLLOWING IMMEDIATE REMEDIAL ACTIONS:
1. Immediate cessation of non-statutory rent increases across all portfolio properties.
2. Immediate repair and inspection of all outstanding habitability code violations.
3. Recognition of the Tenant Association as the exclusive bargaining representative for residents.
4. Formal sit-down meeting with principal officers within 14 calendar days.

Signed in Solidarity,

The Joint Tenant Council of {target_prop.address} & Sister Portfolio Properties
UnmaskLLC Verification Reference: Cluster ID {cluster.cluster_id} (Risk Level: {cluster.risk_level})
"""
