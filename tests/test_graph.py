"""Unit tests for graph construction and export."""

from unmask_llc.data.sample_generator import generate_sample_data
from unmask_llc.core.resolver import EntityResolver
from unmask_llc.core.graph import LandlordGraphBuilder


def test_build_cluster_graph():
    properties, entities = generate_sample_data()
    resolver = EntityResolver()
    clusters = resolver.resolve_clusters(properties, entities)

    builder = LandlordGraphBuilder()
    g = builder.build_cluster_graph(clusters[0])

    assert len(g.nodes) > 0
    assert len(g.edges) > 0

    vis_data = builder.export_vis_js_format(g)
    assert "nodes" in vis_data
    assert "edges" in vis_data
    assert len(vis_data["nodes"]) == len(g.nodes)
