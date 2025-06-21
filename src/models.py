from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

class EntityType(Enum):
    """Types of regulated entities"""
    FIRM = "firm"
    FUND = "fund"
    INVESTMENT_ADVISER = "investment_adviser"
    INVESTMENT_COMPANY = "investment_company"
    UCITS = "ucits"
    MANAGEMENT_COMPANY = "management_company"
    DEPOSITARY = "depositary"
    OTHER = "other"

class ActivityType(Enum):
    """Types of regulated activities"""
    ASSET_MANAGEMENT = "asset_management"
    INVESTMENT_ADVICE = "investment_advice"
    PORTFOLIO_MANAGEMENT = "portfolio_management"
    CUSTODY = "custody"
    DISTRIBUTION = "distribution"
    FUND_ADMINISTRATION = "fund_administration"
    RISK_MANAGEMENT = "risk_management"
    COMPLIANCE = "compliance"
    REPORTING = "reporting"
    OTHER = "other"

class ProductType(Enum):
    """Types of financial products"""
    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"
    UCITS_FUND = "ucits_fund"
    HEDGE_FUND = "hedge_fund"
    MONEY_MARKET_FUND = "money_market_fund"
    INVESTMENT_TRUST = "investment_trust"
    COLLECTIVE_INVESTMENT_SCHEME = "collective_investment_scheme"
    OTHER = "other"

@dataclass
class ExtractedItem:
    """Base class for extracted regulatory items"""
    name: str
    type: str
    description: str
    source_document_id: str
    source_text: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class RegulatedEntity(ExtractedItem):
    """Represents a regulated entity"""
    entity_type: EntityType
    jurisdiction: Optional[str] = None
    regulatory_framework: Optional[str] = None

@dataclass  
class RegulatedActivity(ExtractedItem):
    """Represents a regulated activity"""
    activity_type: ActivityType
    applicable_entities: List[str] = None
    requirements: List[str] = None
    
    def __post_init__(self):
        if self.applicable_entities is None:
            self.applicable_entities = []
        if self.requirements is None:
            self.requirements = []

@dataclass
class RegulatedProduct(ExtractedItem):
    """Represents a regulated product"""
    product_type: ProductType
    issuer_requirements: List[str] = None
    investor_restrictions: List[str] = None
    
    def __post_init__(self):
        if self.issuer_requirements is None:
            self.issuer_requirements = []
        if self.investor_restrictions is None:
            self.investor_restrictions = []

@dataclass
class Document:
    """RegGenome document structure"""
    document_id: str
    title: str
    publishers: List[Dict]
    published: str
    source_text: List[Dict]
    signposts: List[Dict]
    initiatives: List[Dict]
    metadata: Dict[str, Any]

@dataclass
class ResearchResult:
    """Final research output for Task 1"""
    entities: List[RegulatedEntity]
    activities: List[RegulatedActivity]
    products: List[RegulatedProduct]
    total_documents_processed: int
    extraction_metadata: Dict[str, Any]