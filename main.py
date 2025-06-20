#!/usr/bin/env python3
"""
RegGenome Entity Mapper - Main Entry Point
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import json
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from api.client import RegGenomeClient
from extractors.entity_extractor import EntityExtractor
from extractors.financial_entities import FinancialEntityExtractor
from hierarchical.hierarchy_builder import HierarchyBuilder
from classifiers.relevance_predictor import RelevancePredictor
from definitions.definition_extractor import DefinitionExtractor


class EntityMapper:
    """Main class for RegGenome entity mapping solution"""
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        
        self.api_key = api_key or os.getenv("REGGENOME_API_KEY")
        if not self.api_key:
            raise ValueError("RegGenome API key not provided")
        
        # Initialize components
        self.api_client = None
        self.entity_extractor = EntityExtractor()
        self.financial_extractor = FinancialEntityExtractor()
        self.hierarchy_builder = HierarchyBuilder()
        self.relevance_predictor = RelevancePredictor()
        self.definition_extractor = DefinitionExtractor()
        
        # Storage
        self.documents = []
        self.entities = []
        self.definitions = []
        self.hierarchy = None
        self.relevance_predictions = {}
        
        # Output directory
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./outputs"))
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("EntityMapper initialized")
    
    async def process_initiatives(
        self,
        initiative_names: List[str],
        limit: Optional[int] = None
    ) -> Dict:
        """Process documents for specified initiatives"""
        
        logger.info(f"Processing initiatives: {initiative_names}")
        
        async with RegGenomeClient(self.api_key) as client:
            self.api_client = client
            
            # Fetch documents
            logger.info("Fetching documents from RegGenome API...")
            documents = await client.fetch_all_documents_for_initiatives(initiative_names)
            
            if limit:
                documents = documents[:limit]
            
            self.documents = documents
            logger.info(f"Fetched {len(documents)} documents")
            
            # Process documents
            results = await self._process_documents(documents)
            
            return results
    
    async def _process_documents(self, documents: List[Dict]) -> Dict:
        """Process documents through the pipeline"""
        
        # 1. Extract entities
        logger.info("Extracting entities...")
        all_entities = []
        financial_entities = []
        
        for doc in documents:
            # General entity extraction
            doc_entities = self.entity_extractor.extract_from_document(doc)
            all_entities.extend(doc_entities)
            
            # Financial entity extraction
            doc_text = self._get_document_text(doc)
            fin_entities = self.financial_extractor.extract_financial_entities(doc_text)
            financial_entities.extend(fin_entities)
        
        # Combine and deduplicate
        unique_entities = self._merge_entity_types(all_entities, financial_entities)
        self.entities = unique_entities
        logger.info(f"Extracted {len(unique_entities)} unique entities")
        
        # 2. Build hierarchy
        logger.info("Building entity hierarchy...")
        self.hierarchy = self.hierarchy_builder.build_entity_hierarchy(unique_entities)
        
        # 3. Extract definitions
        logger.info("Extracting definitions...")
        all_definitions = []
        
        for doc in documents:
            doc_id = doc.get("document_id")
            
            # Extract from each section
            if "source_text" in doc:
                for section in doc["source_text"]:
                    section_text = section.get("text", "")
                    section_id = section.get("section_id", "unknown")
                    
                    if section_text:
                        definitions = self.definition_extractor.extract_definitions(
                            section_text, doc_id, section_id
                        )
                        all_definitions.extend(definitions)
        
        self.definitions = all_definitions
        logger.info(f"Extracted {len(all_definitions)} definitions")
        
        # 4. Predict relevance
        logger.info("Predicting entity relevance...")
        entity_names = [e["name"] for e in unique_entities]
        self.relevance_predictions = self.relevance_predictor.predict_relevance(
            documents, entity_names
        )
        
        # 5. Link definitions to entities
        logger.info("Linking definitions to entities...")
        entity_definitions = self.definition_extractor.link_definitions_to_entities(
            entity_names, all_definitions
        )
        
        # Compile results
        results = {
            "documents_processed": len(documents),
            "entities_extracted": len(unique_entities),
            "definitions_found": len(all_definitions),
            "hierarchy_nodes": self.hierarchy.number_of_nodes(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Generate outputs
        self._generate_outputs(entity_definitions)
        
        return results
    
    def _get_document_text(self, document: Dict) -> str:
        """Extract all text from document"""
        text_parts = []
        
        if "title" in document:
            text_parts.append(document["title"])
        
        if "source_text" in document:
            for section in document["source_text"]:
                if "text" in section:
                    text_parts.append(section["text"])
        
        return "\n\n".join(text_parts)
    
    def _merge_entity_types(self, general_entities, financial_entities) -> List[Dict]:
        """Merge different types of entities"""
        
        entity_dict = {}
        
        # Add general entities
        for entity in general_entities:
            key = (entity.text.lower(), entity.entity_type)
            if key not in entity_dict:
                entity_dict[key] = {
                    "name": entity.text,
                    "entity_type": entity.entity_type,
                    "confidence": entity.confidence,
                    "occurrences": 1
                }
            else:
                entity_dict[key]["occurrences"] += 1
                entity_dict[key]["confidence"] = max(
                    entity_dict[key]["confidence"],
                    entity.confidence
                )
        
        # Add financial entities
        for entity in financial_entities:
            key = (entity.name.lower(), entity.entity_type)
            if key not in entity_dict:
                entity_dict[key] = {
                    "name": entity.name,
                    "entity_type": entity.entity_type,
                    "category": entity.category,
                    "subcategory": entity.subcategory,
                    "confidence": entity.confidence,
                    "occurrences": 1
                }
            else:
                entity_dict[key]["occurrences"] += 1
                if "category" not in entity_dict[key]:
                    entity_dict[key]["category"] = entity.category
                    entity_dict[key]["subcategory"] = entity.subcategory
        
        # Convert to list and filter by confidence
        threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        unique_entities = [
            entity for entity in entity_dict.values()
            if entity["confidence"] >= threshold
        ]
        
        return unique_entities
    
    def _generate_outputs(self, entity_definitions: Dict):
        """Generate all output files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_subdir = self.output_dir / timestamp
        output_subdir.mkdir(exist_ok=True)
        
        # 1. Entity table
        logger.info("Generating entity table...")
        entity_df = self.hierarchy_builder.get_entity_hierarchy_table()
        entity_df.to_csv(output_subdir / "entities.csv", index=False)
        
        # 2. Relevance predictions
        logger.info("Exporting relevance predictions...")
        self.relevance_predictor.export_predictions(
            self.relevance_predictions,
            str(output_subdir / "relevance.json")
        )
        
        # 3. Definitions
        logger.info("Exporting definitions...")
        self.definition_extractor.export_definitions(
            self.definitions,
            str(output_subdir / "definitions.json")
        )
        
        # 4. Entity-definition links
        logger.info("Exporting entity-definition links...")
        with open(output_subdir / "entity_definitions.json", 'w') as f:
            json.dump(
                {k: [d.__dict__ for d in v] for k, v in entity_definitions.items()},
                f, indent=2, default=str
            )
        
        # 5. Hierarchy visualization
        logger.info("Creating hierarchy visualization...")
        self.hierarchy_builder.visualize_hierarchy(
            str(output_subdir / "hierarchy.png")
        )
        
        # 6. Summary report
        logger.info("Generating summary report...")
        self._generate_summary_report(output_subdir)
        
        logger.info(f"All outputs saved to {output_subdir}")
    
    def _generate_summary_report(self, output_dir: Path):
        """Generate summary report"""
        
        report = {
            "summary": {
                "documents_processed": len(self.documents),
                "entities_extracted": len(self.entities),
                "definitions_found": len(self.definitions),
                "hierarchy_nodes": self.hierarchy.number_of_nodes() if self.hierarchy else 0,
                "timestamp": datetime.now().isoformat()
            },
            "entity_breakdown": self._get_entity_breakdown(),
            "top_entities": self._get_top_entities(20),
            "coverage": self._calculate_coverage()
        }
        
        with open(output_dir / "summary_report.json", 'w') as f:
            json.dump(report, f, indent=2)
    
    def _get_entity_breakdown(self) -> Dict:
        """Get breakdown by entity type"""
        breakdown = {}
        for entity in self.entities:
            entity_type = entity.get("entity_type", "UNKNOWN")
            if entity_type not in breakdown:
                breakdown[entity_type] = 0
            breakdown[entity_type] += 1
        return breakdown
    
    def _get_top_entities(self, n: int) -> List[Dict]:
        """Get top N entities by occurrence"""
        sorted_entities = sorted(
            self.entities,
            key=lambda e: e.get("occurrences", 0),
            reverse=True
        )
        return [
            {
                "name": e["name"],
                "type": e["entity_type"],
                "occurrences": e.get("occurrences", 0),
                "confidence": e["confidence"]
            }
            for e in sorted_entities[:n]
        ]
    
    def _calculate_coverage(self) -> Dict:
        """Calculate coverage statistics"""
        
        docs_with_entities = 0
        docs_with_definitions = 0
        
        for doc in self.documents:
            doc_id = doc.get("document_id")
            
            if doc_id in self.relevance_predictions:
                if self.relevance_predictions[doc_id]["document_level"]:
                    docs_with_entities += 1
            
            if any(d.document_id == doc_id for d in self.definitions):
                docs_with_definitions += 1
        
        total_docs = len(self.documents)
        
        return {
            "documents_with_entities": docs_with_entities,
            "documents_with_definitions": docs_with_definitions,
            "entity_coverage": docs_with_entities / total_docs if total_docs > 0 else 0,
            "definition_coverage": docs_with_definitions / total_docs if total_docs > 0 else 0
        }


async def main():
    """Main entry point"""
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    logger.add("logs/entity_mapper_{time}.log", rotation="500 MB", level="DEBUG")
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="RegGenome Entity Mapper")
    parser.add_argument(
        "--initiatives",
        nargs="+",
        default=[
            "US - Investment Advisers Act (1940)",
            "US - Investment Company Act, 1940",
            "EU - UCITS Directives",
            "UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations, 2011 - 2016"
        ],
        help="Initiative names to process"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="RegGenome API key"
    )
    
    args = parser.parse_args()
    
    # Run processing
    try:
        mapper = EntityMapper(api_key=args.api_key)
        results = await mapper.process_initiatives(
            args.initiatives,
            limit=args.limit
        )
        
        logger.info("Processing complete!")
        logger.info(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())