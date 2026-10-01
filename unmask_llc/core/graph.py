"""Graph construction and network visualization export tools using NetworkX."""

from typing import Dict, Any, List
import networkx as nx

from unmask_llc.core.models import BeneficialOwnerCluster, Property, CorporateEntity


class LandlordGraphBuilder:
    """Builds interactive entity network graphs for visualization and analysis."""

    def __init__(self):
        self.graph = nx.Graph()

    def build_cluster_graph(self, cluster: BeneficialOwnerCluster) -> nx.Graph:
        """Constructs a network graph for a single beneficial owner cluster."""
        g = nx.Graph()

        # Add Parent Node
        parent_id = f"parent_{cluster.cluster_id}"
        g.add_node(
            parent_id,
            label=cluster.canonical_name,
            group="ParentGroup",
            shape="star",
            size=35,
            color="#ef4444",  # Red / High prominence
            title=f"<b>Parent Entity:</b> {cluster.canonical_name}<br><b>Units:</b> {cluster.total_units}<br><b>Monopoly Score:</b> {cluster.monopoly_score}/100",
        )

        # Add Shell LLC Nodes
        for e in cluster.shell_entities:
            shell_node_id = f"shell_{e.id}"
            g.add_node(
                shell_node_id,
                label=e.legal_name,
                group="ShellLLC",
                shape="ellipse",
                size=22,
                color="#3b82f6",  # Blue
                title=f"<b>Shell LLC:</b> {e.legal_name}<br><b>State:</b> {e.state_of_inc}<br><b>Status:</b> {e.status}",
            )
            g.add_edge(parent_id, shell_node_id, label="SUBSIDIARY_OF", color="#94a3b8")

            # Add Registered Agent Node
            if e.registered_agent_name:
                agent_node_id = f"agent_{hash(e.registered_agent_name) % 100000}"
                if not g.has_node(agent_node_id):
                    g.add_node(
                        agent_node_id,
                        label=f"Agent: {e.registered_agent_name}",
                        group="RegisteredAgent",
                        shape="diamond",
                        size=18,
                        color="#f59e0b",  # Amber
                        title=f"<b>Registered Agent:</b> {e.registered_agent_name}<br><b>Address:</b> {e.registered_agent_address or 'N/A'}",
                    )
                g.add_edge(shell_node_id, agent_node_id, label="AGENT_FOR", color="#fcd34d")

            # Add Managing Member Nodes
            for member in e.managing_members:
                member_node_id = f"member_{hash(member) % 100000}"
                if not g.has_node(member_node_id):
                    g.add_node(
                        member_node_id,
                        label=f"Member: {member}",
                        group="ManagingMember",
                        shape="triangle",
                        size=18,
                        color="#10b981",  # Emerald
                        title=f"<b>Managing Member/Officer:</b> {member}",
                    )
                g.add_edge(shell_node_id, member_node_id, label="MANAGED_BY", color="#6ee7b7")

        # Add Property Nodes
        for p in cluster.properties:
            prop_node_id = f"prop_{p.id}"
            g.add_node(
                prop_node_id,
                label=f"{p.address} ({p.units} units)",
                group="Property",
                shape="box",
                size=16,
                color="#8b5cf6",  # Purple
                title=f"<b>Property:</b> {p.address}, {p.city}, {p.state}<br><b>Units:</b> {p.units}<br><b>Evictions (3yr):</b> {p.eviction_count_3yr}<br><b>Violations:</b> {p.building_code_violations}",
            )

            # Link property to its matching shell LLC (or directly to parent if shell not listed)
            matched = False
            for e in cluster.shell_entities:
                if p.normalized_owner_name == e.normalized_name or e.normalized_name in p.normalized_owner_name:
                    g.add_edge(f"shell_{e.id}", prop_node_id, label="DEED_OWNER", color="#c084fc")
                    matched = True
                    break
            if not matched and cluster.shell_entities:
                # Link to first shell
                g.add_edge(f"shell_{cluster.shell_entities[0].id}", prop_node_id, label="DEED_OWNER", color="#c084fc")

        return g

    def export_vis_js_format(self, g: nx.Graph) -> Dict[str, Any]:
        """Exports NetworkX graph object to Vis.js Network JSON format."""
        nodes = []
        for n, attrs in g.nodes(data=True):
            node_dict = {"id": str(n), "label": attrs.get("label", str(n))}
            for k, v in attrs.items():
                if k != "label":
                    node_dict[k] = v
            nodes.append(node_dict)

        edges = []
        for u, v, attrs in g.edges(data=True):
            edge_dict = {"from": str(u), "to": str(v)}
            for k, val in attrs.items():
                edge_dict[k] = val
            edges.append(edge_dict)

        return {"nodes": nodes, "edges": edges}
