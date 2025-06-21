from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import re

from src.models import Document, RegulatedEntity, RegulatedActivity, RegulatedProduct

class DocumentRelevancePredictor:
    """Predicts which regulated items each document is relevant to (Task 2)"""
    
    def __init__(self):
        self.relevance_threshold = 0.3
        
    def predict_relevance(self, 
                         documents: List[Document],
                         entities: List[RegulatedEntity],
                         activities: List[RegulatedActivity],
                         products: List[RegulatedProduct]) -> Dict[str, Any]:
        """Predict document relevance to extracted items"""
        
        # Build keyword mappings for each category
        entity_keywords = self._build_entity_keywords(entities)
        activity_keywords = self._build_activity_keywords(activities)
        product_keywords = self._build_product_keywords(products)
        
        # Analyze each document
        relevance_results = []
        
        for doc in documents:
            doc_relevance = self._analyze_document_relevance(
                doc, entity_keywords, activity_keywords, product_keywords
            )
            
            if doc_relevance["total_relevance_score"] > 0:
                relevance_results.append(doc_relevance)
        
        # Sort by relevance score
        relevance_results.sort(key=lambda x: x["total_relevance_score"], reverse=True)
        
        return {
            "document_relevance": relevance_results,
            "summary": self._generate_relevance_summary(relevance_results, len(documents))
        }
    
    def _build_entity_keywords(self, entities: List[RegulatedEntity]) -> Dict[str, Set[str]]:
        """Build keyword mappings for entities"""
        keywords = defaultdict(set)
        
        for entity in entities:
            # Add entity name and variations
            base_name = entity.name.lower()
            keywords[entity.entity_type.value].add(base_name)
            
            # Add common variations
            if "adviser" in base_name:
                keywords[entity.entity_type.value].add(base_name.replace("adviser", "advisor"))
            if "company" in base_name:
                keywords[entity.entity_type.value].add(base_name.replace("company", "companies"))
            
            # Add type-specific keywords
            type_keywords = {
                "investment_adviser": ["ria", "registered investment", "advisory"],
                "investment_company": ["40 act", "mutual fund", "closed-end"],
                "ucits": ["undertaking", "collective investment", "transferable securities"],
                "management_company": ["manco", "fund manager", "asset manager"],
                "depositary": ["custodian", "trustee", "safekeeping"]
            }
            
            if entity.entity_type.value in type_keywords:
                keywords[entity.entity_type.value].update(type_keywords[entity.entity_type.value])
        
        return dict(keywords)
    
    def _build_activity_keywords(self, activities: List[RegulatedActivity]) -> Dict[str, Set[str]]:
        """Build keyword mappings for activities"""
        keywords = defaultdict(set)
        
        for activity in activities:
            # Add activity name and variations
            base_name = activity.name.lower()
            keywords[activity.activity_type.value].add(base_name)
            
            # Add type-specific keywords
            type_keywords = {
                "asset_management": ["aum", "discretionary", "portfolio construction"],
                "investment_advice": ["recommendation", "suitability", "fiduciary"],
                "portfolio_management": ["rebalancing", "asset allocation", "optimization"],
                "custody": ["safekeeping", "settlement", "asset servicing"],
                "distribution": ["marketing", "placement", "selling"],
                "fund_administration": ["nav", "transfer agency", "shareholder services"],
                "risk_management": ["var", "stress testing", "risk monitoring"],
                "compliance": ["regulatory", "oversight", "monitoring"],
                "reporting": ["disclosure", "transparency", "filing"]
            }
            
            if activity.activity_type.value in type_keywords:
                keywords[activity.activity_type.value].update(type_keywords[activity.activity_type.value])
        
        return dict(keywords)
    
    def _build_product_keywords(self, products: List[RegulatedProduct]) -> Dict[str, Set[str]]:
        """Build keyword mappings for products"""
        keywords = defaultdict(set)
        
        for product in products:
            # Add product name and variations
            base_name = product.name.lower()
            keywords[product.product_type.value].add(base_name)
            
            # Add type-specific keywords
            type_keywords = {
                "mutual_fund": ["open-end", "nav", "redemption"],
                "etf": ["exchange traded", "creation unit", "authorized participant"],
                "ucits_fund": ["eu passport", "kiid", "transferable securities"],
                "hedge_fund": ["alternative", "accredited", "performance fee"],
                "money_market_fund": ["stable nav", "liquidity", "short-term"],
                "investment_trust": ["closed-end", "premium", "discount"],
                "collective_investment_scheme": ["pooled", "units", "collective"]
            }
            
            if product.product_type.value in type_keywords:
                keywords[product.product_type.value].update(type_keywords[product.product_type.value])
        
        return dict(keywords)
    
    def _analyze_document_relevance(self, 
                                  doc: Document,
                                  entity_keywords: Dict[str, Set[str]],
                                  activity_keywords: Dict[str, Set[str]],
                                  product_keywords: Dict[str, Set[str]]) -> Dict[str, Any]:
        """Analyze relevance of a single document"""
        
        # Get document text
        doc_text = self._get_document_text(doc).lower()
        doc_title = (doc.title or "").lower()
        
        # Calculate relevance scores
        entity_relevance = self._calculate_keyword_relevance(doc_text, doc_title, entity_keywords)
        activity_relevance = self._calculate_keyword_relevance(doc_text, doc_title, activity_keywords)
        product_relevance = self._calculate_keyword_relevance(doc_text, doc_title, product_keywords)
        
        # Analyze sub-document relevance (signposts)
        subdoc_relevance = self._analyze_subdocument_relevance(doc, entity_keywords, activity_keywords, product_keywords)
        
        # Calculate total score
        total_score = sum(entity_relevance.values()) + sum(activity_relevance.values()) + sum(product_relevance.values())
        
        return {
            "document_id": doc.document_id,
            "title": doc.title or "Unknown",
            "publishers": [p.get("name", "") for p in (doc.publishers or [])],
            "published_date": doc.published or "Unknown",
            "relevant_entities": {k: v for k, v in entity_relevance.items() if v > self.relevance_threshold},
            "relevant_activities": {k: v for k, v in activity_relevance.items() if v > self.relevance_threshold},
            "relevant_products": {k: v for k, v in product_relevance.items() if v > self.relevance_threshold},
            "subdocument_relevance": subdoc_relevance,
            "total_relevance_score": total_score,
            "primary_focus": self._determine_primary_focus(entity_relevance, activity_relevance, product_relevance)
        }
    
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
        
        return " ".join(text_parts)
    
    def _calculate_keyword_relevance(self, 
                                   doc_text: str,
                                   doc_title: str,
                                   keyword_dict: Dict[str, Set[str]]) -> Dict[str, float]:
        """Calculate relevance scores based on keyword matches"""
        relevance_scores = {}
        
        for category, keywords in keyword_dict.items():
            score = 0.0
            matches = 0
            
            for keyword in keywords:
                # Count occurrences in title (weighted higher)
                title_matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', doc_title))
                score += title_matches * 2.0
                
                # Count occurrences in text
                text_matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', doc_text))
                score += text_matches * 0.1
                
                if title_matches > 0 or text_matches > 0:
                    matches += 1
            
            # Normalize by number of keywords
            if len(keywords) > 0:
                relevance_scores[category] = score / len(keywords)
            else:
                relevance_scores[category] = 0.0
        
        return relevance_scores
    
    def _analyze_subdocument_relevance(self,
                                     doc: Document,
                                     entity_keywords: Dict[str, Set[str]],
                                     activity_keywords: Dict[str, Set[str]],
                                     product_keywords: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        """Analyze relevance at sub-document level (signposts)"""
        subdoc_results = []
        
        if not doc.signposts:
            return subdoc_results
        
        for i, signpost in enumerate(doc.signposts):
            if isinstance(signpost, dict):
                signpost_text = signpost.get("text", "").lower()
                signpost_tags = signpost.get("tags", [])
                
                # Calculate relevance for this signpost
                entity_rel = self._calculate_keyword_relevance(signpost_text, "", entity_keywords)
                activity_rel = self._calculate_keyword_relevance(signpost_text, "", activity_keywords)
                product_rel = self._calculate_keyword_relevance(signpost_text, "", product_keywords)
                
                # Check if any relevance is significant
                if any(v > self.relevance_threshold for v in entity_rel.values()) or \
                   any(v > self.relevance_threshold for v in activity_rel.values()) or \
                   any(v > self.relevance_threshold for v in product_rel.values()):
                    
                    subdoc_results.append({
                        "signpost_index": i,
                        "tags": signpost_tags,
                        "text_preview": signpost_text[:200] + "..." if len(signpost_text) > 200 else signpost_text,
                        "relevant_entities": {k: v for k, v in entity_rel.items() if v > self.relevance_threshold},
                        "relevant_activities": {k: v for k, v in activity_rel.items() if v > self.relevance_threshold},
                        "relevant_products": {k: v for k, v in product_rel.items() if v > self.relevance_threshold}
                    })
        
        return subdoc_results
    
    def _determine_primary_focus(self,
                               entity_scores: Dict[str, float],
                               activity_scores: Dict[str, float],
                               product_scores: Dict[str, float]) -> str:
        """Determine the primary focus of a document"""
        all_scores = []
        
        for category, score in entity_scores.items():
            if score > self.relevance_threshold:
                all_scores.append(("entity", category, score))
        
        for category, score in activity_scores.items():
            if score > self.relevance_threshold:
                all_scores.append(("activity", category, score))
        
        for category, score in product_scores.items():
            if score > self.relevance_threshold:
                all_scores.append(("product", category, score))
        
        if not all_scores:
            return "general"
        
        # Sort by score
        all_scores.sort(key=lambda x: x[2], reverse=True)
        
        return f"{all_scores[0][0]}:{all_scores[0][1]}"
    
    def _generate_relevance_summary(self, results: List[Dict[str, Any]], total_docs: int) -> Dict[str, Any]:
        """Generate summary statistics"""
        relevant_docs = len(results)
        
        # Count documents by primary focus
        focus_counts = defaultdict(int)
        for result in results:
            focus_counts[result["primary_focus"]] += 1
        
        # Find most common relevance patterns
        entity_counts = defaultdict(int)
        activity_counts = defaultdict(int)
        product_counts = defaultdict(int)
        
        for result in results:
            for entity in result["relevant_entities"]:
                entity_counts[entity] += 1
            for activity in result["relevant_activities"]:
                activity_counts[activity] += 1
            for product in result["relevant_products"]:
                product_counts[product] += 1
        
        return {
            "total_documents_analyzed": total_docs,
            "relevant_documents": relevant_docs,
            "relevance_percentage": round(relevant_docs / total_docs * 100, 2) if total_docs > 0 else 0,
            "primary_focus_distribution": dict(focus_counts),
            "top_relevant_entities": sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_relevant_activities": sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_relevant_products": sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }