#!/usr/bin/env python3
"""
RegGenome Deep Research System - Complete Challenge Runner
Generates all three challenge deliverables with human-readable outputs:
1. Hierarchical table of regulated items (redundancy-free)
2. Document relevance predictions (document & sub-document level)
3. Definition linking with full text extraction (stretch goal)
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from src.unified_interface import run_complete_analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reggenome_research.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def print_banner():
    """Print a beautiful banner for the RegGenome Challenge"""
    print("\n" + "="*60)
    print("🏛️  REGGENOME DEEP RESEARCH CHALLENGE")
    print("🚀 AI-Powered Regulatory Intelligence System")
    print("="*60)
    print("📋 Challenge Objectives:")
    print("   1️⃣ Hierarchical Table (Redundancy-Free)")
    print("   2️⃣ Document Relevance Analysis")
    print("   3️⃣ Definition Links (Stretch Goal)")
    print("="*60 + "\n")

def print_progress_update(message: str, emoji: str = "🔄"):
    """Print formatted progress update"""
    print(f"{emoji} {message}")

def print_success_summary(results: dict):
    """Print beautiful success summary"""
    print("\n" + "="*60)
    print("🎉 REGGENOME CHALLENGE COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    # Results overview
    stats = results.get("results_summary", {})
    print(f"📊 Results Summary:")
    print(f"  🏢 Entities extracted: {stats.get('entities', {}).get('total', 0)}")
    print(f"  ⚡ Activities extracted: {stats.get('activities', {}).get('total', 0)}")
    print(f"  📦 Products extracted: {stats.get('products', {}).get('total', 0)}")
    print(f"  ⏱️  Processing time: {results.get('processing_metadata', {}).get('processing_time_seconds', 0):.2f} seconds")
    
    # Files generated
    print(f"\n📁 Generated Files:")
    output_files = results.get("output_files", {})
    for objective, filename in output_files.items():
        print(f"  📄 {objective.replace('_', ' ').title()}: {filename}")
    
    print(f"\n🎯 All RegGenome challenge deliverables generated successfully!")
    print("📖 Check the human-readable .md files for detailed analysis!")
    print("="*60 + "\n")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="RegGenome Deep Research Challenge - Complete AI Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reggenome_research.py "What is UCITS?"
  python reggenome_research.py "Analyze investment fund regulations" --output custom_output
  python reggenome_research.py "ESMA guidelines analysis" --mock
  
This system generates comprehensive regulatory intelligence reports including:
- Hierarchical tables of regulated entities, activities, and products
- Document relevance analysis with confidence scoring  
- Formal definition extraction with source document links
        """
    )
    
    parser.add_argument(
        "query",
        help="Research query to guide the regulatory analysis"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Output directory for generated files (default: 'output')"
    )
    
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Use mock data instead of real RegGenome API"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to custom configuration file"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model to use for analysis (default: gpt-4o-mini)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Print banner
    print_banner()
    
    # Display configuration
    print("🔍 RegGenome Deep Research")
    print(f"📋 Topic: {args.query}")
    print(f"💾 Output: {args.output}")
    print(f"🌐 API Mode: {'Mock' if args.mock else 'Real'}")
    if args.config:
        print(f"⚙️  Config: {args.config}")
    print("=" * 50)
    
    try:
        # Run the complete analysis
        start_time = datetime.now()
        
        print_progress_update("Initializing RegGenome Deep Research system...", "🚀")
        
        results = run_complete_analysis(
            query=args.query,
            output_dir=args.output,
            use_real_api=not args.mock,
            model_name=args.model,
            config_path=args.config
        )
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Update results with total execution time
        if isinstance(results, dict) and "processing_metadata" in results:
            results["processing_metadata"]["total_execution_time"] = total_time
        
        # Print success summary
        print_success_summary(results)
        
        # Additional file recommendations
        print("💡 Next Steps:")
        print("   1. Review the HUMAN_READABLE_SUMMARY_*.md for executive overview")
        print("   2. Examine TASK1_HIERARCHICAL_TABLE_*.md for objective 1")
        print("   3. Check TASK2_DOCUMENT_RELEVANCE_*.md for objective 2")
        print("   4. Explore TASK3_DEFINITION_LINKS_*.md for objective 3")
        print("   5. Read COMPREHENSIVE_REGGENOME_REPORT_*.md for full analysis")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Analysis interrupted by user")
        logger.info("Analysis interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 