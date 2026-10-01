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
            label=f"🏢 {cluster.canonical_name}",
            group="ParentGroup",
            shape="box",
            margin=12,
            color={
                "background": "#e11d48",  # Rose-600
                "border": "#9f1239",
                "highlight": {"background": "#f43f5e", "border": "#881337"},
            },
            font={"color": "#ffffff", "size": 15, "bold": "true"},
            title=f"<div class='p-2 font-sans'><b>Parent Holding Entity:</b> {cluster.canonical_name}<br><b>Portfolio Housing Units:</b> {cluster.total_units}<br><b>Monopoly Score:</b> {cluster.monopoly_score}/100</div>",
        )

        # Add Shell LLC Nodes
        for e in cluster.shell_entities:
            shell_node_id = f"shell_{e.id}"
            g.add_node(
                shell_node_id,
                label=f"⚖️ {e.legal_name}",
                group="ShellLLC",
                shape="box",
                margin=10,
                color={
                    "background": "#2563eb",  # Blue-600
                    "border": "#1d4ed8",
                    "highlight": {"background": "#3b82f6", "border": "#1e40af"},
                },
                font={"color": "#ffffff", "size": 12},
                title=f"<div class='p-2 font-sans'><b>Shell LLC:</b> {e.legal_name}<br><b>Incorporation State:</b> {e.state_of_inc}<br><b>Status:</b> {e.status}</div>",
            )
            g.add_edge(
                parent_id,
                shell_node_id,
                title="Subsidiary Of Parent Group",
                color={"color": "#64748b", "highlight": "#e11d48"},
                width=2,
            )

            # Add Registered Agent Node
            if e.registered_agent_name:
                agent_node_id = f"agent_{hash(e.registered_agent_name) % 100000}"
                if not g.has_node(agent_node_id):
                    g.add_node(
                        agent_node_id,
                        label=f"👔 Agent: {e.registered_agent_name}",
                        group="RegisteredAgent",
                        shape="box",
                        margin=8,
                        color={
                            "background": "#d97706",  # Amber-600
                            "border": "#b45309",
                            "highlight": {"background": "#f59e0b", "border": "#78350f"},
                        },
                        font={"color": "#ffffff", "size": 11},
                        title=f"<div class='p-2 font-sans'><b>Registered Agent:</b> {e.registered_agent_name}<br><b>Address:</b> {e.registered_agent_address or 'N/A'}</div>",
                    )
                g.add_edge(
                    shell_node_id,
                    agent_node_id,
                    title="Registered Agent Infrastructure",
                    color={"color": "#f59e0b", "highlight": "#d97706"},
                    width=1.5,
                    dashes=True,
                )

            # Add Managing Member Nodes
            for member in e.managing_members:
                member_node_id = f"member_{hash(member) % 100000}"
                if not g.has_node(member_node_id):
                    g.add_node(
                        member_node_id,
                        label=f"👤 Officer: {member}",
                        group="ManagingMember",
                        shape="box",
                        margin=8,
                        color={
                            "background": "#059669",  # Emerald-600
                            "border": "#047857",
                            "highlight": {"background": "#10b981", "border": "#065f46"},
                        },
                        font={"color": "#ffffff", "size": 11},
                        title=f"<div class='p-2 font-sans'><b>Managing Member / Principal:</b> {member}</div>",
                    )
                g.add_edge(
                    shell_node_id,
                    member_node_id,
                    title="Managed By Officer",
                    color={"color": "#10b981", "highlight": "#059669"},
                    width=1.5,
                )

        # Add Property Nodes
        for p in cluster.properties:
            prop_node_id = f"prop_{p.id}"
            g.add_node(
                prop_node_id,
                label=f"🏠 {p.address} ({p.units} units)",
                group="Property",
                shape="box",
                margin=10,
                color={
                    "background": "#7c3aed",  # Violet-600
                    "border": "#6d28d9",
                    "highlight": {"background": "#8b5cf6", "border": "#5b21b6"},
                },
                font={"color": "#ffffff", "size": 12, "bold": "true"},
                title=f"<div class='p-2 font-sans'><b>Property:</b> {p.address}, {p.city}, {p.state}<br><b>Housing Units:</b> {p.units}<br><b>Evictions (3yr):</b> {p.eviction_count_3yr}<br><b>Code Violations:</b> {p.building_code_violations}</div>",
            )

            # Link property to its matching shell LLC
            matched = False
            for e in cluster.shell_entities:
                if (
                    p.normalized_owner_name == e.normalized_name
                    or e.normalized_name in p.normalized_owner_name
                ):
                    g.add_edge(
                        f"shell_{e.id}",
                        prop_node_id,
                        title="Deed Owner Record",
                        color={"color": "#8b5cf6", "highlight": "#7c3aed"},
                        width=2,
                    )
                    matched = True
                    break
            if not matched and cluster.shell_entities:
                g.add_edge(
                    f"shell_{cluster.shell_entities[0].id}",
                    prop_node_id,
                    title="Deed Owner Record",
                    color={"color": "#8b5cf6", "highlight": "#7c3aed"},
                    width=2,
                )

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
