#!/usr/bin/env python3
"""
RegGenome Deep Research Multi-agent System

Main entry point for running the deep research workflow to identify regulated
activities, entities, and products from regulatory documents.

Usage:
    python main.py --help                    # Show help
    python main.py --mock                    # Run with mock data (no API key needed)
    python main.py --config config.env       # Specify custom config file
    python main.py --output results.json     # Specify output file
"""

import asyncio
import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import config
from src.deep_research_orchestrator import DeepResearchOrchestrator, run_deep_research


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging configuration."""
    
    # Configure log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def validate_configuration():
    """Validate configuration and return validation errors."""
    errors = config.validate_config()
    return errors


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RegGenome Deep Research Multi-agent System                ║
║                                                                              ║
║   Automated extraction of regulated activities, entities, and products      ║
║   from regulatory documents using AI-powered deep research agents           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def run_research_workflow(args):
    """Run the research workflow with the provided arguments."""
    
    # Validate configuration if not using mock API
    if not args.mock:
        validation_errors = validate_configuration()
        if validation_errors:
            print("❌ Configuration validation failed:")
            for error in validation_errors:
                print(f"   • {error}")
            print("\nPlease check your configuration and try again.")
            return 1
    
    try:
        # Create orchestrator
        orchestrator = DeepResearchOrchestrator(use_mock_api=args.mock)
        
        print(f"🔍 Starting deep research workflow...")
        if args.mock:
            print("🧪 Using mock API for demonstration")
        
        # Run the research
        taxonomy = await orchestrator.run_research(
            query=args.query,
            save_results=True,
            output_file=args.output
        )
        
        # Print summary statistics
        stats = orchestrator.get_summary_statistics()
        print("\n" + "="*80)
        print("📊 RESEARCH RESULTS SUMMARY")
        print("="*80)
        
        print(f"📋 Query: {stats['query']}")
        print(f"📄 Documents processed: {stats['totals']['documents']}")
        print(f"🏢 Entities extracted: {stats['totals']['entities']}")
        print(f"⚡ Activities extracted: {stats['totals']['activities']}")
        print(f"📦 Products extracted: {stats['totals']['products']}")
        
        # Print breakdown by type
        if stats['entity_breakdown']:
            print("\n🏢 Entity Breakdown:")
            for entity_type, count in stats['entity_breakdown'].items():
                print(f"   • {entity_type}: {count}")
        
        if stats['activity_breakdown']:
            print("\n⚡ Activity Breakdown:")
            for activity_type, count in stats['activity_breakdown'].items():
                print(f"   • {activity_type}: {count}")
        
        if stats['product_breakdown']:
            print("\n📦 Product Breakdown:")
            for product_type, count in stats['product_breakdown'].items():
                print(f"   • {product_type}: {count}")
        
        # Print errors and warnings
        if stats['errors']:
            print(f"\n⚠️  Errors ({len(stats['errors'])}):")
            for error in stats['errors']:
                print(f"   • {error}")
        
        if stats['warnings']:
            print(f"\n⚠️  Warnings ({len(stats['warnings'])}):")
            for warning in stats['warnings']:
                print(f"   • {warning}")
        
        # Create and save hierarchical table (Task 1 deliverable)
        if args.table_output:
            print(f"\n📋 Creating hierarchical table...")
            hierarchical_table = await orchestrator.create_hierarchical_table()
            
            with open(args.table_output, 'w', encoding='utf-8') as f:
                json.dump(hierarchical_table, f, indent=2, default=str)
            
            print(f"✅ Hierarchical table saved to: {args.table_output}")
        
        print(f"\n✅ Research completed successfully!")
        if args.output:
            print(f"📁 Full results saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Research workflow failed: {e}")
        logging.exception("Detailed error information:")
        return 1


def parse_arguments():
    """Parse command line arguments."""
    
    parser = argparse.ArgumentParser(
        description="RegGenome Deep Research Multi-agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mock                                 # Demo with mock data
  python main.py --output my_results.json              # Save to specific file
  python main.py --table-output task1_table.json       # Create Task 1 table
  python main.py --query "UCITS regulations"           # Custom research query
  python main.py --log-level DEBUG --log-file debug.log # Detailed logging
        """
    )
    
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock API client (no API key required, for testing)"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        default="Identify regulated activities, entities, and products",
        help="Research query to guide the analysis"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for complete results (default: auto-generated)"
    )
    
    parser.add_argument(
        "--table-output",
        type=str,
        default="regulatory_hierarchy_table.json",
        help="Output file for hierarchical table (Task 1 deliverable)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: .env)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path (default: console only)"
    )
    
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Skip printing the banner"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    
    # Parse arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(
        log_level=args.log_level,
        log_file=args.log_file or config.logging.log_file
    )
    
    # Print banner
    if not args.no_banner:
        print_banner()
    
    # Load custom config if specified
    if args.config:
        import os
        from dotenv import load_dotenv
        
        if not os.path.exists(args.config):
            print(f"❌ Configuration file not found: {args.config}")
            return 1
        
        load_dotenv(args.config, override=True)
        print(f"📁 Loaded configuration from: {args.config}")
    
    # Run the research workflow
    return await run_research_workflow(args)


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
        logging.exception("Unexpected error details:")
        sys.exit(1) 