"""
Example usage of the Deep Research Multi-agent System

This script demonstrates how to use the system for different queries and configurations.
"""

import asyncio
import json
from pathlib import Path
from src.config import Config
from src.deep_research_orchestrator import DeepResearchOrchestrator
from src.terminal_formatter import format_for_terminal

async def example_basic_research():
    """Basic example: Research a simple query"""
    config = Config()
    orchestrator = DeepResearchOrchestrator(config)
    
    query = "What are the main regulated entities in UCITS directives?"
    
    print(format_for_terminal(f"**Running basic research for:** {query}"))
    result = await orchestrator.research(query)
    
    print(format_for_terminal(f"\n**Found {len(result.entities)} entities:**"))
    for entity in result.entities[:5]:
        print(f"  - {entity.name} ({entity.entity_type.value})")
    
    return result

async def example_custom_config():
    """Example with custom configuration"""
    config = Config()
    
    # Customize configuration
    config.max_pages_per_query = 5  # Limit pages for faster demo
    config.page_size = 50  # Smaller page size
    
    orchestrator = DeepResearchOrchestrator(config)
    
    query = "Investment adviser compliance requirements"
    
    print(format_for_terminal(f"**Running research with custom config for:** {query}"))
    result = await orchestrator.research(query)
    
    print(format_for_terminal(f"\n**Found {len(result.activities)} activities**"))
    print(f"Processing took {result.total_documents_processed} documents")
    
    return result

async def example_specific_extraction():
    """Example: Extract specific types of information"""
    config = Config()
    orchestrator = DeepResearchOrchestrator(config)
    
    # You can also process the results to filter specific information
    query = "Fund distribution and marketing activities"
    
    print(f"Running targeted extraction for: {query}")
    result = await orchestrator.research(query)
    
    # Filter for distribution activities
    distribution_activities = [
        activity for activity in result.activities 
        if "distribution" in activity.name.lower() or "marketing" in activity.name.lower()
    ]
    
    print(f"\nFound {len(distribution_activities)} distribution/marketing activities:")
    for activity in distribution_activities:
        print(f"  - {activity.name}")
        if activity.applicable_entities:
            print(f"    Applies to: {', '.join(activity.applicable_entities[:3])}")
    
    return result

async def example_save_formatted_output():
    """Example: Save results in different formats"""
    config = Config()
    orchestrator = DeepResearchOrchestrator(config)
    
    query = "Depositary requirements for UCITS funds"
    
    print(f"Running research and saving in multiple formats for: {query}")
    result = await orchestrator.research(query)
    
    # Generate hierarchical table
    table = orchestrator.generate_hierarchical_table(result)
    
    # Save as JSON
    with open("output/example_results.json", "w") as f:
        json.dump(table, f, indent=2, default=str)
    
    # Save as CSV-friendly format
    import csv
    
    with open("output/example_entities.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "Name", "Description", "Jurisdiction", "Confidence"])
        
        for entity in result.entities:
            writer.writerow([
                entity.entity_type.value,
                entity.name,
                entity.description,
                entity.jurisdiction or "N/A",
                f"{entity.confidence:.2f}"
            ])
    
    print(f"  Saved results to output/example_results.json and output/example_entities.csv")
    
    return result

async def main():
    """Run all examples"""
    print("=" * 80)
    print("DEEP RESEARCH MULTI-AGENT SYSTEM - USAGE EXAMPLES")
    print("=" * 80)
    
    # Ensure output directory exists
    Path("output").mkdir(exist_ok=True)
    
    # Run examples
    print("\n1. BASIC RESEARCH EXAMPLE")
    print("-" * 40)
    await example_basic_research()
    
    print("\n\n2. CUSTOM CONFIGURATION EXAMPLE")
    print("-" * 40)
    await example_custom_config()
    
    print("\n\n3. SPECIFIC EXTRACTION EXAMPLE")
    print("-" * 40)
    await example_specific_extraction()
    
    print("\n\n4. FORMATTED OUTPUT EXAMPLE")
    print("-" * 40)
    await example_save_formatted_output()
    
    print("\n\n✅ All examples completed successfully!")

if __name__ == "__main__":
    # Note: Replace this with your actual API key handling
    print("\nNote: Make sure you have your API key in key.txt before running!")
    print("The system will use the JWT token for RegGenome API authentication.\n")
    
    asyncio.run(main())