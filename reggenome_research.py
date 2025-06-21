"""
RegGenome Deep Research System
Comprehensive analysis for all three tasks:
1. Extract regulated entities, activities, and products
2. Predict document relevance
3. Extract formal definitions with citations
"""

import asyncio
import argparse
from pathlib import Path

from src.config import Config
from src.unified_interface import UnifiedResearchInterface

async def main():
    """Main entry point for comprehensive RegGenome research"""
    
    parser = argparse.ArgumentParser(description="RegGenome Deep Research System")
    parser.add_argument("query", nargs="?", 
                       default="How does a UK fund conduct CDD & KYC with both the EU and UK regulators when verifying foreign investors post-Brexit?",
                       help="Research query")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Output directory for results")
    parser.add_argument("--task", type=str, choices=["all", "1", "2", "3"], default="all",
                       help="Which task(s) to run")
    
    args = parser.parse_args()
    
    # Check for API key
    if not Path("key.txt").exists():
        print("\n❌ ERROR: API key not found!")
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return
    
    # Initialize
    config = Config()
    interface = UnifiedResearchInterface(config)
    
    try:
        if args.task == "all":
            # Run all tasks
            results = await interface.run_all_tasks(args.query)
            interface.save_results(results, Path(args.output_dir))
            
        else:
            # Run specific task(s) - for future implementation
            print(f"Running only Task {args.task} is not yet implemented.")
            print("Please use --task all to run all tasks.")
            
    except Exception as e:
        print(f"\n❌ Error during research: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())