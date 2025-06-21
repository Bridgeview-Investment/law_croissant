import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from src.config import Config
from src.deep_research_orchestrator import DeepResearchOrchestrator
from src.terminal_formatter import format_for_terminal

async def run_batch_mode(query: str = None):
    """Run in batch mode with a predefined query"""
    
    # Initialize configuration
    config = Config()
    
    # Use provided query or default
    if not query:
        query = "How does a UK fund conduct CDD & KYC with both the EU and UK regulators when verifying foreign investors post-Brexit?"
    
    print("=" * 80)
    print(format_for_terminal("# DEEP RESEARCH MULTI-AGENT SYSTEM - BATCH MODE"))
    print(format_for_terminal("## Task 1: Extract Regulated Activities, Entities, and Products"))
    print("=" * 80)
    print(f"\nQuery: {query}")
    print(f"\nInitiatives to analyze:")
    for key, name in config.initiative_filters.items():
        print(f"  - {name}")
    print("\n" + "-" * 80)
    
    # Initialize orchestrator
    orchestrator = DeepResearchOrchestrator(config)
    
    try:
        # Run the research
        print("\nStarting research process...")
        result = await orchestrator.research(query)
        
        # Generate hierarchical table
        table = orchestrator.generate_hierarchical_table(result)
        
        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full results as JSON
        with open(output_dir / f"task1_hierarchical_table_{timestamp}.json", "w") as f:
            json.dump(table, f, indent=2, default=str)
        
        # Save human-readable summary
        with open(output_dir / f"task1_summary_{timestamp}.txt", "w") as f:
            f.write(generate_summary_report(table, result))
        
        print(format_for_terminal(f"\n**Research complete!** Results saved to:"))
        print(f"  - output/task1_hierarchical_table_{timestamp}.json")
        print(f"  - output/task1_summary_{timestamp}.txt")
        
        # Print summary statistics
        print("\n" + "=" * 80)
        print(format_for_terminal("# SUMMARY STATISTICS"))
        print("=" * 80)
        print(f"Total documents processed: {result.total_documents_processed}")
        print(f"Unique entities found: {len(result.entities)}")
        print(f"Unique activities found: {len(result.activities)}")
        print(f"Unique products found: {len(result.products)}")
        print(f"Total unique items: {len(result.entities) + len(result.activities) + len(result.products)}")
        
    except Exception as e:
        print(format_for_terminal(f"\n**Error during research:** {e}"))
        raise

def generate_summary_report(table: dict, result) -> str:
    """Generate a human-readable summary report"""
    report = []
    
    report.append("DEEP RESEARCH MULTI-AGENT SYSTEM - TASK 1 RESULTS")
    report.append("=" * 80)
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Documents Processed: {result.total_documents_processed}")
    
    # Entities section
    report.append("\n\n1. REGULATED ENTITIES")
    report.append("-" * 40)
    for entity_group in table["regulated_entities"]:
        report.append(f"\n{entity_group['type'].upper()} ({entity_group['count']} found):")
        for item in entity_group["items"][:5]:  # Top 5
            report.append(f"  • {item['name']}")
            report.append(f"    Description: {item['description']}")
            if item.get('jurisdiction'):
                report.append(f"    Jurisdiction: {item['jurisdiction']}")
            if item.get('regulatory_framework'):
                report.append(f"    Framework: {item['regulatory_framework']}")
            report.append(f"    Confidence: {item['confidence']:.2f}")
            report.append("")
    
    # Activities section
    report.append("\n2. REGULATED ACTIVITIES")
    report.append("-" * 40)
    for activity_group in table["regulated_activities"]:
        report.append(f"\n{activity_group['type'].upper()} ({activity_group['count']} found):")
        for item in activity_group["items"][:5]:  # Top 5
            report.append(f"  • {item['name']}")
            report.append(f"    Description: {item['description']}")
            if item.get('applicable_entities'):
                report.append(f"    Applicable to: {', '.join(item['applicable_entities'][:3])}")
            if item.get('requirements'):
                report.append(f"    Key requirements:")
                for req in item['requirements'][:2]:
                    report.append(f"      - {req}")
            report.append(f"    Confidence: {item['confidence']:.2f}")
            report.append("")
    
    # Products section
    report.append("\n3. REGULATED PRODUCTS")
    report.append("-" * 40)
    for product_group in table["regulated_products"]:
        report.append(f"\n{product_group['type'].upper()} ({product_group['count']} found):")
        for item in product_group["items"][:5]:  # Top 5
            report.append(f"  • {item['name']}")
            report.append(f"    Description: {item['description']}")
            if item.get('asset_classes'):
                report.append(f"    Asset classes: {', '.join(item['asset_classes'])}")
            if item.get('issuer_requirements'):
                report.append(f"    Issuer requirements:")
                for req in item['issuer_requirements'][:2]:
                    report.append(f"      - {req}")
            if item.get('investor_restrictions'):
                report.append(f"    Investor restrictions:")
                for rest in item['investor_restrictions'][:2]:
                    report.append(f"      - {rest}")
            report.append(f"    Confidence: {item['confidence']:.2f}")
            report.append("")
    
    # Statistics
    report.append("\n\nEXTRACTION STATISTICS")
    report.append("-" * 40)
    stats = result.extraction_metadata["statistics"]
    report.append(f"Total items extracted: {stats['total_entities_extracted'] + stats['total_activities_extracted'] + stats['total_products_extracted']}")
    report.append(f"After deduplication: {stats['unique_entities'] + stats['unique_activities'] + stats['unique_products']}")
    report.append(f"Deduplication ratio: {stats['deduplication_ratio']:.1%}")
    
    return "\n".join(report)

def print_usage():
    """Print usage information"""
    print("\nUsage:")
    print("  python main.py                    # Run interactive mode")
    print("  python main.py --batch            # Run batch mode with default query")
    print("  python main.py --batch \"query\"    # Run batch mode with custom query")
    print("  python main.py --help             # Show this help message")

async def main():
    """Main entry point"""
    
    # Check for API key
    if not Path("key.txt").exists():
        print("\n❌ ERROR: API key not found!")
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    if not args:
        # No arguments - run interactive mode
        from interactive_cli import InteractiveCLI
        cli = InteractiveCLI()
        await cli.run()
        
    elif args[0] == "--help" or args[0] == "-h":
        print_usage()
        
    elif args[0] == "--batch" or args[0] == "-b":
        # Batch mode
        query = None
        if len(args) > 1:
            query = " ".join(args[1:])
        await run_batch_mode(query)
        
    else:
        # Assume the arguments form a query for batch mode
        query = " ".join(args)
        await run_batch_mode(query)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)