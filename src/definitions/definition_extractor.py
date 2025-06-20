import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import spacy
from transformers import pipeline
from loguru import logger
import json


@dataclass
class Definition:
    """Represents an extracted definition"""
    term: str
    definition_text: str
    document_id: str
    section_id: str
    start_pos: int
    end_pos: int
    confidence: float
    context: Optional[str] = None
    definition_type: Optional[str] = None  # formal, contextual, referential


class DefinitionExtractor:
    """Extract and link entity definitions from regulatory documents"""
    
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Definition patterns
        self.definition_patterns = self._load_definition_patterns()
        
        # Load QA model for definition extraction
        try:
            import torch
            self.qa_pipeline = pipeline(
                "question-answering",
                model="deepset/roberta-base-squad2",
                device=0 if torch.cuda.is_available() else -1
            )
        except ImportError:
            logger.warning("PyTorch not available, QA-based extraction disabled")
            self.qa_pipeline = None
        
    def _load_definition_patterns(self) -> List[Dict]:
        """Load regex patterns for definition extraction"""
        return [
            # Formal definitions
            {
                "pattern": r'"([^"]+)"\s+(?:means|refers to|is defined as|shall mean|includes)\s+([^.;]+[.;])',
                "type": "formal",
                "confidence": 0.95
            },
            {
                "pattern": r"'([^']+)'\s+(?:means|refers to|is defined as|shall mean|includes)\s+([^.;]+[.;])",
                "type": "formal",
                "confidence": 0.95
            },
            {
                "pattern": r"\b([A-Z][a-zA-Z\s]+)\s+(?:means|refers to|is defined as|shall mean)\s+([^.;]+[.;])",
                "type": "formal",
                "confidence": 0.90
            },
            
            # Parenthetical definitions
            {
                "pattern": r"\b([a-zA-Z\s]+)\s+\((?:the\s+)?[\"']([^\"']+)[\"']\)",
                "type": "parenthetical",
                "confidence": 0.85
            },
            {
                "pattern": r"\b([a-zA-Z\s]+)\s+\((?:hereinafter|hereafter|referred to as)[^)]*[\"']([^\"']+)[\"']\)",
                "type": "parenthetical",
                "confidence": 0.90
            },
            
            # List-based definitions
            {
                "pattern": r"(?:The following|For the purposes of this)\s+[^:]+:\s*\n\s*(?:\([a-z]\)|\d\.)\s*[\"']?([^\"']+)[\"']?\s*(?:means|refers to|is)\s+([^;]+)",
                "type": "list",
                "confidence": 0.88
            },
            
            # Section headers
            {
                "pattern": r"(?:Article|Section)\s+\d+\s*[-–]\s*Definitions\s*\n([^]+?)(?=Article|Section|\n\n)",
                "type": "section",
                "confidence": 0.80
            },
            
            # Contextual definitions
            {
                "pattern": r"(?:In this|For the purposes of this)\s+(?:Act|Regulation|Directive|Article|Section)[^,]+,\s*[\"']?([^\"']+)[\"']?\s+(?:means|refers to)\s+([^.;]+)",
                "type": "contextual",
                "confidence": 0.85
            }
        ]
    
    def extract_definitions(self, text: str, document_id: str, section_id: str = "unknown") -> List[Definition]:
        """Extract definitions from text using multiple methods"""
        definitions = []
        
        # 1. Pattern-based extraction
        pattern_definitions = self._extract_pattern_definitions(text, document_id, section_id)
        definitions.extend(pattern_definitions)
        
        # 2. NLP-based extraction
        nlp_definitions = self._extract_nlp_definitions(text, document_id, section_id)
        definitions.extend(nlp_definitions)
        
        # 3. QA-based extraction for specific terms
        # This would be called with specific entity terms in practice
        
        # Deduplicate and merge
        definitions = self._merge_definitions(definitions)
        
        return definitions
    
    def _extract_pattern_definitions(
        self,
        text: str,
        document_id: str,
        section_id: str
    ) -> List[Definition]:
        """Extract definitions using regex patterns"""
        definitions = []
        
        for pattern_info in self.definition_patterns:
            pattern = pattern_info["pattern"]
            def_type = pattern_info["type"]
            confidence = pattern_info["confidence"]
            
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                if def_type == "section":
                    # Special handling for definition sections
                    section_text = match.group(1)
                    section_defs = self._extract_from_definition_section(
                        section_text, document_id, section_id, confidence
                    )
                    definitions.extend(section_defs)
                else:
                    # Standard pattern extraction
                    groups = match.groups()
                    if len(groups) >= 2:
                        term = groups[0].strip()
                        definition_text = groups[1].strip()
                        
                        # Clean up
                        term = self._clean_term(term)
                        definition_text = self._clean_definition(definition_text)
                        
                        if term and definition_text:
                            definitions.append(Definition(
                                term=term,
                                definition_text=definition_text,
                                document_id=document_id,
                                section_id=section_id,
                                start_pos=match.start(),
                                end_pos=match.end(),
                                confidence=confidence,
                                definition_type=def_type
                            ))
        
        return definitions
    
    def _extract_nlp_definitions(
        self,
        text: str,
        document_id: str,
        section_id: str
    ) -> List[Definition]:
        """Extract definitions using NLP techniques"""
        definitions = []
        
        doc = self.nlp(text)
        
        # Look for definition patterns in dependency parsing
        for sent in doc.sents:
            # Find definition verbs
            definition_verbs = ["mean", "refer", "include", "define"]
            
            for token in sent:
                if token.lemma_ in definition_verbs and token.pos_ == "VERB":
                    # Find subject (term being defined)
                    subject = None
                    for child in token.children:
                        if child.dep_ in ["nsubj", "nsubjpass"]:
                            subject = child
                            break
                    
                    # Find object (definition)
                    obj = None
                    for child in token.children:
                        if child.dep_ in ["dobj", "attr", "prep"]:
                            obj = child
                            break
                    
                    if subject and obj:
                        # Extract full phrases
                        term = self._get_full_phrase(subject)
                        definition_text = self._get_full_phrase(obj)
                        
                        if term and definition_text:
                            definitions.append(Definition(
                                term=term,
                                definition_text=definition_text,
                                document_id=document_id,
                                section_id=section_id,
                                start_pos=sent.start_char,
                                end_pos=sent.end_char,
                                confidence=0.75,
                                definition_type="nlp",
                                context=sent.text
                            ))
        
        return definitions
    
    def _extract_from_definition_section(
        self,
        text: str,
        document_id: str,
        section_id: str,
        confidence: float
    ) -> List[Definition]:
        """Extract definitions from a dedicated definitions section"""
        definitions = []
        
        # Common patterns in definition sections
        patterns = [
            r'["\']([^"\']+)["\']\s*[:–-]\s*([^;]+)',
            r'\b([A-Z][a-zA-Z\s]+)\s*[:–-]\s*([^;]+)',
            r'(?:\([a-z]\)|\d\.)\s*["\']?([^"\']+)["\']?\s*[:–-]\s*([^;]+)'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                term = self._clean_term(match.group(1))
                definition_text = self._clean_definition(match.group(2))
                
                if term and definition_text:
                    definitions.append(Definition(
                        term=term,
                        definition_text=definition_text,
                        document_id=document_id,
                        section_id=section_id,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=confidence,
                        definition_type="section"
                    ))
        
        return definitions
    
    def extract_definition_for_entity(
        self,
        entity: str,
        text: str,
        document_id: str,
        section_id: str = "unknown"
    ) -> Optional[Definition]:
        """Extract definition for a specific entity using QA"""
        
        # Try different question formulations
        questions = [
            f"What is the definition of {entity}?",
            f"What does {entity} mean?",
            f"How is {entity} defined?"
        ]
        
        best_answer = None
        best_score = 0
        
        for question in questions:
            try:
                result = self.qa_pipeline(question=question, context=text)
                
                if result['score'] > best_score:
                    best_score = result['score']
                    best_answer = result
                    
            except Exception as e:
                logger.warning(f"QA extraction failed: {e}")
        
        if best_answer and best_score > 0.5:
            return Definition(
                term=entity,
                definition_text=best_answer['answer'],
                document_id=document_id,
                section_id=section_id,
                start_pos=best_answer['start'],
                end_pos=best_answer['end'],
                confidence=best_score,
                definition_type="qa"
            )
        
        return None
    
    def _get_full_phrase(self, token) -> str:
        """Get full noun phrase or verb phrase from a token"""
        # Get all children
        phrase_tokens = [token]
        
        for child in token.children:
            if child.dep_ in ["det", "amod", "compound", "prep", "pobj"]:
                phrase_tokens.append(child)
        
        # Sort by position
        phrase_tokens.sort(key=lambda t: t.i)
        
        return " ".join([t.text for t in phrase_tokens])
    
    def _clean_term(self, term: str) -> str:
        """Clean and normalize term"""
        # Remove quotes
        term = term.strip('"\'')
        
        # Remove articles at the beginning
        term = re.sub(r'^(?:the|a|an)\s+', '', term, flags=re.IGNORECASE)
        
        # Normalize whitespace
        term = ' '.join(term.split())
        
        return term.strip()
    
    def _clean_definition(self, definition: str) -> str:
        """Clean and normalize definition text"""
        # Remove trailing punctuation
        definition = definition.rstrip('.;,')
        
        # Normalize whitespace
        definition = ' '.join(definition.split())
        
        # Ensure it ends with period
        if definition and not definition.endswith('.'):
            definition += '.'
        
        return definition.strip()
    
    def _merge_definitions(self, definitions: List[Definition]) -> List[Definition]:
        """Merge duplicate definitions"""
        merged = {}
        
        for defn in definitions:
            key = (defn.term.lower(), defn.document_id)
            
            if key not in merged:
                merged[key] = defn
            else:
                # Keep the one with higher confidence or longer definition
                existing = merged[key]
                if (defn.confidence > existing.confidence or
                    len(defn.definition_text) > len(existing.definition_text)):
                    merged[key] = defn
        
        return list(merged.values())
    
    def link_definitions_to_entities(
        self,
        entities: List[str],
        definitions: List[Definition]
    ) -> Dict[str, List[Definition]]:
        """Link definitions to extracted entities"""
        
        entity_definitions = {}
        
        # Normalize entities
        normalized_entities = {e.lower(): e for e in entities}
        
        for defn in definitions:
            term_lower = defn.term.lower()
            
            # Direct match
            if term_lower in normalized_entities:
                original_entity = normalized_entities[term_lower]
                if original_entity not in entity_definitions:
                    entity_definitions[original_entity] = []
                entity_definitions[original_entity].append(defn)
            
            # Partial match
            else:
                for norm_entity, original_entity in normalized_entities.items():
                    if (norm_entity in term_lower or term_lower in norm_entity):
                        if original_entity not in entity_definitions:
                            entity_definitions[original_entity] = []
                        entity_definitions[original_entity].append(defn)
        
        return entity_definitions
    
    def export_definitions(self, definitions: List[Definition], filepath: str):
        """Export definitions to file"""
        
        # Convert to serializable format
        def_data = []
        for defn in definitions:
            def_data.append({
                "term": defn.term,
                "definition": defn.definition_text,
                "document_id": defn.document_id,
                "section_id": defn.section_id,
                "confidence": defn.confidence,
                "type": defn.definition_type,
                "position": {"start": defn.start_pos, "end": defn.end_pos}
            })
        
        with open(filepath, 'w') as f:
            json.dump(def_data, f, indent=2)
        
        logger.info(f"Exported {len(definitions)} definitions to {filepath}")