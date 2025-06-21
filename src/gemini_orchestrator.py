"""
Gemini-Enhanced Deep Research Orchestrator

This module integrates Google Gemini 2.5 Pro into the RegGenome research system
for enhanced accuracy in entity extraction, document analysis, and definition finding.
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from src.config import Config
from src.models import Document, ResearchResult
from src.api_client import RegGenomeAPIClient
from src.gemini_client import GeminiClient, create_gemini_client, GeminiEnhancedExtractor
from src.agents.gemini_entity_extraction_agent import GeminiEntityExtractionAgent
from src.deduplication_agent import DeduplicationAgent

class GeminiDeepResearchOrchestrator:
    """Enhanced orchestrator using Gemini 2.5 Pro for improved accuracy"""
    
    def __init__(self, config: Config, gemini_client: Optional[GeminiClient] = None):
        self.config = config
        
        # Initialize Gemini client
        if gemini_client:
            self.gemini_client = gemini_client
        else:
            self.gemini_client = create_gemini_client()
            
        if not self.gemini_client:
            raise ValueError("Gemini client is required but could not be initialized")
        
        # Initialize agents with Gemini enhancement
        self.gemini_entity_agent = GeminiEntityExtractionAgent(self.gemini_client)
        self.deduplication_agent = DeduplicationAgent()
        self.gemini_extractor = GeminiEnhancedExtractor(self.gemini_client)
        
        print("🤖 Initialized Gemini-Enhanced Deep Research Orchestrator")
    
    async def research(self, query: str) -> ResearchResult:
        """Execute enhanced research using Gemini 2.5 Pro"""
        
        print(f"\n🚀 Starting Gemini-Enhanced Research")
        print(f"Query: {query}")
        print(f"Model: Gemini 2.5 Pro")
        print("-" * 60)
        
        start_time = datetime.now()
        
        # Step 1: Fetch documents
        print("📥 Fetching documents from RegGenome API...")
        documents = await self._fetch_documents()
        print(f"   Retrieved {len(documents)} documents")
        
        # Step 2: Enhanced entity extraction with Gemini
        print("\n🤖 Running Gemini-enhanced entity extraction...")
        extraction_results = await self.gemini_entity_agent.extract_entities(documents)
        
        raw_entities = extraction_results["entities"]
        raw_activities = extraction_results["activities"] 
        raw_products = extraction_results["products"]
        
        print(f"   Raw extractions - Entities: {len(raw_entities)}, Activities: {len(raw_activities)}, Products: {len(raw_products)}")
        
        # Step 3: Deduplication and refinement
        print("\n🔄 Deduplicating and refining results...")
        
        # Deduplicate entities
        unique_entities = await self.deduplication_agent.deduplicate_entities(raw_entities)
        unique_activities = await self.deduplication_agent.deduplicate_activities(raw_activities)
        unique_products = await self.deduplication_agent.deduplicate_products(raw_products)
        
        print(f"   After deduplication - Entities: {len(unique_entities)}, Activities: {len(unique_activities)}, Products: {len(unique_products)}")
        
        # Step 4: Enhance with Gemini-powered definition finding
        print("\n📖 Finding definitions with Gemini...")
        await self._enhance_with_definitions(unique_entities + unique_activities + unique_products, documents)
        
        # Step 5: Generate comprehensive result
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result = ResearchResult(
            entities=unique_entities,
            activities=unique_activities,
            products=unique_products,
            total_documents_processed=len(documents),
            extraction_metadata={
                "method": "gemini-2.5-pro-enhanced",
                "processing_time_seconds": processing_time,
                "gemini_model": self.gemini_client.config.model_name,
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "statistics": {
                    "total_entities_extracted": len(raw_entities),
                    "total_activities_extracted": len(raw_activities), 
                    "total_products_extracted": len(raw_products),
                    "unique_entities": len(unique_entities),
                    "unique_activities": len(unique_activities),
                    "unique_products": len(unique_products),
                    "deduplication_ratio": 1 - (len(unique_entities) + len(unique_activities) + len(unique_products)) / max(1, len(raw_entities) + len(raw_activities) + len(raw_products))
                }
            }
        )
        
        print(f"\n✅ Gemini-enhanced research complete!")
        print(f"   Processing time: {processing_time:.1f} seconds")
        print(f"   Total unique items: {len(unique_entities) + len(unique_activities) + len(unique_products)}")
        
        return result
    
    async def _fetch_documents(self) -> List[Document]:
        """Fetch documents from RegGenome API"""
        async with RegGenomeAPIClient(self.config) as client:
            # Get initiative names
            initiative_names = list(self.config.initiative_filters.values())
            
            # Fetch documents for all initiatives
            all_documents = []
            for initiative in initiative_names:
                docs = await client.search_documents_by_text_and_filter(
                    text_query="",
                    initiative_filter=initiative,
                    max_pages=self.config.max_pages_per_query
                )
                all_documents.extend(docs)
            
            return all_documents
    
    async def _enhance_with_definitions(self, items: List, documents: List[Document]):
        """Enhance items with Gemini-powered definition finding"""
        
        definition_tasks = []
        
        # Create tasks for finding definitions of top items
        top_items = sorted(items, key=lambda x: x.confidence, reverse=True)[:20]
        
        for item in top_items:
            task = self.gemini_extractor.find_entity_definitions(documents, item.name)
            definition_tasks.append((item, task))
        
        print(f"   Searching definitions for {len(definition_tasks)} top items...")
        
        # Execute definition searches
        for item, task in definition_tasks:
            try:
                definitions = await task
                if definitions:
                    # Store the best definition in the item
                    best_def = definitions[0]
                    item.description = f"{item.description} | Definition: {best_def.get('definition_text', '')[:200]}..."
                    
            except Exception as e:
                logging.error(f"Error finding definition for {item.name}: {e}")
    
    def generate_hierarchical_table(self, result: ResearchResult) -> Dict[str, Any]:
        """Generate hierarchical table with Gemini enhancement metadata"""
        
        # Use the existing logic but add Gemini metadata
        from src.deep_research_orchestrator import DeepResearchOrchestrator
        base_orchestrator = DeepResearchOrchestrator(self.config)
        
        table = base_orchestrator.generate_hierarchical_table(result)
        
        # Add Gemini enhancement information
        table["enhancement_info"] = {
            "ai_model": "Google Gemini 2.5 Pro",
            "enhancement_features": [
                "Advanced financial context understanding",
                "Improved entity classification accuracy", 
                "Enhanced definition extraction",
                "Better relationship inference"
            ],
            "processing_method": "gemini-enhanced-extraction"
        }
        
        return table

class GeminiUnifiedInterface:
    """Unified interface with Gemini enhancement"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize Gemini client
        self.gemini_client = create_gemini_client()
        if not self.gemini_client:
            raise ValueError("Gemini API key required for enhanced processing")
        
        # Initialize Gemini-enhanced orchestrator
        self.orchestrator = GeminiDeepResearchOrchestrator(config, self.gemini_client)
        
        # Import other agents for Tasks 2 & 3
        from src.agents.document_relevance_predictor import DocumentRelevancePredictor
        from src.agents.definition_extractor import DefinitionExtractor
        from src.deliverable_formatter import DeliverableFormatter
        
        self.relevance_predictor = DocumentRelevancePredictor()
        self.definition_extractor = DefinitionExtractor()
        self.deliverable_formatter = DeliverableFormatter()
        
        print("🤖 Initialized Gemini-Enhanced Unified Interface")
    
    async def run_all_tasks_with_gemini(self, query: str) -> Dict[str, Any]:
        """Run all tasks with Gemini enhancement"""
        
        print(f"\n{'='*80}")
        print("🤖 GEMINI-ENHANCED REGULATORY RESEARCH SYSTEM")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"AI Model: Google Gemini 2.5 Pro")
        print(f"{'='*80}\n")
        
        # Task 1: Extract entities with Gemini enhancement
        print("📋 TASK 1: Gemini-Enhanced Entity Extraction...")
        print("-" * 40)
        task1_result = await self.orchestrator.research(query)
        hierarchical_table = self.orchestrator.generate_hierarchical_table(task1_result)
        
        print(f"✅ Task 1 Complete with Gemini Enhancement:")
        print(f"   - Entities: {len(task1_result.entities)}")
        print(f"   - Activities: {len(task1_result.activities)}")
        print(f"   - Products: {len(task1_result.products)}")
        
        # Tasks 2 & 3: Use existing implementation (could be enhanced with Gemini later)
        # Get all documents for tasks 2 and 3
        documents = await self._fetch_all_documents()
        
        # Task 2: Predict document relevance
        print(f"\n📊 TASK 2: Document Relevance Prediction...")
        print("-" * 40)
        task2_result = self.relevance_predictor.predict_relevance(
            documents,
            task1_result.entities,
            task1_result.activities,
            task1_result.products
        )
        
        print(f"✅ Task 2 Complete:")
        print(f"   - Relevant documents: {len(task2_result['document_relevance'])}")
        print(f"   - Coverage: {task2_result['summary']['relevance_percentage']}%")
        
        # Task 3: Extract definitions
        print(f"\n📚 TASK 3: Definition Extraction...")
        print("-" * 40)
        task3_result = self.definition_extractor.extract_definitions(
            documents,
            task1_result.entities,
            task1_result.activities,
            task1_result.products
        )
        
        print(f"✅ Task 3 Complete:")
        print(f"   - Definitions found: {task3_result['summary']['total_definitions_found']}")
        print(f"   - Item coverage: {task3_result['summary']['coverage_percentage']}%")
        
        # Compile comprehensive results
        comprehensive_results = {
            "query": query,
            "execution_timestamp": datetime.now().isoformat(),
            "ai_enhancement": {
                "model": "Google Gemini 2.5 Pro",
                "enhanced_tasks": ["Task 1: Entity Extraction"],
                "enhancement_benefits": [
                    "Improved financial context understanding",
                    "Better entity classification accuracy",
                    "Enhanced semantic analysis"
                ]
            },
            "task1_hierarchical_table": hierarchical_table,
            "task2_document_relevance": task2_result,
            "task3_definitions": task3_result,
            "overall_summary": self._generate_overall_summary(
                task1_result, task2_result, task3_result
            )
        }
        
        return comprehensive_results
    
    async def _fetch_all_documents(self):
        """Fetch all documents for analysis"""
        from src.api_client import RegGenomeAPIClient
        
        async with RegGenomeAPIClient(self.config) as client:
            initiative_names = list(self.config.initiative_filters.values())
            documents = await client.fetch_all_documents_for_initiatives(initiative_names)
            return documents
    
    def _generate_overall_summary(self, task1_result, task2_result, task3_result) -> Dict[str, Any]:
        """Generate overall summary with Gemini enhancement info"""
        return {
            "total_items_extracted": len(task1_result.entities) + len(task1_result.activities) + len(task1_result.products),
            "documents_processed": task1_result.total_documents_processed,
            "relevant_documents_identified": len(task2_result["document_relevance"]),
            "definitions_found": task3_result["summary"]["total_definitions_found"],
            "ai_enhancement": "Google Gemini 2.5 Pro",
            "extraction_method": "gemini-enhanced",
            "overall_coverage": {
                "items_with_definitions": task3_result["summary"]["items_with_definitions"],
                "definition_coverage_percentage": task3_result["summary"]["coverage_percentage"],
                "document_relevance_percentage": task2_result["summary"]["relevance_percentage"]
            }
        }