"""
Interactive CLI for Deep Research Multi-Agent System

Provides a user-friendly terminal interface for running regulatory research queries.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Optional

from src.config import Config
from src.deep_research_orchestrator import DeepResearchOrchestrator
from src.unified_interface import UnifiedResearchInterface
from src.terminal_formatter import format_for_terminal

class InteractiveCLI:
    """Interactive command-line interface for the research system"""
    
    def __init__(self):
        self.config = Config()
        self.orchestrator = DeepResearchOrchestrator(self.config)
        self.unified_interface = UnifiedResearchInterface(self.config)
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        self.mode = "task1"  # Default mode
        
    def print_banner(self):
        """Display welcome banner"""
        print("\n" + "=" * 80)
        print(format_for_terminal("# DEEP RESEARCH MULTI-AGENT SYSTEM - INTERACTIVE MODE"))
        print("=" * 80)
        print("\nWelcome to the RegGenome Deep Research System!")
        print("This system extracts regulated entities, activities, and products from")
        print("regulatory documents using advanced multi-agent architecture.")
        print("\nType 'help' for available commands or enter your research query.")
        print("=" * 80 + "\n")
        
    def print_help(self):
        """Display help information"""
        print(format_for_terminal("\n## AVAILABLE COMMANDS:"))
        print("-" * 40)
        print("  help           - Show this help message")
        print("  examples       - Show example queries")
        print("  config         - View current configuration")
        print("  initiatives    - List available regulatory initiatives")
        print("  history        - Show recent research queries")
        print("  mode           - Switch between task modes (task1, all)")
        print("  clear          - Clear the screen")
        print("  exit/quit      - Exit the program")
        print(format_for_terminal("\n## RESEARCH MODES:"))
        print(f"  task1  - Extract regulated items only (current: {'[x]' if self.mode == 'task1' else '[ ]'})")
        print(f"  all    - Run all 3 tasks comprehensively (current: {'[x]' if self.mode == 'all' else '[ ]'})")
        print(format_for_terminal("\n## TO RUN RESEARCH:"))
        print("  Simply type your query and press Enter")
        print("  Example: What are the compliance requirements for UCITS funds?")
        print("-" * 40 + "\n")
        
    def print_examples(self):
        """Display example queries"""
        print(format_for_terminal("\n## EXAMPLE QUERIES:"))
        print("-" * 40)
        examples = [
            "What are the main regulated entities in UCITS directives?",
            "How does a UK fund conduct CDD & KYC with EU and UK regulators?",
            "What are the compliance requirements for investment advisers?",
            "List the distribution and marketing activities for mutual funds",
            "What are the depositary requirements for UCITS funds?",
            "Investment company portfolio management restrictions",
            "Cross-border fund distribution requirements post-Brexit"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
        print("-" * 40 + "\n")
        
    def print_config(self):
        """Display current configuration"""
        print(format_for_terminal("\n## CURRENT CONFIGURATION:"))
        print("-" * 40)
        print(f"  API Base URL: {self.config.api_base_url}")
        print(f"  Max Pages per Query: {self.config.max_pages_per_query}")
        print(f"  Page Size: {self.config.page_size}")
        print(f"  Concurrent Agents: {self.config.concurrent_agents}")
        print(f"  Output Directory: {self.output_dir}")
        print("\n  Regulatory Initiatives:")
        for key, name in self.config.initiative_filters.items():
            print(f"    • {name}")
        print("-" * 40 + "\n")
        
    def print_initiatives(self):
        """Display available initiatives"""
        print(format_for_terminal("\n## REGULATORY INITIATIVES IN SCOPE:"))
        print("-" * 40)
        initiatives = [
            ("US Investment Advisers Act (1940)", "Regulations for investment advisory services"),
            ("US Investment Company Act (1940)", "Rules governing mutual funds and investment companies"),
            ("EU UCITS Directives", "Harmonized framework for collective investment schemes"),
            ("UK UCITS Regulations (2011-2016)", "UK implementation of UCITS framework")
        ]
        
        for name, desc in initiatives:
            print(f"\n  • {name}")
            print(f"    {desc}")
        print("-" * 40 + "\n")
        
    def show_history(self):
        """Display recent research queries"""
        print(format_for_terminal("\n## RECENT RESEARCH HISTORY:"))
        print("-" * 40)
        
        # Find recent output files
        json_files = sorted(self.output_dir.glob("task1_hierarchical_table_*.json"), 
                          key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        
        if not json_files:
            print("  No previous research found.")
        else:
            for i, file in enumerate(json_files, 1):
                # Extract timestamp from filename
                timestamp = file.stem.split("_")[-2] + "_" + file.stem.split("_")[-1]
                
                # Try to read query from file
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        query = data.get('summary', {}).get('query', 'Unknown query')
                        if not query or query == 'Unknown query':
                            # Try extraction metadata
                            query = "Research query not recorded"
                except:
                    query = "Unable to read query"
                
                print(f"  {i}. [{timestamp}] {query[:60]}...")
                
        print("-" * 40 + "\n")
        
    def clear_screen(self):
        """Clear the terminal screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        self.print_banner()
        
    def switch_mode(self):
        """Switch between research modes"""
        print(format_for_terminal("\n## SELECT RESEARCH MODE:"))
        print("-" * 40)
        print("  1. Task 1 only - Extract regulated items (faster)")
        print("  2. All tasks - Comprehensive analysis (slower)")
        print("-" * 40)
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            self.mode = "task1"
            print(format_for_terminal("**Switched to Task 1 mode (extract regulated items only)**"))
        elif choice == "2":
            self.mode = "all"
            print(format_for_terminal("**Switched to ALL tasks mode (comprehensive analysis)**"))
        else:
            print(format_for_terminal("**Invalid choice. Mode unchanged.**"))
        
        print(f"Current mode: {self.mode.upper()}")
        
    async def run_research(self, query: str):
        """Execute research for the given query"""
        print(format_for_terminal(f"\n## Starting research for: '{query}'"))
        print(format_for_terminal(f"**Mode:** {self.mode.upper()}"))
        print("-" * 80)
        
        try:
            if self.mode == "all":
                # Run all three tasks
                results = await self.unified_interface.run_all_tasks(query)
                timestamp = self.unified_interface.save_results(results, self.output_dir)
                
                print(format_for_terminal(f"\n**Comprehensive research complete!**"))
                print(f"   All results saved with timestamp: {timestamp}")
                
            else:
                # Original Task 1 only mode
                print(format_for_terminal("## Progress:"))
                print("  - Initializing agents...")
                
                # Run the research
                result = await self.orchestrator.research(query)
                
                # Generate outputs
                print("  - Generating hierarchical table...")
                table = self.orchestrator.generate_hierarchical_table(result)
                
                # Add query to summary for history
                table['summary']['query'] = query
                
                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                json_path = self.output_dir / f"task1_hierarchical_table_{timestamp}.json"
                with open(json_path, "w") as f:
                    json.dump(table, f, indent=2, default=str)
                
                txt_path = self.output_dir / f"task1_summary_{timestamp}.txt"
                with open(txt_path, "w") as f:
                    f.write(self.generate_summary_report(query, table, result))
                
                print("  - Results saved to output directory")
                
                # Display results summary
                print(format_for_terminal("\n## RESULTS SUMMARY:"))
                print("-" * 40)
                print(f"  Documents Processed: {result.total_documents_processed}")
                print(f"  Entities Found: {len(result.entities)}")
                print(f"  Activities Found: {len(result.activities)}")
                print(f"  Products Found: {len(result.products)}")
                print(f"  Total Unique Items: {len(result.entities) + len(result.activities) + len(result.products)}")
                
                # Show top findings
                print(format_for_terminal("\n## TOP FINDINGS:"))
                
                if result.entities:
                    print("\n  Entities:")
                    for entity in result.entities[:3]:
                        print(f"    • {entity.name} ({entity.entity_type.value})")
                        
                if result.activities:
                    print("\n  Activities:")
                    for activity in result.activities[:3]:
                        print(f"    • {activity.name} ({activity.activity_type.value})")
                        
                if result.products:
                    print("\n  Products:")
                    for product in result.products[:3]:
                        print(f"    • {product.name} ({product.product_type.value})")
                
                print(format_for_terminal(f"\n**Research complete!** Full results saved to:"))
                print(f"   • {json_path.name} (structured data)")
                print(f"   • {txt_path.name} (human-readable)")
            
        except Exception as e:
            print(format_for_terminal(f"\n**Error during research:** {e}"))
            print("   Please check your API key and network connection.")
            
    def generate_summary_report(self, query: str, table: dict, result) -> str:
        """Generate human-readable summary report"""
        report = []
        
        report.append("DEEP RESEARCH MULTI-AGENT SYSTEM - RESEARCH REPORT")
        report.append("=" * 80)
        report.append(f"\nQuery: {query}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Documents Processed: {result.total_documents_processed}")
        
        # Add sections for entities, activities, and products
        sections = [
            ("REGULATED ENTITIES", table["regulated_entities"]),
            ("REGULATED ACTIVITIES", table["regulated_activities"]),
            ("REGULATED PRODUCTS", table["regulated_products"])
        ]
        
        for section_name, items in sections:
            report.append(f"\n\n{section_name}")
            report.append("-" * 40)
            
            for item_group in items:
                report.append(f"\n{item_group['type'].upper()} ({item_group['count']} found):")
                
                for item in item_group["items"][:5]:  # Top 5
                    report.append(f"\n  • {item['name']}")
                    report.append(f"    {item['description']}")
                    report.append(f"    Confidence: {item['confidence']:.2f}")
                    
                    # Add type-specific details
                    if 'jurisdiction' in item and item['jurisdiction']:
                        report.append(f"    Jurisdiction: {item['jurisdiction']}")
                    if 'applicable_entities' in item and item['applicable_entities']:
                        report.append(f"    Applies to: {', '.join(item['applicable_entities'][:3])}")
                    if 'asset_classes' in item and item['asset_classes']:
                        report.append(f"    Asset classes: {', '.join(item['asset_classes'])}")
        
        # Statistics
        report.append("\n\nSTATISTICS")
        report.append("-" * 40)
        stats = result.extraction_metadata["statistics"]
        report.append(f"Total items extracted: {stats['total_entities_extracted'] + stats['total_activities_extracted'] + stats['total_products_extracted']}")
        report.append(f"After deduplication: {stats['unique_entities'] + stats['unique_activities'] + stats['unique_products']}")
        report.append(f"Deduplication ratio: {stats['deduplication_ratio']:.1%}")
        
        return "\n".join(report)
    
    async def run(self):
        """Main interactive loop"""
        self.print_banner()
        
        while True:
            try:
                # Get user input
                user_input = input("\nuser: Enter query (or command): ").strip()
                
                if not user_input:
                    continue
                    
                # Process commands
                command = user_input.lower()
                
                if command in ['exit', 'quit', 'q']:
                    print(format_for_terminal("\n**Thank you for using the Deep Research System. Goodbye!**"))
                    break
                    
                elif command == 'help':
                    self.print_help()
                    
                elif command == 'examples':
                    self.print_examples()
                    
                elif command == 'config':
                    self.print_config()
                    
                elif command == 'initiatives':
                    self.print_initiatives()
                    
                elif command == 'history':
                    self.show_history()
                    
                elif command == 'clear':
                    self.clear_screen()
                    
                elif command == 'mode':
                    self.switch_mode()
                    
                else:
                    # Treat as research query
                    await self.run_research(user_input)
                    
            except KeyboardInterrupt:
                print(format_for_terminal("\n\n**Interrupted.** Type 'exit' to quit or continue with a new query."))
                
            except Exception as e:
                print(format_for_terminal(f"\n**Unexpected error:** {e}"))
                print("   Please try again or type 'help' for assistance.")

async def main():
    """Entry point for interactive CLI"""
    # Check for API key
    if not Path("key.txt").exists():
        print(format_for_terminal("\n**ERROR:** API key not found!"))
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return
        
    cli = InteractiveCLI()
    await cli.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(format_for_terminal("\n\n**Goodbye!**"))
        sys.exit(0)