from typing import List, Dict, Any, Optional
import re
from src.models import Document, RegulatedEntity, EntityType

class EntityExtractionAgent:
    """Agent specialized in extracting regulated entities from documents"""
    
    def __init__(self):
        # Entity patterns and keywords
        self.entity_patterns = {
            EntityType.INVESTMENT_ADVISER: [
                r"investment adviser[s]?",
                r"investment advisor[s]?",
                r"adviser[s]?",
                r"advisor[s]?",
                r"registered investment adviser",
                r"RIA"
            ],
            EntityType.INVESTMENT_COMPANY: [
                r"investment compan(?:y|ies)",
                r"registered investment compan(?:y|ies)",
                r"mutual fund[s]?",
                r"closed-end fund[s]?",
                r"open-end fund[s]?"
            ],
            EntityType.UCITS: [
                r"UCITS",
                r"undertaking[s]? for collective investment",
                r"UCITS fund[s]?",
                r"UCITS scheme[s]?"
            ],
            EntityType.MANAGEMENT_COMPANY: [
                r"management compan(?:y|ies)",
                r"fund manager[s]?",
                r"asset management compan(?:y|ies)",
                r"UCITS management compan(?:y|ies)"
            ],
            EntityType.DEPOSITARY: [
                r"depositar(?:y|ies)",
                r"custodian[s]?",
                r"trustee[s]?",
                r"depositary bank[s]?"
            ],
            EntityType.FUND: [
                r"fund[s]?",
                r"collective investment scheme[s]?",
                r"investment fund[s]?",
                r"pooled investment vehicle[s]?"
            ],
            EntityType.FIRM: [
                r"firm[s]?",
                r"financial institution[s]?",
                r"regulated entit(?:y|ies)",
                r"financial service[s]? provider[s]?"
            ]
        }
        
        self.entity_definitions = {
            "investment adviser": "entity providing investment advice",
            "investment company": "company engaged in investing, reinvesting, or trading in securities",
            "UCITS": "Undertakings for Collective Investment in Transferable Securities",
            "management company": "entity managing collective investment schemes",
            "depositary": "entity safekeeping assets of investment funds",
            "fund": "pooled investment vehicle",
            "firm": "regulated financial services entity"
        }
    
    def extract_entities(self, document: Document) -> List[RegulatedEntity]:
        """Extract regulated entities from a document"""
        entities = []
        processed_entities = set()  # To avoid duplicates
        
        # Combine all text sources
        full_text = self._get_full_text(document)
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                
                for match in matches:
                    entity_name = match.group(0)
                    context = self._extract_context(full_text, match.start(), match.end())
                    
                    # Create unique key to avoid duplicates
                    entity_key = f"{entity_name.lower()}_{entity_type.value}"
                    
                    if entity_key not in processed_entities:
                        processed_entities.add(entity_key)
                        
                        entity = RegulatedEntity(
                            name=entity_name,
                            type="entity",
                            entity_type=entity_type,
                            description=self._generate_description(entity_name, context),
                            source_document_id=document.document_id,
                            source_text=context,
                            confidence=self._calculate_confidence(entity_name, context),
                            metadata={
                                "document_title": document.title or "Unknown",
                                "publishers": [p.get("name", "") for p in document.publishers] if document.publishers else [],
                                "published_date": document.published or "Unknown"
                            },
                            jurisdiction=self._extract_jurisdiction(document),
                            regulatory_framework=self._extract_framework(document)
                        )
                        entities.append(entity)
        
        return entities
    
    def _get_full_text(self, document: Document) -> str:
        """Combine all text sources from document"""
        text_parts = []
        
        # Add title
        if document.title:
            text_parts.append(document.title)
        
        # Add source text
        if document.source_text:
            for text_item in document.source_text:
                if isinstance(text_item, dict) and "text" in text_item:
                    text_parts.append(text_item["text"])
                elif isinstance(text_item, str):
                    text_parts.append(text_item)
        
        # Add signpost text
        if document.signposts:
            for signpost in document.signposts:
                if isinstance(signpost, dict) and "text" in signpost:
                    text_parts.append(signpost["text"])
        
        return " ".join(text_parts)
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 200) -> str:
        """Extract context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _generate_description(self, entity_name: str, context: str) -> str:
        """Generate description based on entity and context"""
        # Simple rule-based description generation
        entity_lower = entity_name.lower()
        
        if "investment adviser" in entity_lower or "investment advisor" in entity_lower:
            return "Entity providing investment advice to clients"
        elif "investment company" in entity_lower:
            return "Company engaged in investing, reinvesting, or trading in securities"
        elif "ucits" in entity_lower:
            return "Undertaking for Collective Investment in Transferable Securities"
        elif "management company" in entity_lower:
            return "Company managing collective investment schemes"
        elif "depositary" in entity_lower or "custodian" in entity_lower:
            return "Entity responsible for safekeeping of fund assets"
        elif "fund" in entity_lower:
            return "Pooled investment vehicle"
        else:
            return "Regulated financial services entity"
    
    def _calculate_confidence(self, entity_name: str, context: str) -> float:
        """Calculate confidence score for extracted entity"""
        score = 0.5  # Base score
        
        # Increase score for exact matches
        if entity_name in self.entity_definitions:
            score += 0.2
        
        # Increase score for regulatory keywords in context
        regulatory_keywords = ["regulated", "registered", "authorized", "licensed", "approved"]
        for keyword in regulatory_keywords:
            if keyword in context.lower():
                score += 0.1
                break
        
        # Increase score for definition indicators
        if any(indicator in context.lower() for indicator in ["means", "defined as", "refers to"]):
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_jurisdiction(self, document: Document) -> Optional[str]:
        """Extract jurisdiction from document metadata"""
        if document.publishers:
            for publisher in document.publishers:
                if isinstance(publisher, dict):
                    if "jurisdiction" in publisher:
                        return publisher["jurisdiction"]
                    if "name" in publisher:
                        name = publisher["name"].lower()
                        if "uk" in name or "united kingdom" in name:
                            return "UK"
                        elif "us" in name or "united states" in name:
                            return "US"
                        elif "eu" in name or "european" in name:
                            return "EU"
        return None
    
    def _extract_framework(self, document: Document) -> Optional[str]:
        """Extract regulatory framework from document"""
        if not document.title:
            return None
            
        title_lower = document.title.lower()
        
        if "investment advisers act" in title_lower:
            return "Investment Advisers Act (1940)"
        elif "investment company act" in title_lower:
            return "Investment Company Act (1940)"
        elif "ucits" in title_lower:
            if document.publishers:
                if any(isinstance(p, dict) and p.get("jurisdiction") == "UK" for p in document.publishers):
                    return "UK UCITS Regulations"
            return "EU UCITS Directives"
        
        return None