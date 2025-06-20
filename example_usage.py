#!/usr/bin/env python3
"""
Example usage of the RegGenome Deep Research Multi-agent System

This script demonstrates how to use the deep research system programmatically
to extract regulated activities, entities, and products from regulatory documents.
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.deep_research_orchestrator import DeepResearchOrchestrator


async def basic_example():
    """Basic example of running the deep research system."""
    
    print("🧪 Running basic example with mock data...")
    
    # Create orchestrator with mock API (no API keys needed)
    orchestrator = DeepResearchOrchestrator(use_mock_api=True)
    
    try:
        # Run the research workflow
        taxonomy = await orchestrator.run_research(
            query="Identify investment regulations and compliance requirements",
            save_results=False  # Don't save files in this example
        )
        
        # Print results
        print("\n📊 Research Results:")
        print(f"  • Entities found: {len(taxonomy.entities)}")
        print(f"  • Activities found: {len(taxonomy.activities)}")
        print(f"  • Products found: {len(taxonomy.products)}")
        
        # Show some examples
        if taxonomy.entities:
            print(f"\n🏢 Example Entity: {taxonomy.entities[0].name}")
            print(f"   Type: {taxonomy.entities[0].entity_type}")
            print(f"   Description: {taxonomy.entities[0].description[:100]}...")
        
        if taxonomy.activities:
            print(f"\n⚡ Example Activity: {taxonomy.activities[0].name}")
            print(f"   Type: {taxonomy.activities[0].activity_type}")
            print(f"   Description: {taxonomy.activities[0].description[:100]}...")
        
        if taxonomy.products:
            print(f"\n📦 Example Product: {taxonomy.products[0].name}")
            print(f"   Type: {taxonomy.products[0].product_type}")
            print(f"   Description: {taxonomy.products[0].description[:100]}...")
        
        return taxonomy
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


async def advanced_example():
    """Advanced example showing custom analysis and hierarchical table creation."""
    
    print("\n🔬 Running advanced example...")
    
    orchestrator = DeepResearchOrchestrator(use_mock_api=True)
    
    try:
        # Run research with custom query
        taxonomy = await orchestrator.run_research(
            query="Focus on UCITS regulations and mutual fund compliance",
            save_results=False
        )
        
        # Get detailed statistics
        stats = orchestrator.get_summary_statistics()
        
        print("\n📈 Detailed Statistics:")
        print(f"  Query: {stats['query']}")
        print(f"  Documents processed: {stats['totals']['documents']}")
        
        # Entity breakdown
        if stats['entity_breakdown']:
            print("\n🏢 Entity Types Found:")
            for entity_type, count in stats['entity_breakdown'].items():
                print(f"   • {entity_type.replace('_', ' ').title()}: {count}")
        
        # Activity breakdown
        if stats['activity_breakdown']:
            print("\n⚡ Activity Types Found:")
            for activity_type, count in stats['activity_breakdown'].items():
                print(f"   • {activity_type.replace('_', ' ').title()}: {count}")
        
        # Product breakdown
        if stats['product_breakdown']:
            print("\n📦 Product Types Found:")
            for product_type, count in stats['product_breakdown'].items():
                print(f"   • {product_type.replace('_', ' ').title()}: {count}")
        
        # Create hierarchical table (Task 1 deliverable)
        print("\n📋 Creating hierarchical table...")
        hierarchical_table = await orchestrator.create_hierarchical_table()
        
        # Save the hierarchical table
        output_file = "example_hierarchical_table.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchical_table, f, indent=2, default=str)
        
        print(f"✅ Hierarchical table saved to: {output_file}")
        
        # Show table structure
        print("\n🗂️ Table Structure:")
        for category, items in hierarchical_table.items():
            if category != "metadata" and isinstance(items, dict):
                total_items = sum(len(item_list) for item_list in items.values())
                print(f"   • {category.replace('_', ' ').title()}: {total_items} items")
                for subcategory, item_list in items.items():
                    if item_list:
                        print(f"     - {subcategory.replace('_', ' ').title()}: {len(item_list)}")
        
        return hierarchical_table
        
    except Exception as e:
        print(f"❌ Error in advanced example: {e}")
        raise


async def focused_extraction_example():
    """Example of extracting specific types of regulatory items."""
    
    print("\n🎯 Running focused extraction example...")
    
    orchestrator = DeepResearchOrchestrator(use_mock_api=True)
    
    # Run research workflow
    taxonomy = await orchestrator.run_research(
        query="Extract investment adviser regulations and mutual fund definitions",
        save_results=False
    )
    
    # Filter for specific types
    investment_advisers = [
        entity for entity in taxonomy.entities 
        if "investment_adviser" in entity.entity_type.value
    ]
    
    advisory_activities = [
        activity for activity in taxonomy.activities
        if "advisory" in activity.activity_type.value or "investment" in activity.name.lower()
    ]
    
    mutual_funds = [
        product for product in taxonomy.products
        if "mutual_fund" in product.product_type.value or "fund" in product.name.lower()
    ]
    
    print(f"\n🎯 Focused Results:")
    print(f"   • Investment Advisers: {len(investment_advisers)}")
    print(f"   • Advisory Activities: {len(advisory_activities)}")
    print(f"   • Mutual Fund Products: {len(mutual_funds)}")
    
    # Show detailed information for one item from each category
    if investment_advisers:
        entity = investment_advisers[0]
        print(f"\n📋 Sample Investment Adviser:")
        print(f"   Name: {entity.name}")
        print(f"   Jurisdictions: {', '.join(entity.applicable_jurisdictions)}")
        print(f"   Framework: {', '.join(entity.regulatory_framework)}")
        print(f"   Confidence: {entity.confidence_score:.2f}")
    
    if advisory_activities:
        activity = advisory_activities[0]
        print(f"\n📋 Sample Advisory Activity:")
        print(f"   Name: {activity.name}")
        print(f"   Requirements: {len(activity.regulatory_requirements)} items")
        print(f"   Licenses: {len(activity.required_licenses)} items")
        print(f"   Confidence: {activity.confidence_score:.2f}")
    
    if mutual_funds:
        product = mutual_funds[0]
        print(f"\n📋 Sample Mutual Fund Product:")
        print(f"   Name: {product.name}")
        print(f"   Classifications: {len(product.regulatory_classification)} items")
        print(f"   Requirements: {len(product.compliance_requirements)} items")
        print(f"   Confidence: {product.confidence_score:.2f}")


async def document_relevance_example():
    """Example of analyzing document relevance (Task 2)."""
    
    print("\n📄 Running document relevance analysis example...")
    
    orchestrator = DeepResearchOrchestrator(use_mock_api=True)
    
    # Run research workflow
    taxonomy = await orchestrator.run_research(
        query="Analyze document relevance to regulatory items",
        save_results=False
    )
    
    # Analyze document relevance
    print(f"\n📊 Document Relevance Analysis:")
    
    for doc_relevance in taxonomy.document_relevance:
        print(f"\nDocument: {doc_relevance.document_id}")
        
        # Entity relevance
        if doc_relevance.entity_relevance:
            avg_entity_relevance = sum(doc_relevance.entity_relevance.values()) / len(doc_relevance.entity_relevance)
            print(f"   • Entity relevance: {avg_entity_relevance:.2f} (avg of {len(doc_relevance.entity_relevance)} entities)")
        
        # Activity relevance
        if doc_relevance.activity_relevance:
            avg_activity_relevance = sum(doc_relevance.activity_relevance.values()) / len(doc_relevance.activity_relevance)
            print(f"   • Activity relevance: {avg_activity_relevance:.2f} (avg of {len(doc_relevance.activity_relevance)} activities)")
        
        # Product relevance
        if doc_relevance.product_relevance:
            avg_product_relevance = sum(doc_relevance.product_relevance.values()) / len(doc_relevance.product_relevance)
            print(f"   • Product relevance: {avg_product_relevance:.2f} (avg of {len(doc_relevance.product_relevance)} products)")


async def main():
    """Run all examples."""
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 RegGenome Deep Research System - Examples")
    print("=" * 60)
    
    try:
        # Run basic example
        await basic_example()
        
        # Run advanced example
        await advanced_example()
        
        # Run focused extraction example
        await focused_extraction_example()
        
        # Run document relevance example
        await document_relevance_example()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("\nNext steps:")
        print("1. Review the generated 'example_hierarchical_table.json' file")
        print("2. Try running 'python main.py --mock' for the full CLI experience")
        print("3. Set up your API keys and run with real RegGenome data")
        
    except Exception as e:
        print(f"\n❌ Examples failed: {e}")
        logging.exception("Detailed error information:")
        return 1
    
    return 0


if __name__ == "__main__":
    # Handle Windows event loop policy
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 