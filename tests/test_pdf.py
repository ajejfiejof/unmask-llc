"""Unit tests for ReportLab PDF dossier generation."""

from unmask_llc.data.sample_generator import generate_sample_data
from unmask_llc.core.resolver import EntityResolver
from unmask_llc.core.organizer import TenantOrganizingPlanner
from unmask_llc.core.pdf_exporter import PDFDossierExporter


def test_pdf_dossier_generation():
    properties, entities = generate_sample_data()
    resolver = EntityResolver()
    clusters = resolver.resolve_clusters(properties, entities)

    planner = TenantOrganizingPlanner()
    packet = planner.generate_packet(clusters[0], "1230 Market Street")

    exporter = PDFDossierExporter()
    pdf_bytes = exporter.generate_pdf_bytes(packet)

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")
