"""Data models for RegGenome Deep Research System."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document type classification."""
    
    REGULATION = "regulation"
    GUIDANCE = "guidance"
    RULE = "rule"
    DIRECTIVE = "directive"
    ACT = "act"
    AMENDMENT = "amendment"
    OTHER = "other"


class EntityType(str, Enum):
    """Types of regulated entities."""
    
    FINANCIAL_INSTITUTION = "financial_institution"
    INVESTMENT_COMPANY = "investment_company"
    INVESTMENT_ADVISER = "investment_adviser"
    BROKER_DEALER = "broker_dealer"
    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"
    PENSION_FUND = "pension_fund"
    HEDGE_FUND = "hedge_fund"
    PRIVATE_EQUITY = "private_equity"
    BANK = "bank"
    CREDIT_UNION = "credit_union"
    INSURANCE_COMPANY = "insurance_company"
    OTHER = "other"


class ActivityType(str, Enum):
    """Types of regulated activities."""
    
    INVESTMENT_ADVISORY = "investment_advisory"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    FUND_MANAGEMENT = "fund_management"
    SECURITIES_TRADING = "securities_trading"
    CUSTODY_SERVICES = "custody_services"
    PRIME_BROKERAGE = "prime_brokerage"
    CLEARING_SETTLEMENT = "clearing_settlement"
    MARKET_MAKING = "market_making"
    UNDERWRITING = "underwriting"
    RESEARCH_SERVICES = "research_services"
    RISK_MANAGEMENT = "risk_management"
    COMPLIANCE_MONITORING = "compliance_monitoring"
    REPORTING = "reporting"
    OTHER = "other"


class ProductType(str, Enum):
    """Types of regulated products."""
    
    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"
    HEDGE_FUND = "hedge_fund"
    PRIVATE_FUND = "private_fund"
    PENSION_FUND = "pension_fund"
    UCITS = "ucits"
    SECURITIES = "securities"
    DERIVATIVES = "derivatives"
    STRUCTURED_PRODUCTS = "structured_products"
    COLLECTIVE_INVESTMENT_SCHEME = "collective_investment_scheme"
    INVESTMENT_TRUST = "investment_trust"
    OTHER = "other"


class RegGenomeDocument(BaseModel):
    """RegGenome document model."""
    
    document_id: str
    title: str
    content: str
    url: Optional[str] = None
    publisher: Optional[str] = None
    publication_date: Optional[datetime] = None
    document_type: Optional[DocumentType] = None
    jurisdiction: Optional[str] = None
    legislative_initiative: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Sub-document level information
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    thematic_tags: List[str] = Field(default_factory=list)
    relevance_scores: Dict[str, float] = Field(default_factory=dict)


class RegulatedEntity(BaseModel):
    """Regulated entity model."""
    
    entity_id: str = Field(description="Unique identifier for the entity")
    name: str = Field(description="Name of the regulated entity")
    entity_type: EntityType = Field(description="Type of entity")
    description: Optional[str] = Field(description="Description of the entity")
    
    # Hierarchical information
    parent_entity: Optional[str] = Field(default=None, description="Parent entity ID if applicable")
    sub_entities: List[str] = Field(default_factory=list, description="List of sub-entity IDs")
    
    # Regulatory context
    applicable_jurisdictions: List[str] = Field(default_factory=list)
    regulatory_framework: List[str] = Field(default_factory=list)
    
    # Source information
    source_documents: List[str] = Field(default_factory=list)
    source_sections: List[str] = Field(default_factory=list)
    definition_text: Optional[str] = Field(description="Full text of the definition")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class RegulatedActivity(BaseModel):
    """Regulated activity model."""
    
    activity_id: str = Field(description="Unique identifier for the activity")
    name: str = Field(description="Name of the regulated activity")
    activity_type: ActivityType = Field(description="Type of activity")
    description: Optional[str] = Field(description="Description of the activity")
    
    # Hierarchical information
    parent_activity: Optional[str] = Field(default=None, description="Parent activity ID if applicable")
    sub_activities: List[str] = Field(default_factory=list, description="List of sub-activity IDs")
    
    # Regulatory context
    applicable_entities: List[str] = Field(default_factory=list, description="Entity IDs this applies to")
    required_licenses: List[str] = Field(default_factory=list)
    regulatory_requirements: List[str] = Field(default_factory=list)
    
    # Source information
    source_documents: List[str] = Field(default_factory=list)
    source_sections: List[str] = Field(default_factory=list)
    definition_text: Optional[str] = Field(description="Full text of the definition")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class RegulatedProduct(BaseModel):
    """Regulated product model."""
    
    product_id: str = Field(description="Unique identifier for the product")
    name: str = Field(description="Name of the regulated product")
    product_type: ProductType = Field(description="Type of product")
    description: Optional[str] = Field(description="Description of the product")
    
    # Hierarchical information
    parent_product: Optional[str] = Field(default=None, description="Parent product ID if applicable")
    sub_products: List[str] = Field(default_factory=list, description="List of sub-product IDs")
    
    # Regulatory context
    applicable_entities: List[str] = Field(default_factory=list, description="Entity IDs this applies to")
    regulatory_classification: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    
    # Source information
    source_documents: List[str] = Field(default_factory=list)
    source_sections: List[str] = Field(default_factory=list)
    definition_text: Optional[str] = Field(description="Full text of the definition")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class DocumentRelevance(BaseModel):
    """Document relevance assessment."""
    
    document_id: str
    entity_relevance: Dict[str, float] = Field(default_factory=dict)  # entity_id -> relevance_score
    activity_relevance: Dict[str, float] = Field(default_factory=dict)  # activity_id -> relevance_score
    product_relevance: Dict[str, float] = Field(default_factory=dict)  # product_id -> relevance_score
    
    # Section-level relevance
    section_relevance: Dict[str, Dict[str, float]] = Field(default_factory=dict)  # section_id -> {type_id -> score}


class RegulatoryTaxonomy(BaseModel):
    """Complete regulatory taxonomy."""
    
    entities: List[RegulatedEntity] = Field(default_factory=list)
    activities: List[RegulatedActivity] = Field(default_factory=list)
    products: List[RegulatedProduct] = Field(default_factory=list)
    
    # Document relevance mappings
    document_relevance: List[DocumentRelevance] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
    
    def get_entity_by_id(self, entity_id: str) -> Optional[RegulatedEntity]:
        """Get entity by ID."""
        return next((e for e in self.entities if e.entity_id == entity_id), None)
    
    def get_activity_by_id(self, activity_id: str) -> Optional[RegulatedActivity]:
        """Get activity by ID."""
        return next((a for a in self.activities if a.activity_id == activity_id), None)
    
    def get_product_by_id(self, product_id: str) -> Optional[RegulatedProduct]:
        """Get product by ID."""
        return next((p for p in self.products if p.product_id == product_id), None)
    
    def deduplicate(self) -> "RegulatoryTaxonomy":
        """Remove duplicates based on names and merge similar items."""
        # This will be implemented by the deduplication agent
        return self


class ResearchState(BaseModel):
    """State for the research workflow."""
    
    query: str = Field(description="Research query or topic")
    documents: List[RegGenomeDocument] = Field(default_factory=list)
    taxonomy: RegulatoryTaxonomy = Field(default_factory=RegulatoryTaxonomy)
    
    # Processing status
    documents_fetched: bool = False
    entities_extracted: bool = False
    activities_extracted: bool = False
    products_extracted: bool = False
    relevance_assessed: bool = False
    deduplicated: bool = False
    
    # Error tracking
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list) 