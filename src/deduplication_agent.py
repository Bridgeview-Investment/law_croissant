from typing import List, Dict, Set, Tuple
from collections import defaultdict
import re
from src.models import RegulatedEntity, RegulatedActivity, RegulatedProduct, ExtractedItem

class DeduplicationAgent:
    """Agent responsible for deduplicating and consolidating extracted items"""
    
    def __init__(self):
        self.similarity_threshold = 0.85
        
    def deduplicate_results(self, 
                          entities: List[RegulatedEntity],
                          activities: List[RegulatedActivity], 
                          products: List[RegulatedProduct]) -> Tuple[List[RegulatedEntity], 
                                                                    List[RegulatedActivity],
                                                                    List[RegulatedProduct]]:
        """Deduplicate all extracted items"""
        
        # Deduplicate each category
        unique_entities = self._deduplicate_entities(entities)
        unique_activities = self._deduplicate_activities(activities)
        unique_products = self._deduplicate_products(products)
        
        return unique_entities, unique_activities, unique_products
    
    def _deduplicate_entities(self, entities: List[RegulatedEntity]) -> List[RegulatedEntity]:
        """Deduplicate entities based on name and type"""
        grouped = defaultdict(list)
        
        # Group by entity type
        for entity in entities:
            key = (self._normalize_name(entity.name), entity.entity_type)
            grouped[key].append(entity)
        
        # Merge duplicates
        unique_entities = []
        for (name, entity_type), group in grouped.items():
            merged = self._merge_entities(group)
            unique_entities.append(merged)
        
        return unique_entities
    
    def _deduplicate_activities(self, activities: List[RegulatedActivity]) -> List[RegulatedActivity]:
        """Deduplicate activities based on name and type"""
        grouped = defaultdict(list)
        
        # Group by activity type
        for activity in activities:
            key = (self._normalize_name(activity.name), activity.activity_type)
            grouped[key].append(activity)
        
        # Merge duplicates
        unique_activities = []
        for (name, activity_type), group in grouped.items():
            merged = self._merge_activities(group)
            unique_activities.append(merged)
        
        return unique_activities
    
    def _deduplicate_products(self, products: List[RegulatedProduct]) -> List[RegulatedProduct]:
        """Deduplicate products based on name and type"""
        grouped = defaultdict(list)
        
        # Group by product type
        for product in products:
            key = (self._normalize_name(product.name), product.product_type)
            grouped[key].append(product)
        
        # Merge duplicates
        unique_products = []
        for (name, product_type), group in grouped.items():
            merged = self._merge_products(group)
            unique_products.append(merged)
        
        # Additional deduplication for similar product names
        unique_products = self._merge_similar_products(unique_products)
        
        return unique_products
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        # Remove extra spaces, convert to lowercase
        normalized = " ".join(name.lower().split())
        
        # Remove common suffixes
        suffixes = [r"\s*\(s\)", r"s$", r"ies$"]
        for suffix in suffixes:
            normalized = re.sub(suffix, "", normalized)
        
        # Standardize common terms
        replacements = {
            "adviser": "advisor",
            "organisation": "organization",
            "authorised": "authorized"
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized.strip()
    
    def _merge_entities(self, entities: List[RegulatedEntity]) -> RegulatedEntity:
        """Merge multiple entity instances into one"""
        if len(entities) == 1:
            return entities[0]
        
        # Use the entity with highest confidence as base
        base = max(entities, key=lambda e: e.confidence)
        
        # Combine source documents
        all_sources = set()
        all_jurisdictions = set()
        all_frameworks = set()
        
        for entity in entities:
            all_sources.add(entity.source_document_id)
            if entity.jurisdiction:
                all_jurisdictions.add(entity.jurisdiction)
            if entity.regulatory_framework:
                all_frameworks.add(entity.regulatory_framework)
        
        # Update metadata
        base.metadata["source_documents"] = list(all_sources)
        base.metadata["occurrences"] = len(entities)
        
        if all_jurisdictions:
            base.jurisdiction = ", ".join(sorted(all_jurisdictions))
        if all_frameworks:
            base.regulatory_framework = ", ".join(sorted(all_frameworks))
        
        # Update confidence based on multiple occurrences
        base.confidence = min(1.0, base.confidence + (len(entities) - 1) * 0.05)
        
        return base
    
    def _merge_activities(self, activities: List[RegulatedActivity]) -> RegulatedActivity:
        """Merge multiple activity instances into one"""
        if len(activities) == 1:
            return activities[0]
        
        # Use the activity with most complete information as base
        base = max(activities, key=lambda a: len(a.requirements or []) + len(a.applicable_entities or []))
        
        # Combine all unique entities and requirements
        all_entities = set()
        all_requirements = set()
        all_sources = set()
        
        for activity in activities:
            all_sources.add(activity.source_document_id)
            if activity.applicable_entities:
                all_entities.update(activity.applicable_entities)
            if activity.requirements:
                all_requirements.update(activity.requirements)
        
        base.applicable_entities = sorted(list(all_entities))
        base.requirements = sorted(list(all_requirements))[:10]  # Limit to top 10
        
        # Update metadata
        base.metadata["source_documents"] = list(all_sources)
        base.metadata["occurrences"] = len(activities)
        
        # Update confidence
        base.confidence = min(1.0, base.confidence + (len(activities) - 1) * 0.05)
        
        return base
    
    def _merge_products(self, products: List[RegulatedProduct]) -> RegulatedProduct:
        """Merge multiple product instances into one"""
        if len(products) == 1:
            return products[0]
        
        # Use the product with most complete information as base
        base = max(products, key=lambda p: len(p.issuer_requirements or []) + len(p.investor_restrictions or []))
        
        # Combine all unique requirements and restrictions
        all_issuer_reqs = set()
        all_investor_restrictions = set()
        all_sources = set()
        all_asset_classes = set()
        
        for product in products:
            all_sources.add(product.source_document_id)
            if product.issuer_requirements:
                all_issuer_reqs.update(product.issuer_requirements)
            if product.investor_restrictions:
                all_investor_restrictions.update(product.investor_restrictions)
            if "asset_classes" in product.metadata:
                all_asset_classes.update(product.metadata["asset_classes"])
        
        base.issuer_requirements = sorted(list(all_issuer_reqs))[:10]
        base.investor_restrictions = sorted(list(all_investor_restrictions))[:10]
        
        # Update metadata
        base.metadata["source_documents"] = list(all_sources)
        base.metadata["occurrences"] = len(products)
        base.metadata["asset_classes"] = sorted(list(all_asset_classes))
        
        # Update confidence
        base.confidence = min(1.0, base.confidence + (len(products) - 1) * 0.05)
        
        return base
    
    def _merge_similar_products(self, products: List[RegulatedProduct]) -> List[RegulatedProduct]:
        """Additional pass to merge products with similar names"""
        merged = []
        processed = set()
        
        for i, product1 in enumerate(products):
            if i in processed:
                continue
                
            similar_group = [product1]
            
            for j, product2 in enumerate(products[i+1:], i+1):
                if j in processed:
                    continue
                    
                if self._are_similar(product1.name, product2.name):
                    similar_group.append(product2)
                    processed.add(j)
            
            if len(similar_group) > 1:
                merged_product = self._merge_products(similar_group)
                merged.append(merged_product)
            else:
                merged.append(product1)
        
        return merged
    
    def _are_similar(self, name1: str, name2: str) -> bool:
        """Check if two names are similar enough to merge"""
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return True
        
        # Check if one is contained in the other
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Check Jaccard similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        
        return similarity >= self.similarity_threshold