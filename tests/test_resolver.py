"""Unit tests for entity resolution and clustering logic."""

from unmask_llc.data.sample_generator import generate_sample_data
from unmask_llc.core.resolver import EntityResolver, UnionFind


def test_union_find():
    elements = ["a", "b", "c", "d"]
    uf = UnionFind(elements)
    uf.union("a", "b")
    uf.union("b", "c")
    assert uf.find("a") == uf.find("c")
    assert uf.find("d") != uf.find("a")


def test_entity_resolver_clustering():
    properties, entities = generate_sample_data()
    resolver = EntityResolver(confidence_threshold=0.60)
    clusters = resolver.resolve_clusters(properties, entities)

    assert len(clusters) >= 2
    # Check that Pacific Apex cluster was formed
    apex_cluster = next((c for c in clusters if "APEX" in c.canonical_name.upper()), None)
    assert apex_cluster is not None
    assert len(apex_cluster.shell_entities) >= 3
    assert len(apex_cluster.properties) >= 3
    assert apex_cluster.total_units > 100
    assert apex_cluster.monopoly_score > 50
