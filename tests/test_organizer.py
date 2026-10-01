"""Unit tests for tenant organizing packet generator."""

from unmask_llc.data.sample_generator import generate_sample_data
from unmask_llc.core.resolver import EntityResolver
from unmask_llc.core.organizer import TenantOrganizingPlanner


def test_generate_packet():
    properties, entities = generate_sample_data()
    resolver = EntityResolver()
    clusters = resolver.resolve_clusters(properties, entities)

    planner = TenantOrganizingPlanner()
    packet = planner.generate_packet(clusters[0], "1230 Market Street")

    assert packet.target_property.address == "1230 Market Street"
    assert len(packet.organizing_action_plan) >= 4
    assert "DEMAND LETTER" in packet.sample_demand_letter
    assert packet.total_portfolio_units > 0
