from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict

from src.models import Document, RegulatedEntity, RegulatedActivity, RegulatedProduct

class DefinitionExtractor:
    """Extracts formal definitions and links to source documents (Task 3)"""
    
    def __init__(self):
        # Definition patterns
        self.definition_patterns = [
            r'"{term}"\s+(?:means|refers to|is defined as|shall mean|includes?)\s+([^.]+\.)',
            r'(?:the term\s+)?"{term}"\s+(?:means|refers to|is defined as|shall mean)\s+([^.]+\.)',
            r'{term}\s+(?:means|refers to|is defined as|shall mean|includes?)\s+([^.]+\.)',
            r'(?:^|\n)\s*{term}[:\s]+([^.]+\.)',
            r'"{term}"[:\s]+([^.]+\.)',
            r'\({term}\)\s+(?:means|refers to|is defined as)\s+([^.]+\.)',
            r'(?:definition of\s+)?{term}\s+is\s+([^.]+\.)'
        ]
        
        # Section patterns for locating definitions
        self.section_patterns = [
            r'(?:section|§)\s*(\d+(?:\.\d+)*)',
            r'(?:article|art\.?)\s*(\d+)',
            r'(?:clause|cl\.?)\s*(\d+(?:\.\d+)*)',
            r'(?:paragraph|para\.?)\s*(\d+(?:\([a-z]\))?)',
            r'(?:rule|reg\.?)\s*(\d+(?:\.\d+)*)'
        ]
        
    def extract_definitions(self,
                          documents: List[Document],
                          entities: List[RegulatedEntity],
                          activities: List[RegulatedActivity],
                          products: List[RegulatedProduct]) -> Dict[str, Any]:
        """Extract formal definitions for all identified items"""
        
        # Collect all items to find definitions for
        all_items = []
        
        for entity in entities:
            all_items.append({
                "name": entity.name,
                "type": "entity",
                "category": entity.entity_type.value,
                "source_doc": entity.source_document_id
            })
        
        for activity in activities:
            all_items.append({
                "name": activity.name,
                "type": "activity",
                "category": activity.activity_type.value,
                "source_doc": activity.source_document_id
            })
        
        for product in products:
            all_items.append({
                "name": product.name,
                "type": "product", 
                "category": product.product_type.value,
                "source_doc": product.source_document_id
            })
        
        # Find definitions
        definitions = self._find_all_definitions(documents, all_items)
        
        # Organize results
        return {
            "entity_definitions": self._organize_definitions(definitions, "entity"),
            "activity_definitions": self._organize_definitions(definitions, "activity"),
            "product_definitions": self._organize_definitions(definitions, "product"),
            "summary": self._generate_definition_summary(definitions, all_items)
        }
    
    def _find_all_definitions(self, documents: List[Document], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find definitions for all items across all documents"""
        definitions = []
        
        # Create a map of document IDs to documents for quick lookup
        doc_map = {doc.document_id: doc for doc in documents}
        
        # Search for each item
        for item in items:
            item_definitions = self._find_item_definitions(documents, item, doc_map)
            definitions.extend(item_definitions)
        
        # Deduplicate and rank definitions
        definitions = self._deduplicate_definitions(definitions)
        
        return definitions
    
    def _find_item_definitions(self, 
                             documents: List[Document], 
                             item: Dict[str, Any],
                             doc_map: Dict[str, Document]) -> List[Dict[str, Any]]:
        """Find all definitions for a single item"""
        definitions = []
        search_terms = self._generate_search_terms(item["name"])
        
        for doc in documents:
            doc_text = self._get_document_text(doc)
            
            # Search for definitions using various patterns
            for term in search_terms:
                for pattern_template in self.definition_patterns:
                    pattern = pattern_template.replace("{term}", re.escape(term))
                    
                    matches = re.finditer(pattern, doc_text, re.IGNORECASE | re.MULTILINE)
                    
                    for match in matches:
                        definition_text = match.group(1) if match.lastindex else match.group(0)
                        
                        # Extract context and location
                        context, location = self._extract_context_and_location(doc_text, match.start(), match.end())
                        
                        definitions.append({
                            "item_name": item["name"],
                            "item_type": item["type"],
                            "item_category": item["category"],
                            "definition_text": definition_text.strip(),
                            "document_id": doc.document_id,
                            "document_title": doc.title or "Unknown",
                            "document_url": self._get_document_url(doc),
                            "location": location,
                            "context": context,
                            "confidence": self._calculate_definition_confidence(
                                definition_text, term, doc.document_id == item["source_doc"]
                            )
                        })
        
        return definitions
    
    def _generate_search_terms(self, name: str) -> List[str]:
        """Generate variations of a term to search for"""
        terms = [name]
        name_lower = name.lower()
        
        # Add variations
        if "adviser" in name_lower:
            terms.append(name.replace("adviser", "advisor"))
            terms.append(name.replace("Adviser", "Advisor"))
        
        if "company" in name_lower:
            terms.append(name.replace("company", "companies"))
            terms.append(name.replace("Company", "Companies"))
        
        # Add acronyms
        acronym_map = {
            "investment adviser": ["IA", "RIA"],
            "investment company": ["IC", "RIC"],
            "ucits": ["UCITS"],
            "exchange-traded fund": ["ETF"],
            "money market fund": ["MMF"]
        }
        
        for key, acronyms in acronym_map.items():
            if key in name_lower:
                terms.extend(acronyms)
        
        return list(set(terms))
    
    def _get_document_text(self, doc: Document) -> str:
        """Extract all text from document"""
        text_parts = []
        
        if doc.title:
            text_parts.append(doc.title)
        
        if doc.source_text:
            for item in doc.source_text:
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
        
        return "\n".join(text_parts)
    
    def _extract_context_and_location(self, text: str, start: int, end: int) -> Tuple[str, Dict[str, Any]]:
        """Extract surrounding context and section location"""
        # Extract context (500 chars before and after)
        context_start = max(0, start - 500)
        context_end = min(len(text), end + 500)
        context = text[context_start:context_end]
        
        # Find section information
        section_info = {}
        text_before = text[:start]
        
        for pattern in self.section_patterns:
            matches = list(re.finditer(pattern, text_before, re.IGNORECASE))
            if matches:
                last_match = matches[-1]
                section_info["section"] = last_match.group(1)
                section_info["section_type"] = pattern.split("(")[0].strip("(?:")
                break
        
        # Find paragraph number
        paragraphs_before = text_before.count("\n\n")
        section_info["paragraph"] = paragraphs_before + 1
        
        # Calculate character position
        section_info["char_position"] = start
        
        return context, section_info
    
    def _get_document_url(self, doc: Document) -> Optional[str]:
        """Get document URL if available"""
        if doc.metadata and "source_urls" in doc.metadata:
            urls = doc.metadata["source_urls"]
            if urls and isinstance(urls, list) and len(urls) > 0:
                return urls[0]
        return None
    
    def _calculate_definition_confidence(self, definition_text: str, term: str, is_source_doc: bool) -> float:
        """Calculate confidence score for a definition"""
        score = 0.5
        
        # Higher score if from source document
        if is_source_doc:
            score += 0.2
        
        # Higher score for longer, more detailed definitions
        word_count = len(definition_text.split())
        if word_count > 20:
            score += 0.1
        if word_count > 50:
            score += 0.1
        
        # Higher score for definitions with specific markers
        formal_markers = ["means", "defined as", "refers to", "shall mean"]
        if any(marker in definition_text.lower() for marker in formal_markers):
            score += 0.1
        
        # Check for quotation marks around the term
        if f'"{term}"' in definition_text or f"'{term}'" in definition_text:
            score += 0.1
        
        return min(score, 1.0)
    
    def _deduplicate_definitions(self, definitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate definitions and keep the best ones"""
        # Group by item and definition text similarity
        grouped = defaultdict(list)
        
        for defn in definitions:
            key = (defn["item_name"], defn["item_type"])
            grouped[key].append(defn)
        
        # For each item, keep the best definitions
        deduplicated = []
        
        for (item_name, item_type), defn_list in grouped.items():
            # Sort by confidence
            defn_list.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Keep top definitions that are sufficiently different
            kept_definitions = []
            
            for defn in defn_list:
                # Check if this definition is similar to any already kept
                is_duplicate = False
                
                for kept in kept_definitions:
                    if self._are_definitions_similar(defn["definition_text"], kept["definition_text"]):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    kept_definitions.append(defn)
                    
                # Keep max 3 definitions per item
                if len(kept_definitions) >= 3:
                    break
            
            deduplicated.extend(kept_definitions)
        
        return deduplicated
    
    def _are_definitions_similar(self, def1: str, def2: str) -> bool:
        """Check if two definitions are similar"""
        # Simple similarity check based on word overlap
        words1 = set(def1.lower().split())
        words2 = set(def2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        
        return similarity > 0.8
    
    def _organize_definitions(self, definitions: List[Dict[str, Any]], item_type: str) -> List[Dict[str, Any]]:
        """Organize definitions by item type"""
        type_definitions = [d for d in definitions if d["item_type"] == item_type]
        
        # Group by item name
        organized = defaultdict(list)
        
        for defn in type_definitions:
            organized[defn["item_name"]].append({
                "definition": defn["definition_text"],
                "source": {
                    "document_id": defn["document_id"],
                    "document_title": defn["document_title"],
                    "document_url": defn["document_url"],
                    "location": defn["location"]
                },
                "confidence": defn["confidence"],
                "context": defn["context"]
            })
        
        # Convert to list format
        result = []
        for item_name, defn_list in organized.items():
            result.append({
                "name": item_name,
                "definitions": sorted(defn_list, key=lambda x: x["confidence"], reverse=True)
            })
        
        return sorted(result, key=lambda x: x["name"])
    
    def _generate_definition_summary(self, definitions: List[Dict[str, Any]], all_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        items_with_definitions = set()
        
        for defn in definitions:
            items_with_definitions.add((defn["item_name"], defn["item_type"]))
        
        # Count by type
        type_counts = defaultdict(lambda: {"total": 0, "with_definitions": 0})
        
        for item in all_items:
            type_counts[item["type"]]["total"] += 1
            if (item["name"], item["type"]) in items_with_definitions:
                type_counts[item["type"]]["with_definitions"] += 1
        
        # Document statistics
        docs_with_definitions = len(set(d["document_id"] for d in definitions))
        
        return {
            "total_items": len(all_items),
            "items_with_definitions": len(items_with_definitions),
            "coverage_percentage": round(len(items_with_definitions) / len(all_items) * 100, 2) if all_items else 0,
            "total_definitions_found": len(definitions),
            "documents_with_definitions": docs_with_definitions,
            "coverage_by_type": dict(type_counts),
            "average_confidence": round(sum(d["confidence"] for d in definitions) / len(definitions), 2) if definitions else 0
        }