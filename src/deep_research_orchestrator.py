import asyncio
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from src.config import Config
from src.api_client import RegGenomeAPIClient
from src.models import Document, ResearchResult, RegulatedEntity, RegulatedActivity, RegulatedProduct
from src.agents.entity_extraction_agent import EntityExtractionAgent
from src.agents.activity_extraction_agent import ActivityExtractionAgent
from src.agents.product_extraction_agent import ProductExtractionAgent
from src.deduplication_agent import DeduplicationAgent

class DeepResearchOrchestrator:
    """Orchestrates multiple agents to perform deep research on regulatory documents"""
    
    def __init__(self, config: Config):
        self.config = config
        self.entity_agent = EntityExtractionAgent()
        self.activity_agent = ActivityExtractionAgent()
        self.product_agent = ProductExtractionAgent()
        self.dedup_agent = DeduplicationAgent()
        
    async def research(self, query: str) -> ResearchResult:
        """Main research method that coordinates all agents"""
        print(f"[Orchestrator] Starting deep research for query: {query}")
        
        # Step 1: Fetch relevant documents
        documents = await self._fetch_documents()
        print(f"[Orchestrator] Fetched {len(documents)} documents")
        
        # Step 2: Extract information in parallel using multiple agents
        entities, activities, products = await self._parallel_extraction(documents)
        
        print(f"[Orchestrator] Initial extraction complete:")
        print(f"  - Entities: {len(entities)}")
        print(f"  - Activities: {len(activities)}")
        print(f"  - Products: {len(products)}")
        
        # Step 3: Deduplicate and consolidate results
        unique_entities, unique_activities, unique_products = self.dedup_agent.deduplicate_results(
            entities, activities, products
        )
        
        print(f"[Orchestrator] Deduplication complete:")
        print(f"  - Unique Entities: {len(unique_entities)}")
        print(f"  - Unique Activities: {len(unique_activities)}")
        print(f"  - Unique Products: {len(unique_products)}")
        
        # Step 4: Create final research result
        result = ResearchResult(
            entities=unique_entities,
            activities=unique_activities,
            products=unique_products,
            total_documents_processed=len(documents),
            extraction_metadata={
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "initiatives": list(self.config.initiative_filters.values()),
                    "max_pages": self.config.max_pages_per_query,
                    "page_size": self.config.page_size
                },
                "statistics": {
                    "total_entities_extracted": len(entities),
                    "unique_entities": len(unique_entities),
                    "total_activities_extracted": len(activities),
                    "unique_activities": len(unique_activities),
                    "total_products_extracted": len(products),
                    "unique_products": len(unique_products),
                    "deduplication_ratio": self._calculate_dedup_ratio(
                        len(entities) + len(activities) + len(products),
                        len(unique_entities) + len(unique_activities) + len(unique_products)
                    )
                }
            }
        )
        
        return result
    
    async def _fetch_documents(self) -> List[Document]:
        """Fetch documents from RegGenome API"""
        async with RegGenomeAPIClient(self.config) as client:
            # Fetch documents for all configured initiatives
            initiative_names = list(self.config.initiative_filters.values())
            documents = await client.fetch_all_documents_for_initiatives(initiative_names)
            
            return documents
    
    async def _parallel_extraction(self, documents: List[Document]) -> tuple:
        """Run extraction agents in parallel"""
        all_entities = []
        all_activities = []
        all_products = []
        
        # Process documents in batches to avoid overwhelming the system
        batch_size = 10
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            
            # Run extraction for each document in parallel
            tasks = []
            for doc in batch:
                tasks.append(self._extract_from_document(doc))
            
            # Wait for all extractions in this batch to complete
            batch_results = await asyncio.gather(*tasks)
            
            # Aggregate results
            for entities, activities, products in batch_results:
                all_entities.extend(entities)
                all_activities.extend(activities)
                all_products.extend(products)
        
        return all_entities, all_activities, all_products
    
    async def _extract_from_document(self, document: Document) -> tuple:
        """Extract entities, activities, and products from a single document"""
        # Run extraction agents in parallel using thread pool
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit extraction tasks
            entity_future = loop.run_in_executor(
                executor, self.entity_agent.extract_entities, document
            )
            activity_future = loop.run_in_executor(
                executor, self.activity_agent.extract_activities, document
            )
            product_future = loop.run_in_executor(
                executor, self.product_agent.extract_products, document
            )
            
            # Wait for all extractions to complete
            entities = await entity_future
            activities = await activity_future
            products = await product_future
            
        return entities, activities, products
    
    def _calculate_dedup_ratio(self, total: int, unique: int) -> float:
        """Calculate deduplication ratio"""
        if total == 0:
            return 0.0
        return round((total - unique) / total, 3)
    
    def generate_hierarchical_table(self, result: ResearchResult) -> Dict[str, Any]:
        """Generate hierarchical table structure for Task 1"""
        table = {
            "regulated_entities": self._format_entities(result.entities),
            "regulated_activities": self._format_activities(result.activities),
            "regulated_products": self._format_products(result.products),
            "summary": {
                "total_unique_items": len(result.entities) + len(result.activities) + len(result.products),
                "documents_processed": result.total_documents_processed,
                "extraction_date": result.extraction_metadata["timestamp"]
            }
        }
        
        return table
    
    def _format_entities(self, entities: List[RegulatedEntity]) -> List[Dict[str, Any]]:
        """Format entities for hierarchical table"""
        formatted = []
        
        # Group by entity type
        by_type = {}
        for entity in entities:
            type_name = entity.entity_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append({
                "name": entity.name,
                "description": entity.description,
                "jurisdiction": entity.jurisdiction,
                "regulatory_framework": entity.regulatory_framework,
                "confidence": entity.confidence,
                "sources": entity.metadata.get("source_documents", [entity.source_document_id])
            })
        
        # Convert to list format
        for entity_type, items in sorted(by_type.items()):
            formatted.append({
                "type": entity_type,
                "count": len(items),
                "items": sorted(items, key=lambda x: x["confidence"], reverse=True)
            })
        
        return formatted
    
    def _format_activities(self, activities: List[RegulatedActivity]) -> List[Dict[str, Any]]:
        """Format activities for hierarchical table"""
        formatted = []
        
        # Group by activity type
        by_type = {}
        for activity in activities:
            type_name = activity.activity_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append({
                "name": activity.name,
                "description": activity.description,
                "applicable_entities": activity.applicable_entities or [],
                "requirements": activity.requirements[:3] if activity.requirements else [],  # Top 3
                "confidence": activity.confidence,
                "sources": activity.metadata.get("source_documents", [activity.source_document_id])
            })
        
        # Convert to list format
        for activity_type, items in sorted(by_type.items()):
            formatted.append({
                "type": activity_type,
                "count": len(items),
                "items": sorted(items, key=lambda x: x["confidence"], reverse=True)
            })
        
        return formatted
    
    def _format_products(self, products: List[RegulatedProduct]) -> List[Dict[str, Any]]:
        """Format products for hierarchical table"""
        formatted = []
        
        # Group by product type
        by_type = {}
        for product in products:
            type_name = product.product_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append({
                "name": product.name,
                "description": product.description,
                "asset_classes": product.metadata.get("asset_classes", []),
                "issuer_requirements": product.issuer_requirements[:3] if product.issuer_requirements else [],
                "investor_restrictions": product.investor_restrictions[:3] if product.investor_restrictions else [],
                "confidence": product.confidence,
                "sources": product.metadata.get("source_documents", [product.source_document_id])
            })
        
        # Convert to list format
        for product_type, items in sorted(by_type.items()):
            formatted.append({
                "type": product_type,
                "count": len(items),
                "items": sorted(items, key=lambda x: x["confidence"], reverse=True)
            })
        
        return formatted