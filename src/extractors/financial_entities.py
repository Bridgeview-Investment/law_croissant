import re
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import pandas as pd
from loguru import logger


@dataclass
class FinancialEntity:
    """Represents a financial regulatory entity"""
    name: str
    entity_type: str
    category: str
    subcategory: Optional[str] = None
    jurisdiction: Optional[str] = None
    regulation: Optional[str] = None
    confidence: float = 1.0


class FinancialEntityExtractor:
    """Specialized extractor for financial regulatory entities"""
    
    def __init__(self):
        self.entity_mappings = self._load_entity_mappings()
        self.abbreviations = self._load_abbreviations()
        self.regulatory_frameworks = self._load_regulatory_frameworks()
        
    def _load_entity_mappings(self) -> Dict[str, Dict]:
        """Load mappings for financial entities"""
        return {
            "organizations": {
                "investment_companies": {
                    "patterns": [
                        r"investment\s+company",
                        r"mutual\s+fund",
                        r"unit\s+trust",
                        r"OEIC",
                        r"SICAV",
                        r"SICAF",
                        r"closed-end\s+fund",
                        r"open-end\s+fund",
                        r"exchange-traded\s+fund",
                        r"ETF",
                        r"money\s+market\s+fund"
                    ],
                    "category": "Investment Vehicle"
                },
                "investment_firms": {
                    "patterns": [
                        r"investment\s+firm",
                        r"investment\s+adviser",
                        r"investment\s+advisor",
                        r"portfolio\s+manager",
                        r"asset\s+manager",
                        r"wealth\s+manager",
                        r"discretionary\s+manager",
                        r"AIFM",
                        r"management\s+company",
                        r"ManCo"
                    ],
                    "category": "Investment Service Provider"
                },
                "financial_institutions": {
                    "patterns": [
                        r"credit\s+institution",
                        r"bank(?:ing\s+institution)?",
                        r"depositary",
                        r"custodian",
                        r"prime\s+broker",
                        r"clearing\s+(?:house|member)",
                        r"settlement\s+agent",
                        r"paying\s+agent",
                        r"transfer\s+agent"
                    ],
                    "category": "Financial Institution"
                },
                "market_infrastructure": {
                    "patterns": [
                        r"(?:regulated|recognized)\s+market",
                        r"MTF",
                        r"multilateral\s+trading\s+facility",
                        r"OTF",
                        r"organised\s+trading\s+facility",
                        r"systematic\s+internaliser",
                        r"central\s+counterparty",
                        r"CCP",
                        r"central\s+securities\s+depository",
                        r"CSD",
                        r"trade\s+repository"
                    ],
                    "category": "Market Infrastructure"
                },
                "regulatory_bodies": {
                    "patterns": [
                        r"competent\s+authority",
                        r"regulatory\s+authority",
                        r"supervisory\s+authority",
                        r"home\s+(?:member\s+)?state\s+authority",
                        r"host\s+(?:member\s+)?state\s+authority",
                        r"ESMA",
                        r"EBA",
                        r"EIOPA",
                        r"national\s+competent\s+authority",
                        r"NCA"
                    ],
                    "category": "Regulatory Body"
                }
            },
            "products": {
                "securities": {
                    "patterns": [
                        r"transferable\s+securit(?:y|ies)",
                        r"equity\s+securit(?:y|ies)",
                        r"debt\s+securit(?:y|ies)",
                        r"government\s+bond",
                        r"corporate\s+bond",
                        r"shares?",
                        r"stocks?",
                        r"bonds?",
                        r"notes?",
                        r"debentures?",
                        r"certificates?\s+of\s+deposit",
                        r"commercial\s+paper"
                    ],
                    "category": "Securities"
                },
                "derivatives": {
                    "patterns": [
                        r"derivative(?:\s+instrument)?",
                        r"futures?\s+contract",
                        r"options?\s+contract",
                        r"swaps?",
                        r"forward\s+contract",
                        r"CFD",
                        r"contract\s+for\s+difference",
                        r"warrant",
                        r"structured\s+product",
                        r"structured\s+note"
                    ],
                    "category": "Derivatives"
                },
                "funds": {
                    "patterns": [
                        r"collective\s+investment\s+(?:scheme|undertaking)",
                        r"UCITS",
                        r"AIF",
                        r"alternative\s+investment\s+fund",
                        r"feeder\s+fund",
                        r"master\s+fund",
                        r"fund\s+of\s+funds",
                        r"umbrella\s+fund",
                        r"sub-fund",
                        r"compartment",
                        r"share\s+class"
                    ],
                    "category": "Investment Funds"
                }
            },
            "activities": {
                "investment_services": {
                    "patterns": [
                        r"portfolio\s+management",
                        r"investment\s+advice",
                        r"reception\s+and\s+transmission\s+of\s+orders",
                        r"execution\s+of\s+orders",
                        r"dealing\s+on\s+own\s+account",
                        r"underwriting",
                        r"placing",
                        r"operation\s+of\s+an?\s+MTF",
                        r"operation\s+of\s+an?\s+OTF"
                    ],
                    "category": "Investment Services"
                },
                "ancillary_services": {
                    "patterns": [
                        r"safekeeping\s+and\s+administration",
                        r"custody\s+services",
                        r"granting\s+(?:of\s+)?credit",
                        r"lending\s+(?:to|of)\s+(?:financial\s+)?instruments",
                        r"foreign\s+exchange\s+services",
                        r"investment\s+research",
                        r"financial\s+analysis"
                    ],
                    "category": "Ancillary Services"
                },
                "fund_activities": {
                    "patterns": [
                        r"collective\s+portfolio\s+management",
                        r"risk\s+management",
                        r"administration\s+of\s+(?:collective\s+investment\s+)?(?:schemes|undertakings)",
                        r"marketing\s+of\s+(?:units|shares)",
                        r"distribution\s+of\s+(?:units|shares)",
                        r"valuation\s+(?:of\s+assets)?",
                        r"share\s+dealing",
                        r"fund\s+accounting"
                    ],
                    "category": "Fund Management Activities"
                }
            }
        }
    
    def _load_abbreviations(self) -> Dict[str, str]:
        """Load common abbreviations and their expansions"""
        return {
            "UCITS": "Undertakings for Collective Investment in Transferable Securities",
            "AIF": "Alternative Investment Fund",
            "AIFM": "Alternative Investment Fund Manager",
            "AIFMD": "Alternative Investment Fund Managers Directive",
            "MiFID": "Markets in Financial Instruments Directive",
            "MiFIR": "Markets in Financial Instruments Regulation",
            "EMIR": "European Market Infrastructure Regulation",
            "SFTR": "Securities Financing Transactions Regulation",
            "PRIIPs": "Packaged Retail and Insurance-based Investment Products",
            "CRD": "Capital Requirements Directive",
            "CRR": "Capital Requirements Regulation",
            "IFD": "Investment Firms Directive",
            "IFR": "Investment Firms Regulation",
            "ESMA": "European Securities and Markets Authority",
            "EBA": "European Banking Authority",
            "EIOPA": "European Insurance and Occupational Pensions Authority",
            "NCA": "National Competent Authority",
            "MTF": "Multilateral Trading Facility",
            "OTF": "Organised Trading Facility",
            "CCP": "Central Counterparty",
            "CSD": "Central Securities Depository",
            "OEIC": "Open-Ended Investment Company",
            "SICAV": "Société d'Investissement à Capital Variable",
            "SICAF": "Société d'Investissement à Capital Fixe",
            "ETF": "Exchange-Traded Fund",
            "NAV": "Net Asset Value",
            "KID": "Key Information Document",
            "KIID": "Key Investor Information Document"
        }
    
    def _load_regulatory_frameworks(self) -> Dict[str, Dict]:
        """Load regulatory framework information"""
        return {
            "EU": {
                "UCITS": {
                    "full_name": "Directive 2009/65/EC",
                    "applies_to": ["UCITS", "Management Company", "Depositary"],
                    "jurisdiction": "European Union"
                },
                "AIFMD": {
                    "full_name": "Directive 2011/61/EU",
                    "applies_to": ["AIF", "AIFM", "Depositary"],
                    "jurisdiction": "European Union"
                },
                "MiFID II": {
                    "full_name": "Directive 2014/65/EU",
                    "applies_to": ["Investment Firm", "Credit Institution", "Market Operator"],
                    "jurisdiction": "European Union"
                }
            },
            "US": {
                "Investment Company Act": {
                    "full_name": "Investment Company Act of 1940",
                    "applies_to": ["Investment Company", "Mutual Fund", "Closed-End Fund"],
                    "jurisdiction": "United States"
                },
                "Investment Advisers Act": {
                    "full_name": "Investment Advisers Act of 1940",
                    "applies_to": ["Investment Adviser", "Registered Investment Adviser"],
                    "jurisdiction": "United States"
                }
            },
            "UK": {
                "UK UCITS": {
                    "full_name": "The UCITS Regulations 2011",
                    "applies_to": ["UK UCITS", "UK ManCo", "Depositary"],
                    "jurisdiction": "United Kingdom"
                }
            }
        }
    
    def extract_financial_entities(self, text: str) -> List[FinancialEntity]:
        """Extract financial entities from text"""
        entities = []
        
        # Extract from each category
        for main_category, subcategories in self.entity_mappings.items():
            for subcategory_name, subcategory_info in subcategories.items():
                for pattern in subcategory_info["patterns"]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entity_text = match.group()
                        
                        # Check if it's an abbreviation
                        expanded = self.abbreviations.get(entity_text.upper(), entity_text)
                        
                        entity = FinancialEntity(
                            name=entity_text,
                            entity_type=main_category,
                            category=subcategory_info["category"],
                            subcategory=subcategory_name,
                            confidence=0.95
                        )
                        
                        # Add regulatory framework if mentioned
                        entity.regulation = self._extract_regulation_context(text, match.start())
                        
                        entities.append(entity)
        
        # Deduplicate
        unique_entities = self._deduplicate_entities(entities)
        
        return unique_entities
    
    def _extract_regulation_context(self, text: str, position: int, window: int = 100) -> Optional[str]:
        """Extract regulatory framework mentioned near the entity"""
        start = max(0, position - window)
        end = min(len(text), position + window)
        context = text[start:end]
        
        for jurisdiction, frameworks in self.regulatory_frameworks.items():
            for framework_name, framework_info in frameworks.items():
                if framework_name in context or framework_info["full_name"] in context:
                    return framework_name
        
        return None
    
    def _deduplicate_entities(self, entities: List[FinancialEntity]) -> List[FinancialEntity]:
        """Remove duplicate entities"""
        seen = set()
        unique = []
        
        for entity in entities:
            key = (entity.name.lower(), entity.entity_type, entity.category)
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        
        return unique
    
    def create_entity_hierarchy(self, entities: List[FinancialEntity]) -> Dict[str, Dict]:
        """Create hierarchical structure of entities"""
        hierarchy = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for entity in entities:
            hierarchy[entity.entity_type][entity.category][entity.subcategory].append({
                "name": entity.name,
                "regulation": entity.regulation,
                "confidence": entity.confidence
            })
        
        return dict(hierarchy)
    
    def export_to_dataframe(self, entities: List[FinancialEntity]) -> pd.DataFrame:
        """Export entities to pandas DataFrame"""
        data = []
        for entity in entities:
            data.append({
                "entity_name": entity.name,
                "entity_type": entity.entity_type,
                "category": entity.category,
                "subcategory": entity.subcategory,
                "regulation": entity.regulation,
                "confidence": entity.confidence
            })
        
        return pd.DataFrame(data)