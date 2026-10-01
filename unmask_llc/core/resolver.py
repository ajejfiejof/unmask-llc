"""Entity resolution engine for corporate landlords and property records."""

from typing import List, Dict, Set, Tuple
from collections import defaultdict
import math

from unmask_llc.core.models import Property, CorporateEntity, EntityLink, BeneficialOwnerCluster
from unmask_llc.core.normalizer import (
    normalize_address,
    normalize_company_name,
    normalize_person_name,
)


class UnionFind:
    """Disjoint-set data structure for clustering resolved entities."""

    def __init__(self, elements: List[str]):
        self.parent = {el: el for el in elements}
        self.rank = {el: 0 for el in elements}

    def find(self, i: str) -> str:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: str, j: str):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1


class EntityResolver:
    """Core entity resolution engine matching shell companies to beneficial owners."""

    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold

    def calculate_link_score(
        self, entity1: CorporateEntity, entity2: CorporateEntity
    ) -> Tuple[float, List[str]]:
        """Computes a match confidence score between two corporate entities."""
        score = 0.0
        reasons = []

        # 1. Registered Agent Address Match (High Weight: +0.45)
        addr1 = normalize_address(entity1.registered_agent_address or "")
        addr2 = normalize_address(entity2.registered_agent_address or "")
        if addr1 and addr2 and addr1 == addr2:
            score += 0.45
            reasons.append(f"Shared Registered Agent Address: '{addr1}'")

        # 2. Tax Mailing Address Match (High Weight: +0.40)
        tax1 = normalize_address(entity1.tax_mailing_address or "")
        tax2 = normalize_address(entity2.tax_mailing_address or "")
        if tax1 and tax2 and tax1 == tax2:
            score += 0.40
            reasons.append(f"Shared Tax Mailing Address: '{tax1}'")

        # 3. Registered Agent Name Match (Medium Weight: +0.30)
        agent1 = normalize_person_name(entity1.registered_agent_name or "")
        agent2 = normalize_person_name(entity2.registered_agent_name or "")
        if agent1 and agent2 and agent1 == agent2 and agent1 not in ("CORPORATE AGENT", "CSC"):
            score += 0.30
            reasons.append(f"Shared Registered Agent Name: '{agent1}'")

        # 4. Shared Officers or Managing Members (High Weight: +0.50)
        members1 = {normalize_person_name(m) for m in entity1.managing_members if m}
        members2 = {normalize_person_name(m) for m in entity2.managing_members if m}
        shared_members = members1.intersection(members2)
        if shared_members:
            score += 0.50
            reasons.append(f"Shared Managing Members: {', '.join(shared_members)}")

        # 5. Base Name Similarity (Stripped Suffixes: +0.25)
        base1 = normalize_company_name(entity1.legal_name, strip_suffixes=True)
        base2 = normalize_company_name(entity2.legal_name, strip_suffixes=True)
        if base1 and base2 and (base1 in base2 or base2 in base1) and len(base1) > 4:
            score += 0.25
            reasons.append(f"Base Name Similarity: '{base1}' ~ '{base2}'")

        final_score = min(score, 1.0)
        return final_score, reasons

    def resolve_clusters(
        self, properties: List[Property], entities: List[CorporateEntity]
    ) -> List[BeneficialOwnerCluster]:
        """Resolves property records and corporate entities into beneficial ownership clusters."""
        entity_map = {e.id: e for e in entities}
        prop_map = {p.id: p for p in properties}

        all_ids = list(entity_map.keys())
        uf = UnionFind(all_ids)
        links: List[EntityLink] = []

        # Find pairwise links between corporate entities
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1 = entities[i]
                e2 = entities[j]
                score, reasons = self.calculate_link_score(e1, e2)
                if score >= self.confidence_threshold:
                    uf.union(e1.id, e2.id)
                    links.append(
                        EntityLink(
                            source_id=e1.id,
                            target_id=e2.id,
                            link_type="SHARED_CORPORATE_INFRASTRUCTURE",
                            confidence_score=score,
                            reason="; ".join(reasons),
                        )
                    )

        # Group entities by root parent
        clusters_raw: Dict[str, List[CorporateEntity]] = defaultdict(list)
        for e_id in all_ids:
            root = uf.find(e_id)
            clusters_raw[root].append(entity_map[e_id])

        # Link properties to corporate entities and clusters
        owner_name_to_entity_ids: Dict[str, List[str]] = defaultdict(list)
        for e in entities:
            norm_name = normalize_company_name(e.legal_name)
            owner_name_to_entity_ids[norm_name].append(e.id)

        cluster_properties: Dict[str, List[Property]] = defaultdict(list)
        unmatched_properties: List[Property] = []

        for p in properties:
            norm_owner = p.normalized_owner_name
            matched_entity_ids = owner_name_to_entity_ids.get(norm_owner, [])

            if matched_entity_ids:
                root = uf.find(matched_entity_ids[0])
                cluster_properties[root].append(p)
            else:
                # Try fallback matching property recorded owner to entity list directly
                best_root = None
                for e in entities:
                    if normalize_company_name(e.legal_name, strip_suffixes=True) in norm_owner:
                        best_root = uf.find(e.id)
                        break
                if best_root:
                    cluster_properties[best_root].append(p)
                else:
                    unmatched_properties.append(p)

        # Build final BeneficialOwnerCluster models
        result_clusters: List[BeneficialOwnerCluster] = []

        for idx, (root_id, shell_list) in enumerate(clusters_raw.items(), start=1):
            props = cluster_properties.get(root_id, [])

            # Infer canonical parent name
            parent_name = self._infer_parent_name(shell_list)
            shared_agents = list(
                {e.registered_agent_name for e in shell_list if e.registered_agent_name}
            )
            shared_addrs = list(
                {e.registered_agent_address for e in shell_list if e.registered_agent_address}
            )

            total_units = sum(p.units for p in props)
            total_props = len(props)
            total_val = sum(p.assessed_value or 0.0 for p in props)
            total_evictions = sum(p.eviction_count_3yr for p in props)
            total_violations = sum(p.building_code_violations for p in props)

            # Monopoly score formula: combination of units, shell count, and eviction concentration
            monopoly_score = round(
                min(
                    100.0,
                    (total_units * 1.5)
                    + (len(shell_list) * 5.0)
                    + (total_evictions * 3.0)
                    + (total_violations * 2.0),
                ),
                1,
            )

            risk_level = "Low"
            if monopoly_score > 70:
                risk_level = "Monopolistic"
            elif monopoly_score > 40:
                risk_level = "High"
            elif monopoly_score > 20:
                risk_level = "Medium"

            cluster = BeneficialOwnerCluster(
                cluster_id=f"cluster_{idx:03d}",
                canonical_name=parent_name,
                estimated_parent_name=parent_name,
                risk_level=risk_level,
                shell_entities=shell_list,
                properties=props,
                total_units=total_units,
                total_properties=total_props,
                total_assessed_value=total_val,
                total_evictions=total_evictions,
                total_violations=total_violations,
                shared_registered_agents=shared_agents,
                shared_addresses=shared_addrs,
                monopoly_score=monopoly_score,
            )
            result_clusters.append(cluster)

        # Sort clusters by monopoly score descending
        result_clusters.sort(key=lambda c: c.monopoly_score, reverse=True)
        return result_clusters

    def _infer_parent_name(self, shell_entities: List[CorporateEntity]) -> str:
        """Determines the most plausible parent company / beneficial owner name."""
        # Check if any entity contains terms like "HOLDINGS", "GROUP", "CAPITAL", "PARTNERS"
        for e in shell_entities:
            name_upper = e.legal_name.upper()
            if any(kw in name_upper for kw in ["HOLDINGS", "CAPITAL", "PARTNERS", "GROUP", "INVESTMENTS"]):
                return e.legal_name

        # Fallback to managing member name if available
        all_members = [m for e in shell_entities for m in e.managing_members if m]
        if all_members:
            return f"{all_members[0]} Real Estate Network"

        # Fallback to shortest base name + "Capital / Real Estate Group"
        base_names = [normalize_company_name(e.legal_name, strip_suffixes=True) for e in shell_entities]
        common = min(base_names, key=len) if base_names else "Apex Landlord"
        return f"{common.title()} Parent Group"
