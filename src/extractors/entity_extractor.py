import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
from loguru import logger


@dataclass
class Entity:
    """Represents an extracted entity"""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float
    document_id: Optional[str] = None
    section_id: Optional[str] = None
    context: Optional[str] = None


class EntityExtractor:
    """Advanced entity extraction for regulatory documents"""
    
    def __init__(self, model_name: str = "dslim/bert-base-NER-uncased"):
        logger.info(f"Initializing EntityExtractor with model: {model_name}")
        
        # Load spaCy model for basic NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("Downloading spaCy model...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Add custom components
        self._add_custom_components()
        
        # Load transformer model for advanced NER
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.ner_pipeline = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            aggregation_strategy="simple",
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Financial entity patterns
        self.financial_patterns = self._load_financial_patterns()
        
    def _add_custom_components(self):
        """Add custom spaCy components for regulatory text"""
        
        @Language.component("regulatory_entities")
        def regulatory_entity_component(doc: Doc) -> Doc:
            # Pattern matching for regulatory entities
            patterns = [
                r"\b(?:investment|mutual|hedge|pension|insurance)\s+(?:fund|company|adviser|advisor)\b",
                r"\b(?:broker|dealer|custodian|trustee|fiduciary)\b",
                r"\b(?:UCITS|AIF|AIFM|MiFID|EMIR)\b",
                r"\b(?:registered|regulated|authorized|licensed)\s+\w+\b"
            ]
            
            for pattern in patterns:
                for match in re.finditer(pattern, doc.text, re.IGNORECASE):
                    start, end = match.span()
                    span = doc.char_span(start, end, alignment_mode="expand")
                    if span:
                        span._.is_regulatory_entity = True
            
            return doc
        
        # Register extension attribute
        if not Span.has_extension("is_regulatory_entity"):
            Span.set_extension("is_regulatory_entity", default=False)
        
        # Add component to pipeline
        if "regulatory_entities" not in self.nlp.pipe_names:
            self.nlp.add_pipe("regulatory_entities", after="ner")
    
    def _load_financial_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for financial entity recognition"""
        return {
            "ORGANIZATION": [
                r"investment\s+(?:company|adviser|advisor)",
                r"mutual\s+fund",
                r"hedge\s+fund",
                r"pension\s+(?:fund|scheme)",
                r"insurance\s+(?:company|undertaking)",
                r"credit\s+institution",
                r"investment\s+firm",
                r"management\s+company",
                r"depositary",
                r"custodian",
                r"prime\s+broker",
                r"clearing\s+house",
                r"central\s+(?:bank|counterparty)",
                r"regulatory\s+(?:authority|body)",
                r"competent\s+authority"
            ],
            "PRODUCT": [
                r"transferable\s+securities",
                r"money\s+market\s+instruments",
                r"units\s+(?:of|in)\s+collective\s+investment",
                r"derivative\s+(?:instrument|contract)s?",
                r"financial\s+(?:instrument|product)s?",
                r"structured\s+(?:product|note)s?",
                r"exchange-traded\s+fund",
                r"ETF",
                r"share\s+class(?:es)?",
                r"investment\s+portfolio"
            ],
            "ACTIVITY": [
                r"portfolio\s+management",
                r"investment\s+advice",
                r"collective\s+investment",
                r"securities\s+lending",
                r"risk\s+management",
                r"safekeeping\s+(?:and\s+)?administration",
                r"order\s+(?:execution|routing)",
                r"clearing\s+and\s+settlement",
                r"market\s+making",
                r"proprietary\s+trading",
                r"underwriting",
                r"placement\s+(?:of\s+)?(?:financial\s+)?instruments"
            ],
            "REGULATION": [
                r"UCITS\s+(?:Directive|Regulation)",
                r"AIFMD?",
                r"MiFID\s+I{1,2}",
                r"EMIR",
                r"SFTR",
                r"PRIIPs",
                r"Solvency\s+I{1,2}",
                r"CRD\s+(?:IV|V)",
                r"Investment\s+(?:Company|Advisers)\s+Act",
                r"Securities\s+Exchange\s+Act"
            ]
        }
    
    def extract_entities(self, text: str, document_id: Optional[str] = None) -> List[Entity]:
        """Extract all types of entities from text"""
        entities = []
        
        # 1. SpaCy NER + custom patterns
        doc = self.nlp(text)
        for ent in doc.ents:
            entities.append(Entity(
                text=ent.text,
                entity_type=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.85,
                document_id=document_id
            ))
        
        # Check custom regulatory entities
        for span in doc.spans:
            if hasattr(span._, "is_regulatory_entity") and span._.is_regulatory_entity:
                entities.append(Entity(
                    text=span.text,
                    entity_type="REGULATORY_ENTITY",
                    start=span.start_char,
                    end=span.end_char,
                    confidence=0.9,
                    document_id=document_id
                ))
        
        # 2. Transformer-based NER
        transformer_entities = self.ner_pipeline(text)
        for ent in transformer_entities:
            entities.append(Entity(
                text=ent["word"],
                entity_type=ent["entity_group"],
                start=ent["start"],
                end=ent["end"],
                confidence=ent["score"],
                document_id=document_id
            ))
        
        # 3. Pattern-based extraction
        pattern_entities = self._extract_pattern_entities(text, document_id)
        entities.extend(pattern_entities)
        
        # Deduplicate and merge overlapping entities
        entities = self._merge_entities(entities)
        
        return entities
    
    def _extract_pattern_entities(self, text: str, document_id: Optional[str]) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.financial_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(Entity(
                        text=match.group(),
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.95,  # High confidence for exact pattern matches
                        document_id=document_id
                    ))
        
        return entities
    
    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """Merge overlapping entities, keeping highest confidence"""
        if not entities:
            return []
        
        # Sort by start position and confidence
        sorted_entities = sorted(entities, key=lambda e: (e.start, -e.confidence))
        
        merged = []
        current = sorted_entities[0]
        
        for entity in sorted_entities[1:]:
            # Check for overlap
            if entity.start < current.end:
                # Keep the one with higher confidence
                if entity.confidence > current.confidence:
                    current = entity
            else:
                # No overlap, add current and update
                merged.append(current)
                current = entity
        
        merged.append(current)
        return merged
    
    def extract_from_document(self, document: Dict) -> List[Entity]:
        """Extract entities from a RegGenome document"""
        all_entities = []
        
        # Extract from title
        if "title" in document:
            title_entities = self.extract_entities(
                document["title"],
                document_id=document.get("document_id")
            )
            for ent in title_entities:
                ent.section_id = "title"
            all_entities.extend(title_entities)
        
        # Extract from source text sections
        if "source_text" in document:
            for section in document["source_text"]:
                if "text" in section:
                    section_entities = self.extract_entities(
                        section["text"],
                        document_id=document.get("document_id")
                    )
                    for ent in section_entities:
                        ent.section_id = section.get("section_id", "unknown")
                    all_entities.extend(section_entities)
        
        # Extract from signposts
        if "signposts" in document:
            for signpost in document["signposts"]:
                if "inference_text" in signpost:
                    signpost_entities = self.extract_entities(
                        signpost["inference_text"],
                        document_id=document.get("document_id")
                    )
                    for ent in signpost_entities:
                        ent.section_id = f"signpost_{signpost.get('id', 'unknown')}"
                    all_entities.extend(signpost_entities)
        
        return all_entities
    
    def get_unique_entities(self, entities: List[Entity]) -> Set[Tuple[str, str]]:
        """Get unique entity text and type pairs"""
        return {(e.text.lower(), e.entity_type) for e in entities}
    
    def filter_entities_by_type(self, entities: List[Entity], entity_types: List[str]) -> List[Entity]:
        """Filter entities by type"""
        return [e for e in entities if e.entity_type in entity_types]
    
    def filter_entities_by_confidence(self, entities: List[Entity], min_confidence: float) -> List[Entity]:
        """Filter entities by confidence score"""
        return [e for e in entities if e.confidence >= min_confidence]