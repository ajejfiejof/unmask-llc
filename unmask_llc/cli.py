"""Command Line Interface (CLI) for UnmaskLLC."""

import sys
import argparse
import json
import uvicorn

from unmask_llc.data.sample_generator import generate_sample_data
from unmask_llc.core.resolver import EntityResolver
from unmask_llc.core.organizer import TenantOrganizingPlanner
from unmask_llc.core.graph import LandlordGraphBuilder


def main():
    parser = argparse.ArgumentParser(
        description="UnmaskLLC: Automated Corporate Landlord Entity Resolution & Tenant Union Graph Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run entity resolution on sample/loaded dataset")
    run_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search for property ownership or shell entity")
    search_parser.add_argument("query", help="Address or company name to search")

    # Command: packet
    packet_parser = subparsers.add_parser("packet", help="Generate tenant organizing packet for an address")
    packet_parser.add_argument("address", help="Target property address")
    packet_parser.add_argument("--output", help="Path to save markdown organizing packet")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch interactive web server dashboard")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port number")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load data and run resolver
    props, entities = generate_sample_data()
    resolver = EntityResolver()
    clusters = resolver.resolve_clusters(props, entities)

    if args.command == "run":
        if args.format == "json":
            out = [c.model_dump() for c in clusters]
            print(json.dumps(out, indent=2))
        else:
            print("\n=== UNMASK-LLC ENTITY RESOLUTION SUMMARY ===")
            print(f"Resolved {len(props)} properties and {len(entities)} corporate entities into {len(clusters)} beneficial ownership clusters.\n")
            for c in clusters:
                print(f"🏢 [{c.risk_level.upper()} RISK] Parent Entity: {c.canonical_name}")
                print(f"   - Shell LLC Count: {len(c.shell_entities)}")
                print(f"   - Total Properties: {c.total_properties} | Total Housing Units: {c.total_units}")
                print(f"   - Monopoly Score: {c.monopoly_score}/100 | Evictions (3yr): {c.total_evictions}")
                print("   - Portfolio Addresses:")
                for p in c.properties:
                    print(f"     * {p.address}, {p.city}, {p.state} ({p.units} units)")
                print()

    elif args.command == "search":
        q = args.query.lower()
        found = False
        print(f"\nSearching for: '{args.query}'...\n")
        for c in clusters:
            match_props = [p for p in c.properties if q in p.address.lower() or q in p.city.lower()]
            match_shells = [e for e in c.shell_entities if q in e.legal_name.lower()]
            if match_props or match_shells or q in c.canonical_name.lower():
                found = True
                print(f"MATCH FOUND -> Parent Cluster: {c.canonical_name} (Monopoly Score: {c.monopoly_score}/100)")
                print(f"Risk Level: {c.risk_level} | Total Portfolio Units: {c.total_units}")
                print(f"Shell LLCs: {', '.join([e.legal_name for e in c.shell_entities])}")
                print("Properties:")
                for p in c.properties:
                    print(f"  - {p.address}, {p.city}, {p.state} [{p.units} units]")
                print()
        if not found:
            print("No matching entity or property found.")

    elif args.command == "packet":
        planner = TenantOrganizingPlanner()
        target_cluster = None
        for c in clusters:
            for p in c.properties:
                if args.address.lower() in p.address.lower():
                    target_cluster = c
                    break
            if target_cluster:
                break

        if not target_cluster and clusters:
            target_cluster = clusters[0]

        packet = planner.generate_packet(target_cluster, args.address)
        if args.output:
            with open(args.output, "w") as f:
                f.write(f"# Tenant Organizing Packet: {packet.parent_company_name}\n\n")
                f.write(f"Target Property: {packet.target_property.address}\n\n")
                f.write("## Action Plan\n")
                for step in packet.organizing_action_plan:
                    f.write(f"{step}\n")
                f.write("\n## Sample Demand Letter\n")
                f.write(f"```\n{packet.sample_demand_letter}\n```\n")
            print(f"Organizing packet successfully saved to: {args.output}")
        else:
            print(f"\n=== ORGANIZING PACKET FOR {packet.target_property.address} ===")
            print(f"Parent Entity: {packet.parent_company_name}")
            print(f"Portfolio Control: {packet.total_portfolio_units} units across {packet.total_portfolio_properties} properties")
            print("\nSTRATEGIC ACTION PLAN:")
            for step in packet.organizing_action_plan:
                print(f"  {step}")
            print("\nSAMPLE DEMAND LETTER:")
            print(packet.sample_demand_letter)

    elif args.command == "serve":
        print(f"\n🚀 Launching UnmaskLLC Web Server on http://{args.host}:{args.port}")
        uvicorn.run("unmask_llc.api.app:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
