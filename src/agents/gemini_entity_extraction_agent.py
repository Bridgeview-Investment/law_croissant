"""
Gemini-Enhanced Entity Extraction Agent

This agent uses Google Gemini 2.5 Pro for enhanced entity extraction
with better understanding of financial regulatory context.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from src.models import Document, RegulatedEntity, RegulatedActivity, RegulatedProduct
from src.models import EntityType, ActivityType, ProductType
from src.gemini_client import GeminiClient, GeminiEnhancedExtractor

class GeminiEntityExtractionAgent:
    """Enhanced entity extraction using Gemini 2.5 Pro"""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.gemini_extractor = GeminiEnhancedExtractor(gemini_client)
        
        # Mapping from Gemini categories to our enum types
        self.entity_type_mapping = {
            "investment_adviser": EntityType.INVESTMENT_ADVISER,
            "investment_company": EntityType.INVESTMENT_COMPANY,
            "fund_manager": EntityType.MANAGEMENT_COMPANY,
            "management_company": EntityType.MANAGEMENT_COMPANY,
            "depositary": EntityType.DEPOSITARY,
            "ucits": EntityType.UCITS,
            "bank": EntityType.INVESTMENT_ADVISER,  # Map to closest available
            "financial_institution": EntityType.INVESTMENT_ADVISER,
            "regulatory_body": EntityType.INVESTMENT_ADVISER,
        }
        
        self.activity_type_mapping = {
            "portfolio_management": ActivityType.PORTFOLIO_MANAGEMENT,
            "investment_advice": ActivityType.INVESTMENT_ADVICE,
            "asset_management": ActivityType.ASSET_MANAGEMENT,
            "custody": ActivityType.CUSTODY,
            "distribution": ActivityType.DISTRIBUTION,
            "fund_administration": ActivityType.FUND_ADMINISTRATION,
            "risk_management": ActivityType.RISK_MANAGEMENT,
            "compliance": ActivityType.COMPLIANCE,
            "reporting": ActivityType.REPORTING,
            "trading": ActivityType.PORTFOLIO_MANAGEMENT,  # Map to closest
            "safekeeping": ActivityType.CUSTODY,
            "marketing": ActivityType.DISTRIBUTION,
        }
        
        self.product_type_mapping = {
            "mutual_fund": ProductType.MUTUAL_FUND,
            "ucits_fund": ProductType.UCITS_FUND,
            "etf": ProductType.ETF,
            "hedge_fund": ProductType.HEDGE_FUND,
            "money_market_fund": ProductType.MONEY_MARKET_FUND,
            "investment_trust": ProductType.INVESTMENT_TRUST,
            "collective_investment_scheme": ProductType.COLLECTIVE_INVESTMENT_SCHEME,
            "securities": ProductType.MUTUAL_FUND,  # Map to closest
            "derivatives": ProductType.HEDGE_FUND,  # Map to closest
            "bonds": ProductType.MUTUAL_FUND,
            "shares": ProductType.MUTUAL_FUND,
        }
    
    async def extract_entities(self, documents: List[Document]) -> Dict[str, Any]:
        """Extract entities using Gemini with improved accuracy"""
        
        print(f"🤖 Using Gemini 2.5 Pro for entity extraction from {len(documents)} documents...")
        
        all_entities = []
        all_activities = []
        all_products = []
        
        # Process documents in batches to respect API limits
        batch_size = 5
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            print(f"   Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}...")
            
            # Process batch concurrently
            tasks = [self.gemini_extractor.extract_from_document(doc) for doc in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for doc, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logging.error(f"Error processing document {doc.document_id}: {result}")
                    continue
                
                # Convert Gemini results to our model objects
                entities = self._convert_to_entities(result.get("entities", []), doc)
                activities = self._convert_to_activities(result.get("activities", []), doc)
                products = self._convert_to_products(result.get("products", []), doc)
                
                all_entities.extend(entities)
                all_activities.extend(activities)
                all_products.extend(products)
            
            # Add small delay to respect rate limits
            await asyncio.sleep(1)
        
        print(f"✅ Gemini extraction complete:")
        print(f"   - Entities: {len(all_entities)}")
        print(f"   - Activities: {len(all_activities)}")
        print(f"   - Products: {len(all_products)}")
        
        return {
            "entities": all_entities,
            "activities": all_activities,
            "products": all_products,
            "extraction_method": "gemini-2.5-pro"
        }
    
    def _convert_to_entities(self, gemini_entities: List[Dict[str, Any]], doc: Document) -> List[RegulatedEntity]:
        """Convert Gemini entity results to RegulatedEntity objects"""
        entities = []
        
        for item in gemini_entities:
            try:
                # Map category to our enum type
                category = item.get("category", "").lower()
                entity_type = self.entity_type_mapping.get(category, EntityType.INVESTMENT_ADVISER)
                
                entity = RegulatedEntity(
                    name=item["name"],
                    entity_type=entity_type,
                    description=item.get("description", ""),
                    confidence=float(item.get("confidence", 0.5)),
                    source_document_id=doc.document_id,
                    jurisdiction=self._extract_jurisdiction(doc),
                    regulatory_framework=self._extract_framework(doc)
                )
                entities.append(entity)
                
            except Exception as e:
                logging.error(f"Error converting entity {item}: {e}")
                continue
        
        return entities
    
    def _convert_to_activities(self, gemini_activities: List[Dict[str, Any]], doc: Document) -> List[RegulatedActivity]:
        """Convert Gemini activity results to RegulatedActivity objects"""
        activities = []
        
        for item in gemini_activities:
            try:
                # Map category to our enum type
                category = item.get("category", "").lower()
                activity_type = self.activity_type_mapping.get(category, ActivityType.PORTFOLIO_MANAGEMENT)
                
                activity = RegulatedActivity(
                    name=item["name"],
                    activity_type=activity_type,
                    description=item.get("description", ""),
                    confidence=float(item.get("confidence", 0.5)),
                    source_document_id=doc.document_id,
                    applicable_entities=self._extract_applicable_entities(item, doc)
                )
                activities.append(activity)
                
            except Exception as e:
                logging.error(f"Error converting activity {item}: {e}")
                continue
        
        return activities
    
    def _convert_to_products(self, gemini_products: List[Dict[str, Any]], doc: Document) -> List[RegulatedProduct]:
        """Convert Gemini product results to RegulatedProduct objects"""
        products = []
        
        for item in gemini_products:
            try:
                # Map category to our enum type
                category = item.get("category", "").lower()
                product_type = self.product_type_mapping.get(category, ProductType.MUTUAL_FUND)
                
                product = RegulatedProduct(
                    name=item["name"],
                    product_type=product_type,
                    description=item.get("description", ""),
                    confidence=float(item.get("confidence", 0.5)),
                    source_document_id=doc.document_id,
                    asset_classes=self._extract_asset_classes(item, doc)
                )
                products.append(product)
                
            except Exception as e:
                logging.error(f"Error converting product {item}: {e}")
                continue
        
        return products
    
    def _extract_jurisdiction(self, doc: Document) -> Optional[str]:
        """Extract jurisdiction from document metadata or content"""
        if doc.publishers:
            for publisher in doc.publishers:
                name = publisher.get("name", "").lower()
                if "sec" in name or "us" in name:
                    return "US"
                elif "eu" in name or "esma" in name:
                    return "EU"
                elif "uk" in name or "fca" in name:
                    return "UK"
        
        # Check document title
        title = (doc.title or "").lower()
        if "us" in title or "sec" in title:
            return "US"
        elif "eu" in title or "ucits" in title:
            return "EU"
        elif "uk" in title:
            return "UK"
        
        return None
    
    def _extract_framework(self, doc: Document) -> Optional[str]:
        """Extract regulatory framework from document"""
        title = (doc.title or "").lower()
        
        if "investment advisers act" in title:
            return "Investment Advisers Act 1940"
        elif "investment company act" in title:
            return "Investment Company Act 1940"
        elif "ucits" in title:
            return "UCITS Directive"
        
        return None
    
    def _extract_applicable_entities(self, item: Dict[str, Any], doc: Document) -> List[str]:
        """Extract applicable entities for an activity"""
        # This could be enhanced with Gemini's context understanding
        return []
    
    def _extract_asset_classes(self, item: Dict[str, Any], doc: Document) -> List[str]:
        """Extract asset classes for a product"""
        # This could be enhanced with Gemini's context understanding
        return []

# Function to create Gemini-enhanced agent
def create_gemini_entity_agent(gemini_client: GeminiClient) -> GeminiEntityExtractionAgent:
    """Create a Gemini-enhanced entity extraction agent"""
    return GeminiEntityExtractionAgent(gemini_client)