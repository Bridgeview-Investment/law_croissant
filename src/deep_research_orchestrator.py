"""Deep Research Orchestrator for RegGenome regulatory document analysis."""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from .config import config
from .models import (
    RegGenomeDocument, RegulatoryTaxonomy, ResearchState,
    RegulatedEntity, RegulatedActivity, RegulatedProduct,
    DocumentRelevance
)
from .api_client import RegGenomeAPIClient, MockRegGenomeAPIClient
from .agents.entity_extraction_agent import EntityExtractionAgent, EntityMerger
from .agents.activity_extraction_agent import ActivityExtractionAgent, ActivityMerger
from .agents.product_extraction_agent import ProductExtractionAgent, ProductMerger
from .auth import token_manager

logger = logging.getLogger(__name__)


class DeepResearchOrchestrator:
    """Main orchestrator for the RegGenome deep research system."""
    
    def __init__(self, use_mock_api: bool = False):
        """Initialize the orchestrator with all agents."""
        
        # Initialize API client
        if use_mock_api or not self._has_valid_authentication():
            logger.info("Using mock API client for testing")
            self.api_client = MockRegGenomeAPIClient()
        else:
            self.api_client = RegGenomeAPIClient()
        
        # Initialize extraction agents
        self.entity_agent = EntityExtractionAgent()
        self.activity_agent = ActivityExtractionAgent()
        self.product_agent = ProductExtractionAgent()
        
        # Initialize mergers for deduplication
        self.entity_merger = EntityMerger()
        self.activity_merger = ActivityMerger()
        self.product_merger = ProductMerger()
        
        # Research state
        self.current_state: Optional[ResearchState] = None
    
    def _has_valid_authentication(self) -> bool:
        """Check if we have valid authentication credentials for the real API."""
        # Check for JWT authentication
        if config.reggenome.use_jwt_auth:
            jwt_token = token_manager.get_access_token()
            if jwt_token and not token_manager.is_token_expired():
                logger.info("Found valid JWT authentication")
                return True
            elif jwt_token and token_manager.is_token_expired():
                logger.warning("JWT token is expired")
                return False
            else:
                logger.warning("JWT authentication enabled but no token available")
        
        # Check for traditional API key
        if config.reggenome.api_key:
            logger.info("Found API key authentication")
            return True
        
        logger.warning("No valid authentication method found (JWT or API key)")
        return False
    
    async def _test_api_connectivity(self) -> bool:
        """Test if the RegGenome API is accessible."""
        try:
            async with self.api_client:
                # Try a simple request to test connectivity
                await self.api_client._make_request('GET', '/health')
                return True
        except Exception as e:
            logger.error(f"API connectivity test failed: {e}")
            return False
    
    async def run_research(
        self,
        query: str = "Identify regulated activities, entities, and products",
        save_results: bool = True,
        output_file: Optional[str] = None
    ) -> RegulatoryTaxonomy:
        """Run the complete deep research workflow."""
        
        logger.info(f"Starting deep research workflow: {query}")
        
        # Initialize research state
        self.current_state = ResearchState(query=query)
        
        # Check if using mock API and warn user
        if isinstance(self.api_client, MockRegGenomeAPIClient):
            logger.warning("🧪 Using mock API client - results will be synthetic/demo data")
            logger.warning("📡 Real RegGenome API may be unreachable or authentication may be invalid")
        
        try:
            # Step 1: Fetch documents
            await self._fetch_documents()
            
            # Step 2: Extract entities, activities, and products in parallel
            await self._extract_all_information()
            
            # Step 3: Assess document relevance
            await self._assess_document_relevance()
            
            # Step 4: Deduplicate and merge similar items
            await self._deduplicate_taxonomy()
            
            # Step 5: Generate final taxonomy
            taxonomy = self.current_state.taxonomy
            taxonomy.updated_at = datetime.utcnow()
            
            # Save results if requested
            if save_results:
                await self._save_results(taxonomy, output_file)
            
            if isinstance(self.api_client, MockRegGenomeAPIClient):
                logger.warning("⚠️  Results are from mock data - not real regulatory documents")
            
            logger.info("Deep research workflow completed successfully")
            return taxonomy
            
        except Exception as e:
            logger.error(f"Error in research workflow: {e}")
            self.current_state.errors.append(str(e))
            raise
        
        finally:
            # Clean up API client
            await self.api_client.close()
    
    async def _fetch_documents(self):
        """Fetch relevant documents from RegGenome API."""
        logger.info("Fetching documents from RegGenome API...")
        
        try:
            documents = []
            max_docs_per_initiative = 5  # Limit docs per initiative
            
            async with self.api_client:
                # First try to search for documents matching the query
                if self.current_state.query and self.current_state.query.lower() != "identify regulated activities, entities, and products":
                    logger.info(f"Searching for documents matching: {self.current_state.query}")
                    
                    # Try searching with title parameter
                    response = await self.api_client.search_documents(
                        query=self.current_state.query,
                        page_size=config.research.max_documents_to_process
                    )
                    
                    doc_list = response if isinstance(response, list) else response.get("documents", [])
                    logger.info(f"Title search returned {len(doc_list)} documents")
                    
                    for doc_data in doc_list[:config.research.max_documents_to_process]:
                        try:
                            # Extract content if needed
                            if doc_data.get("source_text") and isinstance(doc_data["source_text"], list):
                                doc_data["content"] = "\n".join([
                                    text.get("text", "") for text in doc_data["source_text"] 
                                    if isinstance(text, dict) and text.get("text")
                                ])
                            if not doc_data.get("content"):
                                doc_data["content"] = doc_data.get("title", "")
                                
                            parsed_doc = self.api_client._parse_document(doc_data)
                            documents.append(parsed_doc)
                            logger.info(f"✓ Fetched: {parsed_doc.title[:80]}...")
                        except Exception as e:
                            logger.warning(f"Failed to parse document: {e}")
                            continue
                
                # If no documents found with title search, try fetching from initiatives
                if len(documents) == 0:
                    logger.info("No documents found with title search, trying initiative-based search...")
                    
                    # Look for UCITS-related initiatives if query contains "UCITS"
                    initiatives = await self.api_client.get_legislative_initiatives()
                    relevant_initiatives = []
                    
                    if "ucits" in self.current_state.query.lower():
                        relevant_initiatives = [i for i in initiatives if "UCITS" in i.get("name", "")]
                        logger.info(f"Found {len(relevant_initiatives)} UCITS-related initiatives")
                    
                    # Use relevant initiatives or fall back to all initiatives
                    initiatives_to_use = relevant_initiatives if relevant_initiatives else initiatives[:3]
                    
                    for initiative in initiatives_to_use:
                        initiative_name = initiative.get("name", "Unknown")
                        initiative_id = initiative.get("id")
                        
                        if initiative_id:
                            logger.info(f"Fetching from initiative: {initiative_name}")
                            async for document in self.api_client.get_documents_by_legislative_initiative(
                                initiative_id, 
                                max_documents=min(5, config.research.max_documents_to_process - len(documents))
                            ):
                                documents.append(document)
                                logger.info(f"✓ Fetched: {document.title[:80]}...")
                                
                                if len(documents) >= config.research.max_documents_to_process:
                                    logger.info(f"Reached document limit ({config.research.max_documents_to_process})")
                                    break
                        
                        if len(documents) >= config.research.max_documents_to_process:
                            break
            
            self.current_state.documents = documents
            self.current_state.documents_fetched = True
            
            logger.info(f"✅ Successfully fetched {len(documents)} documents for analysis")
            
        except Exception as e:
            error_msg = f"Failed to fetch documents: {e}"
            logger.error(error_msg)
            self.current_state.errors.append(error_msg)
            raise
    
    async def _extract_all_information(self):
        """Extract entities, activities, and products from all documents."""
        logger.info("Extracting regulatory information from documents...")
        
        if not self.current_state.documents:
            raise ValueError("No documents available for extraction")
        
        # Run extractions in parallel for efficiency
        tasks = [
            self._extract_entities(),
            self._extract_activities(),
            self._extract_products()
        ]
        
        try:
            await asyncio.gather(*tasks)
            logger.info("Successfully completed all extractions")
            
        except Exception as e:
            error_msg = f"Error during extraction: {e}"
            logger.error(error_msg)
            self.current_state.errors.append(error_msg)
            raise
    
    async def _extract_entities(self):
        """Extract entities from all documents."""
        logger.info(f"🔍 Extracting entities from {len(self.current_state.documents)} documents...")
        
        try:
            # Process documents in smaller batches to show progress
            batch_size = 5
            all_entities = []
            
            for i in range(0, len(self.current_state.documents), batch_size):
                batch = self.current_state.documents[i:i + batch_size]
                logger.info(f"  Processing batch {i//batch_size + 1}/{(len(self.current_state.documents) + batch_size - 1)//batch_size}...")
                
                entities = await self.entity_agent.extract_entities_batch(batch)
                all_entities.extend(entities)
                
                logger.info(f"  ✓ Extracted {len(entities)} entities from batch")
            
            self.current_state.taxonomy.entities = all_entities
            self.current_state.entities_extracted = True
            
            logger.info(f"✅ Extracted total of {len(all_entities)} entities")
            
        except Exception as e:
            error_msg = f"Entity extraction failed: {e}"
            logger.error(error_msg)
            self.current_state.errors.append(error_msg)
    
    async def _extract_activities(self):
        """Extract activities from all documents."""
        logger.info(f"⚡ Extracting activities from {len(self.current_state.documents)} documents...")
        
        try:
            # Process documents in smaller batches to show progress
            batch_size = 5
            all_activities = []
            
            for i in range(0, len(self.current_state.documents), batch_size):
                batch = self.current_state.documents[i:i + batch_size]
                logger.info(f"  Processing batch {i//batch_size + 1}/{(len(self.current_state.documents) + batch_size - 1)//batch_size}...")
                
                activities = await self.activity_agent.extract_activities_batch(batch)
                all_activities.extend(activities)
                
                logger.info(f"  ✓ Extracted {len(activities)} activities from batch")
            
            self.current_state.taxonomy.activities = all_activities
            self.current_state.activities_extracted = True
            
            logger.info(f"✅ Extracted total of {len(all_activities)} activities")
            
        except Exception as e:
            error_msg = f"Activity extraction failed: {e}"
            logger.error(error_msg)
            self.current_state.errors.append(error_msg)
    
    async def _extract_products(self):
        """Extract products from all documents."""
        logger.info(f"📦 Extracting products from {len(self.current_state.documents)} documents...")
        
        try:
            # Process documents in smaller batches to show progress
            batch_size = 5
            all_products = []
            
            for i in range(0, len(self.current_state.documents), batch_size):
                batch = self.current_state.documents[i:i + batch_size]
                logger.info(f"  Processing batch {i//batch_size + 1}/{(len(self.current_state.documents) + batch_size - 1)//batch_size}...")
                
                products = await self.product_agent.extract_products_batch(batch)
                all_products.extend(products)
                
                logger.info(f"  ✓ Extracted {len(products)} products from batch")
            
            self.current_state.taxonomy.products = all_products
            self.current_state.products_extracted = True
            
            logger.info(f"✅ Extracted total of {len(all_products)} products")
            
        except Exception as e:
            error_msg = f"Product extraction failed: {e}"
            logger.error(error_msg)
            self.current_state.errors.append(error_msg)
    
    async def _assess_document_relevance(self):
        """Assess relevance of each document to extracted entities, activities, and products."""
        logger.info("Assessing document relevance...")
        
        try:
            relevance_assessments = []
            
            for document in self.current_state.documents:
                relevance = DocumentRelevance(document_id=document.document_id)
                
                # Assess entity relevance
                for entity in self.current_state.taxonomy.entities:
                    if document.document_id in entity.source_documents:
                        relevance.entity_relevance[entity.entity_id] = entity.confidence_score
                
                # Assess activity relevance
                for activity in self.current_state.taxonomy.activities:
                    if document.document_id in activity.source_documents:
                        relevance.activity_relevance[activity.activity_id] = activity.confidence_score
                
                # Assess product relevance
                for product in self.current_state.taxonomy.products:
                    if document.document_id in product.source_documents:
                        relevance.product_relevance[product.product_id] = product.confidence_score
                
                relevance_assessments.append(relevance)
            
            self.current_state.taxonomy.document_relevance = relevance_assessments
            self.current_state.relevance_assessed = True
            
            logger.info(f"Assessed relevance for {len(relevance_assessments)} documents")
            
        except Exception as e:
            error_msg = f"Relevance assessment failed: {e}"
            logger.error(error_msg)
            self.current_state.errors.append(error_msg)
    
    async def _deduplicate_taxonomy(self):
        """Deduplicate and merge similar entities, activities, and products."""
        logger.info("Deduplicating taxonomy...")
        
        try:
            # Merge similar entities
            if self.current_state.taxonomy.entities:
                merged_entities = self.entity_merger.merge_similar_entities(
                    self.current_state.taxonomy.entities
                )
                self.current_state.taxonomy.entities = merged_entities
                logger.info(f"Merged entities: {len(merged_entities)} final entities")
            
            # Merge similar activities
            if self.current_state.taxonomy.activities:
                merged_activities = self.activity_merger.merge_similar_activities(
                    self.current_state.taxonomy.activities
                )
                self.current_state.taxonomy.activities = merged_activities
                logger.info(f"Merged activities: {len(merged_activities)} final activities")
            
            # Merge similar products
            if self.current_state.taxonomy.products:
                merged_products = self.product_merger.merge_similar_products(
                    self.current_state.taxonomy.products
                )
                self.current_state.taxonomy.products = merged_products
                logger.info(f"Merged products: {len(merged_products)} final products")
            
            self.current_state.deduplicated = True
            
        except Exception as e:
            error_msg = f"Deduplication failed: {e}"
            logger.error(error_msg)
            self.current_state.errors.append(error_msg)
    
    async def _save_results(self, taxonomy: RegulatoryTaxonomy, output_file: Optional[str] = None):
        """Save research results to file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"regulatory_taxonomy_{timestamp}.json"
        
        try:
            # Convert taxonomy to dict for JSON serialization
            taxonomy_dict = taxonomy.model_dump()
            
            # Add metadata
            taxonomy_dict["metadata"] = {
                "query": self.current_state.query,
                "total_documents": len(self.current_state.documents),
                "total_entities": len(taxonomy.entities),
                "total_activities": len(taxonomy.activities),
                "total_products": len(taxonomy.products),
                "errors": self.current_state.errors,
                "warnings": self.current_state.warnings
            }
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(taxonomy_dict, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {output_file}")
            
        except Exception as e:
            error_msg = f"Failed to save results: {e}"
            logger.error(error_msg)
            self.current_state.warnings.append(error_msg)
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics of the research results."""
        if not self.current_state:
            return {"error": "No research has been conducted"}
        
        taxonomy = self.current_state.taxonomy
        
        # Entity statistics
        entity_stats = {}
        if taxonomy.entities:
            entity_types = {}
            for entity in taxonomy.entities:
                entity_type = entity.entity_type.value
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            entity_stats = entity_types
        
        # Activity statistics
        activity_stats = {}
        if taxonomy.activities:
            activity_types = {}
            for activity in taxonomy.activities:
                activity_type = activity.activity_type.value
                activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
            activity_stats = activity_types
        
        # Product statistics
        product_stats = {}
        if taxonomy.products:
            product_types = {}
            for product in taxonomy.products:
                product_type = product.product_type.value
                product_types[product_type] = product_types.get(product_type, 0) + 1
            product_stats = product_types
        
        return {
            "query": self.current_state.query,
            "processing_status": {
                "documents_fetched": self.current_state.documents_fetched,
                "entities_extracted": self.current_state.entities_extracted,
                "activities_extracted": self.current_state.activities_extracted,
                "products_extracted": self.current_state.products_extracted,
                "relevance_assessed": self.current_state.relevance_assessed,
                "deduplicated": self.current_state.deduplicated
            },
            "totals": {
                "documents": len(self.current_state.documents),
                "entities": len(taxonomy.entities),
                "activities": len(taxonomy.activities),
                "products": len(taxonomy.products)
            },
            "entity_breakdown": entity_stats,
            "activity_breakdown": activity_stats,
            "product_breakdown": product_stats,
            "errors": self.current_state.errors,
            "warnings": self.current_state.warnings
        }
    
    async def create_hierarchical_table(self) -> Dict[str, Any]:
        """Create a hierarchical table of all regulated items (Task 1 output)."""
        if not self.current_state or not self.current_state.deduplicated:
            raise ValueError("Research must be completed and deduplicated first")
        
        taxonomy = self.current_state.taxonomy
        
        # Create hierarchical structure
        hierarchical_table = {
            "regulated_entities": {},
            "regulated_activities": {},
            "regulated_products": {},
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "total_items": len(taxonomy.entities) + len(taxonomy.activities) + len(taxonomy.products),
                "source_documents": len(self.current_state.documents)
            }
        }
        
        # Organize entities by type
        for entity in taxonomy.entities:
            entity_type = entity.entity_type.value
            if entity_type not in hierarchical_table["regulated_entities"]:
                hierarchical_table["regulated_entities"][entity_type] = []
            
            hierarchical_table["regulated_entities"][entity_type].append({
                "id": entity.entity_id,
                "name": entity.name,
                "description": entity.description,
                "jurisdictions": entity.applicable_jurisdictions,
                "regulatory_framework": entity.regulatory_framework,
                "source_documents": entity.source_documents,
                "confidence_score": entity.confidence_score
            })
        
        # Organize activities by type
        for activity in taxonomy.activities:
            activity_type = activity.activity_type.value
            if activity_type not in hierarchical_table["regulated_activities"]:
                hierarchical_table["regulated_activities"][activity_type] = []
            
            hierarchical_table["regulated_activities"][activity_type].append({
                "id": activity.activity_id,
                "name": activity.name,
                "description": activity.description,
                "applicable_entities": activity.applicable_entities,
                "required_licenses": activity.required_licenses,
                "regulatory_requirements": activity.regulatory_requirements,
                "source_documents": activity.source_documents,
                "confidence_score": activity.confidence_score
            })
        
        # Organize products by type
        for product in taxonomy.products:
            product_type = product.product_type.value
            if product_type not in hierarchical_table["regulated_products"]:
                hierarchical_table["regulated_products"][product_type] = []
            
            hierarchical_table["regulated_products"][product_type].append({
                "id": product.product_id,
                "name": product.name,
                "description": product.description,
                "applicable_entities": product.applicable_entities,
                "regulatory_classification": product.regulatory_classification,
                "compliance_requirements": product.compliance_requirements,
                "source_documents": product.source_documents,
                "confidence_score": product.confidence_score
            })
        
        return hierarchical_table


# Convenience function for running the complete workflow
async def run_deep_research(
    query: str = "Identify regulated activities, entities, and products",
    use_mock_api: bool = False,
    save_results: bool = True,
    output_file: Optional[str] = None
) -> RegulatoryTaxonomy:
    """Run the complete deep research workflow."""
    
    orchestrator = DeepResearchOrchestrator(use_mock_api=use_mock_api)
    return await orchestrator.run_research(
        query=query,
        save_results=save_results,
        output_file=output_file
    ) 