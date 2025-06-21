import asyncio
from typing import Dict, Any, Optional
import json
import re
from datetime import datetime
from pathlib import Path

from src.config import Config
from src.deep_research_orchestrator import DeepResearchOrchestrator
from src.agents.document_relevance_predictor import DocumentRelevancePredictor
from src.agents.definition_extractor import DefinitionExtractor
from src.deliverable_formatter import DeliverableFormatter
from src.terminal_formatter import format_for_terminal

class UnifiedResearchInterface:
    """Unified interface for all three research tasks"""
    
    def __init__(self, config: Config):
        self.config = config
        self.orchestrator = DeepResearchOrchestrator(config)
        self.relevance_predictor = DocumentRelevancePredictor()
        self.definition_extractor = DefinitionExtractor()
        self.deliverable_formatter = DeliverableFormatter()
        
    async def run_all_tasks(self, query: str) -> Dict[str, Any]:
        """Run all three tasks and return comprehensive results"""
        
        print(f"\n{'='*80}")
        print("COMPREHENSIVE REGULATORY RESEARCH SYSTEM")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}\n")
        
        # Task 1: Extract entities, activities, and products
        print(format_for_terminal("## TASK 1: Extracting Regulated Items..."))
        print("-" * 40)
        task1_result = await self.orchestrator.research(query)
        hierarchical_table = self.orchestrator.generate_hierarchical_table(task1_result)
        
        print(format_for_terminal("**Task 1 Complete:**"))
        print(f"   - Entities: {len(task1_result.entities)}")
        print(f"   - Activities: {len(task1_result.activities)}")
        print(f"   - Products: {len(task1_result.products)}")
        
        # Get all documents for tasks 2 and 3
        documents = await self._fetch_all_documents()
        
        # Task 2: Predict document relevance
        print(format_for_terminal("\n## TASK 2: Predicting Document Relevance..."))
        print("-" * 40)
        task2_result = self.relevance_predictor.predict_relevance(
            documents,
            task1_result.entities,
            task1_result.activities,
            task1_result.products
        )
        
        print(format_for_terminal("**Task 2 Complete:**"))
        print(f"   - Relevant documents: {len(task2_result['document_relevance'])}")
        print(f"   - Coverage: {task2_result['summary']['relevance_percentage']}%")
        
        # Task 3: Extract definitions
        print(format_for_terminal("\n## TASK 3: Extracting Formal Definitions..."))
        print("-" * 40)
        task3_result = self.definition_extractor.extract_definitions(
            documents,
            task1_result.entities,
            task1_result.activities,
            task1_result.products
        )
        
        print(format_for_terminal("**Task 3 Complete:**"))
        print(f"   - Definitions found: {task3_result['summary']['total_definitions_found']}")
        print(f"   - Item coverage: {task3_result['summary']['coverage_percentage']}%")
        
        # Compile comprehensive results
        comprehensive_results = {
            "query": query,
            "execution_timestamp": datetime.now().isoformat(),
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
        """Generate overall summary of all tasks"""
        return {
            "total_items_extracted": len(task1_result.entities) + len(task1_result.activities) + len(task1_result.products),
            "documents_processed": task1_result.total_documents_processed,
            "relevant_documents_identified": len(task2_result["document_relevance"]),
            "definitions_found": task3_result["summary"]["total_definitions_found"],
            "overall_coverage": {
                "items_with_definitions": task3_result["summary"]["items_with_definitions"],
                "definition_coverage_percentage": task3_result["summary"]["coverage_percentage"],
                "document_relevance_percentage": task2_result["summary"]["relevance_percentage"]
            }
        }
    
    def save_results(self, results: Dict[str, Any], output_dir: Path = None):
        """Save results in multiple formats"""
        if output_dir is None:
            output_dir = Path("output")
        
        output_dir.mkdir(exist_ok=True)
        
        # Create subfolder based on query
        query_folder = self._create_query_folder(results["query"], output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete results as JSON
        with open(query_folder / f"complete_results_summary_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save Task 1 results separately
        with open(query_folder / f"task1_hierarchical_table_{timestamp}.json", "w") as f:
            json.dump(results["task1_hierarchical_table"], f, indent=2, default=str)
        
        # Save Task 2 results as JSON
        with open(query_folder / f"task2_document_relevance_{timestamp}.json", "w") as f:
            json.dump(results["task2_document_relevance"], f, indent=2, default=str)
        
        # Save Task 3 results as JSON
        with open(query_folder / f"task3_regulatory_taxonomy_{timestamp}.json", "w") as f:
            json.dump(results["task3_definitions"], f, indent=2, default=str)
        
        # Save Task 1 in markdown format
        with open(query_folder / f"TASK1_HIERARCHICAL_TABLE_{timestamp}.md", "w") as f:
            f.write(self._format_task1_markdown(results["task1_hierarchical_table"]))
        
        # Save MERGED Task 2 & 3 in single report
        with open(query_folder / f"TASK2_3_DOCUMENT_ANALYSIS_{timestamp}.md", "w") as f:
            f.write(self._format_task2_3_document_analysis(results))
        
        # Save comprehensive human-readable summary
        with open(query_folder / f"COMPREHENSIVE_REGGENOME_REPORT_{timestamp}.md", "w") as f:
            f.write(self._format_comprehensive_report(results))
        
        # Save human-readable summary
        with open(query_folder / f"HUMAN_READABLE_SUMMARY_{timestamp}.md", "w") as f:
            f.write(self._format_comprehensive_summary(results))
        
        # Generate RegGenome Challenge Deliverables (CSV + JSON format)
        print(format_for_terminal("\n## Generating RegGenome Challenge Deliverables..."))
        deliverable_files = self.deliverable_formatter.format_all_deliverables(results, query_folder)
        
        # Save deliverable summary
        summary_report = self.deliverable_formatter.generate_summary_report(deliverable_files, results["query"])
        with open(query_folder / f"REGGENOME_DELIVERABLES_SUMMARY_{timestamp}.md", "w") as f:
            f.write(summary_report)
        
        print(format_for_terminal(f"\n**All results saved to {query_folder}/**"))
        print(f"   - Complete JSON: complete_results_summary_{timestamp}.json")
        print(f"   - Task 1 Table: TASK1_HIERARCHICAL_TABLE_{timestamp}.md")
        print(f"   - Task 2&3 Analysis: TASK2_3_DOCUMENT_ANALYSIS_{timestamp}.md")
        print(f"   - Comprehensive Report: COMPREHENSIVE_REGGENOME_REPORT_{timestamp}.md")
        print(f"   - Human Summary: HUMAN_READABLE_SUMMARY_{timestamp}.md")
        print(format_for_terminal("\n### RegGenome Challenge Deliverables:"))
        print(f"   - Deliverable 1 (CSV): {Path(deliverable_files['taxonomy_csv']).name}")
        print(f"   - Deliverable 2 (CSV): {Path(deliverable_files['relevance_csv']).name}")  
        print(f"   - Deliverable 3 (CSV): {Path(deliverable_files['definitions_csv']).name}")
        print(f"   - Deliverables Summary: REGGENOME_DELIVERABLES_SUMMARY_{timestamp}.md")
        
        return timestamp
    
    def _create_query_folder(self, query: str, output_dir: Path) -> Path:
        """Create a folder based on the first 10 chars of the query"""
        # Clean the query for folder name
        clean_query = re.sub(r'[^\w\s-]', '', query)  # Remove special chars
        clean_query = re.sub(r'[-\s]+', '_', clean_query)  # Replace spaces/hyphens with underscore
        folder_name = clean_query[:10].strip('_')  # First 10 chars
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{folder_name}_{timestamp}"
        
        # Create the folder
        query_folder = output_dir / folder_name
        query_folder.mkdir(exist_ok=True)
        
        return query_folder
    
    def _format_task1_markdown(self, table: Dict[str, Any]) -> str:
        """Format Task 1 results as markdown"""
        lines = []
        lines.append("# TASK 1: HIERARCHICAL TABLE OF REGULATED ITEMS")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n## Summary")
        lines.append(f"- Total unique items: {table['summary']['total_unique_items']}")
        lines.append(f"- Documents processed: {table['summary']['documents_processed']}")
        
        # Entities section
        lines.append("\n## 1. REGULATED ENTITIES")
        for entity_group in table["regulated_entities"]:
            lines.append(f"\n### {entity_group['type'].replace('_', ' ').title()} ({entity_group['count']} items)")
            lines.append("\n| Name | Description | Jurisdiction | Framework | Confidence |")
            lines.append("|------|-------------|--------------|-----------|------------|")
            
            for item in entity_group["items"][:10]:  # Top 10
                lines.append(f"| {item['name']} | {item['description'][:50]}... | {item.get('jurisdiction', 'N/A')} | {item.get('regulatory_framework', 'N/A')} | {item['confidence']:.2f} |")
        
        # Activities section
        lines.append("\n## 2. REGULATED ACTIVITIES")
        for activity_group in table["regulated_activities"]:
            lines.append(f"\n### {activity_group['type'].replace('_', ' ').title()} ({activity_group['count']} items)")
            lines.append("\n| Name | Description | Applicable Entities | Confidence |")
            lines.append("|------|-------------|---------------------|------------|")
            
            for item in activity_group["items"][:10]:
                entities = ", ".join(item.get('applicable_entities', [])[:3])
                lines.append(f"| {item['name']} | {item['description'][:50]}... | {entities} | {item['confidence']:.2f} |")
        
        # Products section
        lines.append("\n## 3. REGULATED PRODUCTS")
        for product_group in table["regulated_products"]:
            lines.append(f"\n### {product_group['type'].replace('_', ' ').title()} ({product_group['count']} items)")
            lines.append("\n| Name | Description | Asset Classes | Confidence |")
            lines.append("|------|-------------|---------------|------------|")
            
            for item in product_group["items"][:10]:
                assets = ", ".join(item.get('asset_classes', [])[:3])
                lines.append(f"| {item['name']} | {item['description'][:50]}... | {assets} | {item['confidence']:.2f} |")
        
        return "\n".join(lines)
    
    def _format_task2_3_document_analysis(self, results: Dict[str, Any]) -> str:
        """Format Task 2 & 3 as a unified document analysis report"""
        lines = []
        lines.append("# TASK 2 & 3: DOCUMENT ANALYSIS WITH CITATIONS")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n**Query:** {results['query']}")
        
        relevance_data = results["task2_document_relevance"]
        definitions_data = results["task3_definitions"]
        
        # Summary Section
        lines.append("\n## EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(f"\n- **Documents Analyzed:** {relevance_data['summary']['total_documents_analyzed']}")
        lines.append(f"- **Relevant Documents:** {relevance_data['summary']['relevant_documents']} ({relevance_data['summary']['relevance_percentage']}%)")
        lines.append(f"- **Formal Definitions Found:** {definitions_data['summary']['total_definitions_found']}")
        lines.append(f"- **Items with Definitions:** {definitions_data['summary']['items_with_definitions']} / {definitions_data['summary']['total_items']} ({definitions_data['summary']['coverage_percentage']}%)")
        
        # Document Relevance Analysis
        lines.append("\n## DOCUMENT RELEVANCE ANALYSIS")
        lines.append("-" * 80)
        
        # Create a map of item to definitions for easy lookup
        definition_map = {}
        for entity_def in definitions_data["entity_definitions"]:
            definition_map[entity_def["name"]] = entity_def["definitions"]
        for activity_def in definitions_data["activity_definitions"]:
            definition_map[activity_def["name"]] = activity_def["definitions"]
        for product_def in definitions_data["product_definitions"]:
            definition_map[product_def["name"]] = product_def["definitions"]
        
        # Most Referenced Items with Definitions
        lines.append("\n### HIGHLY REFERENCED ITEMS WITH FORMAL DEFINITIONS")
        
        # Entities
        if relevance_data["summary"]["top_relevant_entities"]:
            lines.append("\n#### Entities")
            for entity, count in relevance_data["summary"]["top_relevant_entities"][:5]:
                lines.append(f"\n**{entity}** - Referenced in {count} documents")
                
                # Check if we have a definition
                if entity in definition_map and definition_map[entity]:
                    best_def = definition_map[entity][0]  # Highest confidence
                    lines.append(f"\n**Definition:** {best_def['definition']}")
                    lines.append(f"\n**Citation:**")
                    lines.append(f"   - Document: {best_def['source']['document_title']}")
                    lines.append(f"   - Document ID: `{best_def['source']['document_id']}`")
                    if best_def['source'].get('document_url'):
                        lines.append(f"   - URL: {best_def['source']['document_url']}")
                else:
                    lines.append("\n*No formal definition found*")
        
        # Activities
        if relevance_data["summary"]["top_relevant_activities"]:
            lines.append("\n#### Activities")
            for activity, count in relevance_data["summary"]["top_relevant_activities"][:5]:
                lines.append(f"\n**{activity}** - Referenced in {count} documents")
                
                if activity in definition_map and definition_map[activity]:
                    best_def = definition_map[activity][0]
                    lines.append(f"\n**Definition:** {best_def['definition']}")
                    lines.append(f"\n**Citation:**")
                    lines.append(f"   - Document: {best_def['source']['document_title']}")
                    lines.append(f"   - Document ID: `{best_def['source']['document_id']}`")
                    if best_def['source'].get('document_url'):
                        lines.append(f"   - URL: {best_def['source']['document_url']}")
                else:
                    lines.append("\n*No formal definition found*")
        
        # Products
        if relevance_data["summary"]["top_relevant_products"]:
            lines.append("\n#### Products")
            for product, count in relevance_data["summary"]["top_relevant_products"][:5]:
                lines.append(f"\n**{product}** - Referenced in {count} documents")
                
                if product in definition_map and definition_map[product]:
                    best_def = definition_map[product][0]
                    lines.append(f"\n**Definition:** {best_def['definition']}")
                    lines.append(f"\n**Citation:**")
                    lines.append(f"   - Document: {best_def['source']['document_title']}")
                    lines.append(f"   - Document ID: `{best_def['source']['document_id']}`")
                    if best_def['source'].get('document_url'):
                        lines.append(f"   - URL: {best_def['source']['document_url']}")
                else:
                    lines.append("\n*No formal definition found*")
        
        # Key Documents with High Relevance
        lines.append("\n### KEY REGULATORY DOCUMENTS")
        lines.append("\n| Document Title | Relevance Score | Primary Focus | Document ID |")
        lines.append("|----------------|-----------------|---------------|-------------|")
        
        for doc in relevance_data["document_relevance"][:15]:
            title = doc["title"][:50] + "..." if len(doc["title"]) > 50 else doc["title"]
            doc_id = doc["document_id"][:12] + "..." if len(doc["document_id"]) > 12 else doc["document_id"]
            lines.append(f"| {title} | {doc['total_relevance_score']:.1f} | {doc['primary_focus']} | `{doc_id}` |")
        
        # Sub-document Analysis
        lines.append("\n### SUB-DOCUMENT LEVEL ANALYSIS")
        
        docs_with_subdocs = [d for d in relevance_data["document_relevance"] if d["subdocument_relevance"]]
        
        if docs_with_subdocs:
            lines.append(f"\n{len(docs_with_subdocs)} documents contain relevant sub-sections:")
            
            for doc in docs_with_subdocs[:5]:
                lines.append(f"\n**{doc['title']}**")
                for subdoc in doc["subdocument_relevance"][:2]:
                    lines.append(f"- Signpost {subdoc['signpost_index']}: {', '.join(subdoc['tags'][:3])}")
                    
                    relevant_items = []
                    for e in subdoc.get("relevant_entities", {}).keys():
                        relevant_items.append(f"{e} (Entity)")
                    for a in subdoc.get("relevant_activities", {}).keys():
                        relevant_items.append(f"{a} (Activity)")
                    for p in subdoc.get("relevant_products", {}).keys():
                        relevant_items.append(f"{p} (Product)")
                    
                    if relevant_items:
                        lines.append(f"  Relevant to: {', '.join(relevant_items[:3])}")
        
        # Definition Coverage Analysis
        lines.append("\n## DEFINITION COVERAGE ANALYSIS")
        lines.append("-" * 80)
        
        coverage = definitions_data["summary"]["coverage_by_type"]
        lines.append("\n| Category | Total Items | With Definitions | Coverage % |")
        lines.append("|----------|-------------|------------------|------------|")
        
        for item_type, stats in coverage.items():
            coverage_pct = (stats["with_definitions"] / stats["total"] * 100) if stats["total"] > 0 else 0
            lines.append(f"| {item_type.title()} | {stats['total']} | {stats['with_definitions']} | {coverage_pct:.1f}% |")
        
        # Items Without Definitions
        lines.append("\n### ITEMS REQUIRING DEFINITION CLARIFICATION")
        
        # Find items without definitions from top referenced items
        missing_definitions = []
        
        for entity, count in relevance_data["summary"]["top_relevant_entities"][:10]:
            if entity not in definition_map or not definition_map[entity]:
                missing_definitions.append((entity, "Entity", count))
        
        for activity, count in relevance_data["summary"]["top_relevant_activities"][:10]:
            if activity not in definition_map or not definition_map[activity]:
                missing_definitions.append((activity, "Activity", count))
        
        for product, count in relevance_data["summary"]["top_relevant_products"][:10]:
            if product not in definition_map or not definition_map[product]:
                missing_definitions.append((product, "Product", count))
        
        if missing_definitions:
            missing_definitions.sort(key=lambda x: x[2], reverse=True)  # Sort by reference count
            lines.append("\nThe following frequently referenced items lack formal definitions:")
            for item, item_type, count in missing_definitions[:10]:
                lines.append(f"- **{item}** ({item_type}) - Referenced in {count} documents")
        
        return "\n".join(lines)
    
    def _format_task2_markdown(self, relevance_data: Dict[str, Any]) -> str:
        """Format Task 2 results as markdown"""
        lines = []
        lines.append("# TASK 2: DOCUMENT RELEVANCE PREDICTIONS")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        summary = relevance_data["summary"]
        lines.append("\n## Summary")
        lines.append(f"- Documents analyzed: {summary['total_documents_analyzed']}")
        lines.append(f"- Relevant documents: {summary['relevant_documents']}")
        lines.append(f"- Relevance percentage: {summary['relevance_percentage']}%")
        
        return "\n".join(lines)
    
    def _format_task3_markdown(self, definitions_data: Dict[str, Any]) -> str:
        """Format Task 3 results as markdown with proper citations"""
        lines = []
        lines.append("# TASK 3: FORMAL DEFINITIONS WITH DOCUMENT CITATIONS")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        summary = definitions_data["summary"]
        lines.append("\n## Summary")
        lines.append(f"- Total items: {summary['total_items']}")
        lines.append(f"- Items with definitions: {summary['items_with_definitions']}")
        lines.append(f"- Coverage: {summary['coverage_percentage']}%")
        
        return "\n".join(lines)
    
    def _format_comprehensive_summary(self, results: Dict[str, Any]) -> str:
        """Format comprehensive human-readable summary"""
        lines = []
        lines.append("# COMPREHENSIVE REGGENOME RESEARCH REPORT")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n**Query:** {results['query']}")
        
        # Executive Summary
        lines.append("\n## EXECUTIVE SUMMARY")
        overall = results["overall_summary"]
        lines.append(f"\nThis research analyzed **{overall['documents_processed']} regulatory documents** and identified:")
        lines.append(f"- **{overall['total_items_extracted']} unique regulated items** (entities, activities, and products)")
        lines.append(f"- **{overall['relevant_documents_identified']} documents** directly relevant to these items")
        lines.append(f"- **{overall['definitions_found']} formal definitions** with document citations")
        lines.append(f"- **{overall['overall_coverage']['definition_coverage_percentage']}%** of items have formal definitions")
        
        return "\n".join(lines)
    
    def _format_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """Format a comprehensive report combining all three tasks"""
        lines = []
        lines.append("# COMPREHENSIVE REGGENOME RESEARCH REPORT")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n**Research Query:** {results['query']}")
        
        # Executive Summary
        lines.append("\n" + "="*80)
        lines.append("\n## EXECUTIVE SUMMARY")
        lines.append("="*80)
        
        overall = results["overall_summary"]
        table = results["task1_hierarchical_table"]
        relevance = results["task2_document_relevance"]["summary"]
        definitions = results["task3_definitions"]["summary"]
        
        lines.append(f"\nThis comprehensive analysis of regulatory documents has identified and analyzed:")
        lines.append(f"- **{overall['total_items_extracted']}** unique regulated items across entities, activities, and products")
        lines.append(f"- **{overall['documents_processed']}** regulatory documents processed")
        lines.append(f"- **{overall['relevant_documents_identified']}** documents ({relevance['relevance_percentage']}%) directly relevant to identified items")
        lines.append(f"- **{overall['definitions_found']}** formal definitions extracted with citations")
        lines.append(f"- **{overall['overall_coverage']['definition_coverage_percentage']}%** of items have formal definitions")
        
        # Key Findings by Task
        lines.append("\n## KEY FINDINGS")
        
        # Task 1 highlights
        lines.append("\n### Task 1: Regulated Items Identified")
        entity_count = sum(g["count"] for g in table["regulated_entities"])
        activity_count = sum(g["count"] for g in table["regulated_activities"])
        product_count = sum(g["count"] for g in table["regulated_products"])
        lines.append(f"- **Entities:** {entity_count} unique regulated entities")
        lines.append(f"- **Activities:** {activity_count} unique regulated activities")
        lines.append(f"- **Products:** {product_count} unique regulated products")
        
        # Task 2 highlights
        lines.append("\n### Task 2: Document Relevance")
        lines.append(f"- **{relevance['relevance_percentage']}%** of documents are relevant to identified items")
        lines.append(f"- **Top referenced categories:**")
        if relevance["top_relevant_entities"]:
            top_entity = relevance["top_relevant_entities"][0]
            lines.append(f"  - Entity: {top_entity[0]} ({top_entity[1]} documents)")
        if relevance["top_relevant_activities"]:
            top_activity = relevance["top_relevant_activities"][0]
            lines.append(f"  - Activity: {top_activity[0]} ({top_activity[1]} documents)")
        
        # Task 3 highlights
        lines.append("\n### Task 3: Definition Coverage")
        lines.append(f"- **{definitions['coverage_percentage']}%** of items have formal definitions")
        lines.append(f"- **{definitions['documents_with_definitions']}** documents contain definitions")
        lines.append(f"- **Average confidence:** {definitions['average_confidence']}")
        
        return "\n".join(lines)