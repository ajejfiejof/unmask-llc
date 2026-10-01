"""Pydantic data models for UnmaskLLC entity graph and property records."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Address(BaseModel):
    id: str
    raw_address: str
    normalized_street: str
    city: str
    state: str
    zip_code: str
    standard_hash: str


class Person(BaseModel):
    id: str
    name: str
    role: str  # e.g., "Registered Agent", "Managing Member", "Officer", "Attorney"
    address: Optional[str] = None


class CorporateEntity(BaseModel):
    id: str
    legal_name: str
    normalized_name: str
    entity_type: str  # e.g., "LLC", "Corporation", "LP"
    state_of_inc: str  # e.g., "CA", "NC", "DE"
    registered_agent_name: Optional[str] = None
    registered_agent_address: Optional[str] = None
    managing_members: List[str] = Field(default_factory=list)
    tax_mailing_address: Optional[str] = None
    filing_date: Optional[str] = None
    status: str = "Active"


class Property(BaseModel):
    id: str
    parcel_id: str
    address: str
    normalized_address: str
    city: str
    state: str
    zip_code: str
    units: int = 1
    recorded_owner_name: str
    normalized_owner_name: str
    year_built: Optional[int] = None
    assessed_value: Optional[float] = None
    eviction_count_3yr: int = 0
    building_code_violations: int = 0


class EntityLink(BaseModel):
    source_id: str
    target_id: str
    link_type: str  # e.g., "OWNS", "REGISTERED_AGENT_FOR", "SHARED_ADDRESS", "OFFICER_OF"
    confidence_score: float
    reason: str


class BeneficialOwnerCluster(BaseModel):
    cluster_id: str
    canonical_name: str
    estimated_parent_name: str
    risk_level: str  # "Low", "Medium", "High", "Monopolistic"
    shell_entities: List[CorporateEntity] = Field(default_factory=list)
    properties: List[Property] = Field(default_factory=list)
    total_units: int = 0
    total_properties: int = 0
    total_assessed_value: float = 0.0
    total_evictions: int = 0
    total_violations: int = 0
    shared_registered_agents: List[str] = Field(default_factory=list)
    shared_addresses: List[str] = Field(default_factory=list)
    monopoly_score: float = 0.0  # 0.0 to 100.0 scale


class TenantOrganizingPacket(BaseModel):
    cluster_id: str
    parent_company_name: str
    target_property: Property
    sister_properties: List[Property]
    total_portfolio_units: int
    total_portfolio_properties: int
    shell_company_web: List[str]
    shared_agents_and_officers: List[str]
    organizing_action_plan: List[str]
    sample_demand_letter: str
    risk_summary: Dict[str, Any]
