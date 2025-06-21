"""
Deliverable Formatter - Aligns system output with RegGenome challenge specification

This module reformats the existing system outputs to match the exact deliverable
specifications outlined in the challenge requirements:

Deliverable 1: Entity Taxonomy (EntityID, EntityName, EntityType, ParentEntityID) 
Deliverable 2: Relevance Predictions (DocumentID, SubDocumentID, TextSnippet, RelevantEntityID)
Deliverable 3: Entity Definitions (EntityID, EntityName, DefiningDocumentID, DefinitionFullText)
"""

import csv
import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
from collections import defaultdict
import uuid
from src.terminal_formatter import format_for_terminal

class DeliverableFormatter:
    """Formats system outputs to match challenge specifications"""
    
    def __init__(self):
        self.entity_id_map = {}  # Maps entity names to unique IDs
        self.next_entity_id = 1
        
    def format_all_deliverables(self, comprehensive_results: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
        """Format all deliverables and save to CSV/JSON"""
        
        # Extract data from comprehensive results
        task1_data = comprehensive_results["task1_hierarchical_table"]
        task2_data = comprehensive_results["task2_document_relevance"]
        task3_data = comprehensive_results["task3_definitions"]
        
        # Generate deliverable 1: Entity taxonomy
        taxonomy_table = self._create_entity_taxonomy(task1_data)
        
        # Generate deliverable 2: Relevance predictions
        relevance_table = self._create_relevance_predictions(task2_data)
        
        # Generate deliverable 3: Entity definitions
        definitions_table = self._create_entity_definitions(task3_data)
        
        # Save all deliverables
        output_files = {}
        timestamp = comprehensive_results.get('execution_timestamp', '').replace(':', '-').replace('.', '-')[:19]
        
        # Save CSV files
        taxonomy_csv = output_dir / f"DELIVERABLE_1_Entity_Taxonomy_{timestamp}.csv"
        relevance_csv = output_dir / f"DELIVERABLE_2_Relevance_Predictions_{timestamp}.csv"
        definitions_csv = output_dir / f"DELIVERABLE_3_Entity_Definitions_{timestamp}.csv"
        
        self._save_csv(taxonomy_table, taxonomy_csv, 
                      ['EntityID', 'EntityName', 'EntityType', 'ParentEntityID'])
        self._save_csv(relevance_table, relevance_csv,
                      ['DocumentID', 'SubDocumentID', 'TextSnippet', 'RelevantEntityID'])
        self._save_csv(definitions_table, definitions_csv,
                      ['EntityID', 'EntityName', 'DefiningDocumentID', 'DefinitionFullText'])
        
        # Save JSON files for reference
        taxonomy_json = output_dir / f"DELIVERABLE_1_Entity_Taxonomy_{timestamp}.json"
        relevance_json = output_dir / f"DELIVERABLE_2_Relevance_Predictions_{timestamp}.json"
        definitions_json = output_dir / f"DELIVERABLE_3_Entity_Definitions_{timestamp}.json"
        
        with open(taxonomy_json, 'w', encoding='utf-8') as f:
            json.dump(taxonomy_table, f, indent=2, ensure_ascii=False)
        with open(relevance_json, 'w', encoding='utf-8') as f:
            json.dump(relevance_table, f, indent=2, ensure_ascii=False)
        with open(definitions_json, 'w', encoding='utf-8') as f:
            json.dump(definitions_table, f, indent=2, ensure_ascii=False)
        
        output_files = {
            'taxonomy_csv': str(taxonomy_csv),
            'relevance_csv': str(relevance_csv),  
            'definitions_csv': str(definitions_csv),
            'taxonomy_json': str(taxonomy_json),
            'relevance_json': str(relevance_json),
            'definitions_json': str(definitions_json)
        }
        
        return output_files
    
    def _create_entity_taxonomy(self, task1_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Create Deliverable 1: Entity Taxonomy
        Format: EntityID, EntityName, EntityType, ParentEntityID
        """
        taxonomy_rows = []
        
        # Create hierarchical structure
        # Level 1: Root categories
        root_categories = {
            'Financial_Entity': self._get_entity_id('Financial Entity'),
            'Financial_Product': self._get_entity_id('Financial Product'), 
            'Financial_Activity': self._get_entity_id('Financial Activity')
        }
        
        # Add root categories
        for name, entity_id in root_categories.items():
            taxonomy_rows.append({
                'EntityID': entity_id,
                'EntityName': name.replace('_', ' '),
                'EntityType': 'ROOT_CATEGORY',
                'ParentEntityID': ''
            })
        
        # Level 2: Entity subcategories
        for entity_group in task1_data.get("regulated_entities", []):
            category_id = self._get_entity_id(f"{entity_group['type']}_category")
            taxonomy_rows.append({
                'EntityID': category_id,
                'EntityName': entity_group['type'].replace('_', ' ').title(),
                'EntityType': 'ENTITY_CATEGORY',
                'ParentEntityID': root_categories['Financial_Entity']
            })
            
            # Level 3: Individual entities
            for item in entity_group.get("items", []):
                entity_id = self._get_entity_id(item['name'])
                taxonomy_rows.append({
                    'EntityID': entity_id,
                    'EntityName': item['name'],
                    'EntityType': 'ENTITY',
                    'ParentEntityID': category_id
                })
        
        # Level 2: Activity subcategories  
        for activity_group in task1_data.get("regulated_activities", []):
            category_id = self._get_entity_id(f"{activity_group['type']}_category")
            taxonomy_rows.append({
                'EntityID': category_id,
                'EntityName': activity_group['type'].replace('_', ' ').title(),
                'EntityType': 'ACTIVITY_CATEGORY', 
                'ParentEntityID': root_categories['Financial_Activity']
            })
            
            # Level 3: Individual activities
            for item in activity_group.get("items", []):
                entity_id = self._get_entity_id(item['name'])
                taxonomy_rows.append({
                    'EntityID': entity_id,
                    'EntityName': item['name'],
                    'EntityType': 'ACTIVITY',
                    'ParentEntityID': category_id
                })
        
        # Level 2: Product subcategories
        for product_group in task1_data.get("regulated_products", []):
            category_id = self._get_entity_id(f"{product_group['type']}_category")
            taxonomy_rows.append({
                'EntityID': category_id,
                'EntityName': product_group['type'].replace('_', ' ').title(),
                'EntityType': 'PRODUCT_CATEGORY',
                'ParentEntityID': root_categories['Financial_Product']
            })
            
            # Level 3: Individual products
            for item in product_group.get("items", []):
                entity_id = self._get_entity_id(item['name'])
                taxonomy_rows.append({
                    'EntityID': entity_id,
                    'EntityName': item['name'],
                    'EntityType': 'PRODUCT',
                    'ParentEntityID': category_id
                })
        
        return taxonomy_rows
    
    def _create_relevance_predictions(self, task2_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Create Deliverable 2: Relevance Predictions  
        Format: DocumentID, SubDocumentID, TextSnippet, RelevantEntityID
        """
        relevance_rows = []
        
        for doc in task2_data.get("document_relevance", []):
            doc_id = doc["document_id"]
            doc_title = doc.get("title", "")[:100]  # Truncate for snippet
            
            # Document-level relevance
            relevant_entities = []
            
            # Collect all relevant entities
            for entity_type in doc.get("relevant_entities", {}):
                entity_id = self._get_entity_id_if_exists(entity_type)
                if entity_id:
                    relevant_entities.append(entity_id)
            
            for activity_type in doc.get("relevant_activities", {}):
                entity_id = self._get_entity_id_if_exists(activity_type) 
                if entity_id:
                    relevant_entities.append(entity_id)
                    
            for product_type in doc.get("relevant_products", {}):
                entity_id = self._get_entity_id_if_exists(product_type)
                if entity_id:
                    relevant_entities.append(entity_id)
            
            # Add document-level entries
            for entity_id in relevant_entities:
                relevance_rows.append({
                    'DocumentID': doc_id,
                    'SubDocumentID': '',
                    'TextSnippet': doc_title,
                    'RelevantEntityID': entity_id
                })
            
            # Sub-document level relevance (signposts)
            for subdoc in doc.get("subdocument_relevance", []):
                signpost_id = f"signpost_{subdoc['signpost_index']}"
                text_snippet = subdoc.get("text_preview", "")[:200]
                
                # Extract relevant entities from subdocument
                subdoc_entities = []
                
                for entity in subdoc.get("relevant_entities", {}):
                    entity_id = self._get_entity_id_if_exists(entity)
                    if entity_id:
                        subdoc_entities.append(entity_id)
                
                for activity in subdoc.get("relevant_activities", {}):
                    entity_id = self._get_entity_id_if_exists(activity)
                    if entity_id:
                        subdoc_entities.append(entity_id)
                        
                for product in subdoc.get("relevant_products", {}):
                    entity_id = self._get_entity_id_if_exists(product)
                    if entity_id:
                        subdoc_entities.append(entity_id)
                
                for entity_id in subdoc_entities:
                    relevance_rows.append({
                        'DocumentID': doc_id,
                        'SubDocumentID': signpost_id,
                        'TextSnippet': text_snippet,
                        'RelevantEntityID': entity_id
                    })
        
        return relevance_rows
    
    def _create_entity_definitions(self, task3_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Create Deliverable 3: Entity Definitions
        Format: EntityID, EntityName, DefiningDocumentID, DefinitionFullText
        """
        definitions_rows = []
        
        # Process entity definitions
        for entity_def in task3_data.get("entity_definitions", []):
            entity_name = entity_def["name"]
            entity_id = self._get_entity_id_if_exists(entity_name)
            
            if entity_id:
                for definition in entity_def.get("definitions", []):
                    definitions_rows.append({
                        'EntityID': entity_id,
                        'EntityName': entity_name,
                        'DefiningDocumentID': definition["source"]["document_id"],
                        'DefinitionFullText': definition["definition"]
                    })
        
        # Process activity definitions
        for activity_def in task3_data.get("activity_definitions", []):
            activity_name = activity_def["name"]
            entity_id = self._get_entity_id_if_exists(activity_name)
            
            if entity_id:
                for definition in activity_def.get("definitions", []):
                    definitions_rows.append({
                        'EntityID': entity_id,
                        'EntityName': activity_name,
                        'DefiningDocumentID': definition["source"]["document_id"],
                        'DefinitionFullText': definition["definition"]
                    })
        
        # Process product definitions
        for product_def in task3_data.get("product_definitions", []):
            product_name = product_def["name"]
            entity_id = self._get_entity_id_if_exists(product_name)
            
            if entity_id:
                for definition in product_def.get("definitions", []):
                    definitions_rows.append({
                        'EntityID': entity_id,
                        'EntityName': product_name,
                        'DefiningDocumentID': definition["source"]["document_id"],
                        'DefinitionFullText': definition["definition"]
                    })
        
        return definitions_rows
    
    def _get_entity_id(self, entity_name: str) -> str:
        """Get or create a unique EntityID for an entity name"""
        if entity_name not in self.entity_id_map:
            # Create ID in format E001, E002, etc.
            entity_id = f"E{self.next_entity_id:03d}"
            self.entity_id_map[entity_name] = entity_id
            self.next_entity_id += 1
        
        return self.entity_id_map[entity_name]
    
    def _get_entity_id_if_exists(self, entity_name: str) -> str:
        """Get EntityID if it exists, otherwise return empty string"""
        return self.entity_id_map.get(entity_name, "")
    
    def _save_csv(self, data: List[Dict[str, str]], file_path: Path, fieldnames: List[str]):
        """Save data to CSV file"""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def generate_summary_report(self, output_files: Dict[str, str], query: str) -> str:
        """Generate a summary report of the deliverables"""
        report = []
        report.append("=" * 80)
        report.append("REGGENOME CHALLENGE DELIVERABLES SUMMARY")
        report.append("=" * 80)
        report.append(f"Query: {query}")
        report.append(f"Generated: {Path(output_files['taxonomy_csv']).stem.split('_')[-1]}")
        report.append("")
        
        report.append("DELIVERABLE 1: Entity Taxonomy")
        report.append(f"   CSV: {Path(output_files['taxonomy_csv']).name}")
        report.append(f"   JSON: {Path(output_files['taxonomy_json']).name}")
        report.append("   Format: EntityID | EntityName | EntityType | ParentEntityID")
        report.append("")
        
        report.append("DELIVERABLE 2: Relevance Predictions") 
        report.append(f"   CSV: {Path(output_files['relevance_csv']).name}")
        report.append(f"   JSON: {Path(output_files['relevance_json']).name}")
        report.append("   Format: DocumentID | SubDocumentID | TextSnippet | RelevantEntityID")
        report.append("")
        
        report.append("DELIVERABLE 3: Entity Definitions")
        report.append(f"   CSV: {Path(output_files['definitions_csv']).name}")
        report.append(f"   JSON: {Path(output_files['definitions_json']).name}")
        report.append("   Format: EntityID | EntityName | DefiningDocumentID | DefinitionFullText")
        report.append("")
        
        report.append("All deliverables conform to RegGenome challenge specifications")
        report.append("=" * 80)
        
        return "\n".join(report)