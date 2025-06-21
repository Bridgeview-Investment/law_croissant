#!/usr/bin/env python3
"""
Example: Using the RegGenome Unified Interface

This script demonstrates different ways to use the one-for-all interface
to generate all RegGenome challenge deliverables.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.unified_interface import run_complete_analysis, quick_research
from src.config import config


def example_1_simple_usage():
    """Example 1: Simplest possible usage."""
    print("🔥 Example 1: Simple Usage")
    print("=" * 40)
    
    # One line to generate all deliverables
    results = run_complete_analysis("investment advisers")
    
    print(f"✅ Found {len(results.taxonomy.entities)} entities")
    print(f"✅ Found {len(results.taxonomy.activities)} activities") 
    print(f"✅ Found {len(results.taxonomy.products)} products")
    print(f"✅ Task 1 file: {results.output_files['hierarchical_table']}")
    print()


def example_2_with_custom_config():
    """Example 2: Using custom configuration."""
    print("🔥 Example 2: Custom Configuration")
    print("=" * 40)
    
    # Custom configuration
    custom_config = {
        "llm": {
            "default_model": "gpt-4o",  # Use more powerful model
            "temperature": 0.0  # More deterministic results
        },
        "research": {
            "confidence_threshold": 0.8  # Higher confidence threshold
        }
    }
    
    results = run_complete_analysis(
        query="UCITS fund regulations and compliance requirements",
        output_dir="ucits_analysis",
        custom_config=custom_config
    )
    
    print(f"✅ Analysis completed with custom config")
    print(f"✅ Results saved to: {results.metadata['output_directory']}")
    print()


def example_3_quick_research():
    """Example 3: Ultra-simple quick research."""
    print("🔥 Example 3: Quick Research")
    print("=" * 40)
    
    # One line for quick results
    summary_file = quick_research("hedge funds", "hedge_fund_analysis")
    
    print(f"✅ Quick research completed")
    print(f"✅ Summary saved to: {summary_file}")
    print()


def example_4_mock_data():
    """Example 4: Using mock data for testing."""
    print("🔥 Example 4: Mock Data (No API Required)")
    print("=" * 40)
    
    results = run_complete_analysis(
        query="pension fund regulations",
        output_dir="pension_analysis",
        use_real_api=False  # Use mock data
    )
    
    print(f"✅ Mock analysis completed")
    print(f"✅ Processing time: {results.metadata['processing_time']:.2f} seconds")
    print()


def example_5_programmatic_analysis():
    """Example 5: Programmatic analysis with result processing."""
    print("🔥 Example 5: Programmatic Analysis")
    print("=" * 40)
    
    results = run_complete_analysis(
        query="mutual fund and ETF regulations",
        output_dir="fund_analysis",
        save_files=False  # Don't save files, just get results
    )
    
    # Process results programmatically
    print("Entity Analysis:")
    entity_types = {}
    for entity in results.taxonomy.entities:
        entity_types[entity.entity_type] = entity_types.get(entity.entity_type, 0) + 1
    
    for entity_type, count in entity_types.items():
        print(f"  {entity_type}: {count}")
    
    print("\nActivity Analysis:")
    activity_types = {}
    for activity in results.taxonomy.activities:
        activity_types[activity.activity_type] = activity_types.get(activity.activity_type, 0) + 1
    
    for activity_type, count in activity_types.items():
        print(f"  {activity_type}: {count}")
    
    print()


def example_6_with_json_config():
    """Example 6: Loading from JSON config file."""
    print("🔥 Example 6: JSON Config File")
    print("=" * 40)
    
    # The config.json file is automatically loaded
    print(f"Current LLM model: {config.llm.default_model}")
    print(f"Current provider: {config.llm.provider}")
    print(f"JWT authentication: {config.reggenome.use_jwt_auth}")
    
    # Run with loaded config
    results = run_complete_analysis(
        query="insurance product regulations",
        output_dir="insurance_analysis"
    )
    
    print(f"✅ Analysis with JSON config completed")
    print()


def main():
    """Run all examples."""
    print("🚀 RegGenome Unified Interface Examples")
    print("=" * 50)
    print()
    
    # Check authentication status
    from src.auth import token_manager
    token_info = token_manager.get_token_info()
    if token_info['status'] == 'valid':
        print(f"🔐 JWT Authentication: Active (expires {token_info.get('expires_at')})")
    else:
        print("🔐 JWT Authentication: Not configured (will use mock data)")
    print()
    
    try:
        # Run examples
        example_1_simple_usage()
        example_3_quick_research()
        example_4_mock_data()
        example_5_programmatic_analysis()
        example_6_with_json_config()
        
        # Skip examples that require real API if not configured
        if token_info['status'] == 'valid':
            example_2_with_custom_config()
        else:
            print("⏭️  Skipping real API examples (no valid JWT token)")
            print()
        
        print("🎉 All examples completed successfully!")
        print()
        print("📚 Usage Summary:")
        print("• run_complete_analysis() - Full control, all options")
        print("• quick_research() - Simplest interface, minimal config")
        print("• Use config.json to set default LLM models and parameters")
        print("• Custom configs can override any setting on-the-fly")
        print("• Real API requires JWT token in key.txt")
        print("• Mock mode works without any API configuration")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 