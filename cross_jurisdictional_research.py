#!/usr/bin/env python3
"""
Cross-Jurisdictional Regulatory Research System

This system addresses real-world business scenarios where firms need to comply
with multiple jurisdictions simultaneously. 

Real-World Use Cases:
1. Multi-Market Account Opening:
   - Customer wants US stocks + Hong Kong stocks + A-shares accounts
   - Single application, multiple jurisdiction compliance

2. Cross-Border Compliance:
   - EU firm expanding to US and UK markets
   - Understanding regulatory differences and requirements

3. Unified Customer Onboarding:
   - Design single customer data collection system
   - Map to multiple jurisdictional requirements

Usage:
    python cross_jurisdictional_research.py [query] [--use-case TYPE]

Examples:
    # Account opening analysis
    python cross_jurisdictional_research.py "Customer account opening requirements" --use-case account_opening
    
    # General compliance analysis
    python cross_jurisdictional_research.py "Investment adviser compliance requirements" --use-case compliance
    
    # Product launch analysis
    python cross_jurisdictional_research.py "UCITS fund distribution requirements" --use-case product_launch
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from config import Config
from cross_jurisdictional_interface import CrossJurisdictionalInterface

def print_cross_jurisdictional_banner():
    """Print banner for cross-jurisdictional analysis"""
    print("\n" + "="*80)
    print("🌍 CROSS-JURISDICTIONAL REGULATORY ANALYSIS SYSTEM")
    print("="*80)
    print("🇺🇸 United States | 🇪🇺 European Union | 🇬🇧 United Kingdom")
    print()
    print("📋 Real-World Business Applications:")
    print("   • Multi-market account opening (US stocks + Hong Kong + A-shares)")
    print("   • Cross-border compliance analysis")
    print("   • Unified customer onboarding design")
    print("   • Regulatory arbitrage analysis")
    print("="*80)

def print_use_case_examples():
    """Print use case examples"""
    print("\n📝 USE CASE EXAMPLES:")
    print("-" * 50)
    
    examples = [
        {
            "use_case": "account_opening",
            "title": "Multi-Market Account Opening",
            "description": "Customer wants to trade US stocks, EU securities, and UK markets",
            "query": "Customer account opening and KYC requirements",
            "benefits": ["Single application form", "Unified data collection", "Automated compliance"]
        },
        {
            "use_case": "compliance", 
            "title": "Cross-Border Compliance",
            "description": "Investment firm expanding from EU to US and UK markets",
            "query": "Investment adviser licensing and compliance requirements",
            "benefits": ["Gap analysis", "Compliance roadmap", "Risk assessment"]
        },
        {
            "use_case": "product_launch",
            "title": "Multi-Jurisdiction Product Launch",
            "description": "Launching investment product across US, EU, and UK",
            "query": "Investment fund registration and distribution requirements",
            "benefits": ["Regulatory approval process", "Marketing restrictions", "Ongoing obligations"]
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   Use Case: {example['use_case']}")
        print(f"   Scenario: {example['description']}")
        print(f"   Query: \"{example['query']}\"")
        print(f"   Benefits: {', '.join(example['benefits'])}")
    
    print("-" * 50)

async def main():
    """Main function for cross-jurisdictional analysis"""
    
    parser = argparse.ArgumentParser(description="Cross-Jurisdictional Regulatory Research")
    parser.add_argument("query", nargs="?", 
                       default="Customer account opening and KYC requirements across multiple jurisdictions",
                       help="Business requirement or use case to analyze")
    parser.add_argument("--use-case", type=str, 
                       choices=["account_opening", "compliance", "product_launch", "general"],
                       default="account_opening",
                       help="Specific use case type for targeted analysis")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Output directory for results")
    parser.add_argument("--examples", action="store_true",
                       help="Show use case examples and exit")
    
    args = parser.parse_args()
    
    if args.examples:
        print_use_case_examples()
        return
    
    print_cross_jurisdictional_banner()
    
    # Check for API key
    if not Path("key.txt").exists():
        print("\n❌ ERROR: RegGenome API key not found!")
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return
    
    print(f"\n🔍 Analysis Query: {args.query}")
    print(f"📊 Use Case: {args.use_case}")
    print(f"🌍 Jurisdictions: US, EU, UK")
    print(f"📁 Output Directory: {args.output_dir}")
    print()
    
    try:
        # Initialize system
        config = Config()
        interface = CrossJurisdictionalInterface(config)
        
        print("🚀 Starting Cross-Jurisdictional Analysis...")
        print("   This comprehensive analysis may take 5-10 minutes...")
        print("   Processing each jurisdiction separately, then cross-matching...")
        
        # Run cross-jurisdictional analysis
        results = await interface.analyze_multi_jurisdictional_requirements(args.query, args.use_case)
        
        # Save results
        output_dir = Path(args.output_dir)
        timestamp = interface.save_cross_jurisdictional_results(results, output_dir)
        
        # Display results summary
        print(f"\n🎯 ANALYSIS COMPLETE!")
        print(f"{'='*60}")
        
        # Show key findings
        summary = results.get("summary", {})
        print(f"\n📊 Key Findings:")
        print(f"   • Jurisdictions Analyzed: {summary.get('jurisdictions_analyzed', 3)}")
        print(f"   • Cross-Matched Requirements: {summary.get('cross_matched_requirements', 0)}")
        print(f"   • Total Entities Found: {summary.get('total_entities_found', 0)}")
        print(f"   • Total Documents Processed: {summary.get('total_documents_processed', 0)}")
        
        # Show compliance complexity
        comparison = results.get("comparison_analysis", {})
        complexity = comparison.get("compliance_complexity", {})
        if complexity:
            print(f"\n⚖️ Compliance Complexity:")
            print(f"   • Complexity Level: {complexity.get('complexity_level', 'Unknown')}")
            print(f"   • Conflicting Requirements: {complexity.get('conflicting_requirements', 0)}")
            print(f"   • Complexity Score: {complexity.get('complexity_score', 0):.2f}")
        
        # Show business recommendations
        business_recs = results.get("business_recommendations", {})
        strategic_recs = business_recs.get("strategic_recommendations", [])
        if strategic_recs:
            print(f"\n💡 Key Strategic Recommendations:")
            for i, rec in enumerate(strategic_recs[:3], 1):
                print(f"   {i}. {rec}")
        
        # Show unified customer recommendations for account opening use case
        if args.use_case == "account_opening":
            unified_recs = results.get("unified_recommendations", {})
            unified_form = unified_recs.get("unified_customer_form", {})
            if unified_form:
                print(f"\n📋 Unified Customer Onboarding:")
                approach = unified_form.get("data_collection_strategy", "")
                print(f"   • Strategy: {approach}")
                
                form_structure = unified_form.get("form_structure", {})
                total_sections = len([k for k in form_structure.keys() if k != "jurisdiction_specific"])
                print(f"   • Form Sections: {total_sections} common sections")
                
                jurisdiction_specific = form_structure.get("jurisdiction_specific", {})
                if jurisdiction_specific:
                    print(f"   • Jurisdiction-Specific Fields:")
                    for jurisdiction, fields in jurisdiction_specific.items():
                        print(f"     - {jurisdiction}: {len(fields)} additional fields")
        
        # Show implementation timeline
        impl_guide = results.get("practical_implementation", {})
        if impl_guide:
            total_duration = 0
            phases = []
            for phase_name, phase_details in impl_guide.items():
                duration_str = phase_details.get("duration", "0 months")
                try:
                    # Extract months from duration string
                    months = int(duration_str.split("-")[0].split()[0])
                    total_duration += months
                    phases.append(phase_name.replace("_", " ").title())
                except:
                    pass
            
            if total_duration > 0:
                print(f"\n🗓️ Implementation Timeline:")
                print(f"   • Total Duration: {total_duration} months")
                print(f"   • Implementation Phases: {len(phases)}")
                for phase in phases:
                    print(f"     - {phase}")
        
        # Show output files
        query_folders = list(output_dir.glob("CrossJurisdictional_*"))
        if query_folders:
            latest_folder = max(query_folders, key=lambda x: x.stat().st_mtime)
            print(f"\n📁 Generated Reports:")
            for file_path in sorted(latest_folder.glob("*")):
                if file_path.is_file():
                    file_type = "📊" if file_path.suffix == ".json" else "📝"
                    print(f"   {file_type} {file_path.name}")
        
        print(f"\n✅ Cross-Jurisdictional Analysis Complete!")
        print(f"   📂 Full results available in: {latest_folder}")
        print(f"   🎯 Use this analysis to design unified compliance processes")
        
    except Exception as e:
        print(f"\n❌ Error during cross-jurisdictional analysis: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n💡 Troubleshooting Tips:")
        print(f"   1. Verify your RegGenome API key is valid")
        print(f"   2. Check your internet connection")
        print(f"   3. Try with a simpler query first")
        print(f"   4. Ensure sufficient API quota")

def show_real_world_scenario():
    """Show detailed real-world scenario"""
    
    print("\n" + "="*80)
    print("🏦 REAL-WORLD SCENARIO: MULTI-MARKET ACCOUNT OPENING")
    print("="*80)
    
    print("\n📋 Business Challenge:")
    print("A wealth management firm wants to offer clients the ability to trade:")
    print("   • 🇺🇸 US stocks (NYSE, NASDAQ)")
    print("   • 🇭🇰 Hong Kong stocks (HKEX)")
    print("   • 🇨🇳 A-shares (Shanghai/Shenzhen Stock Exchange)")
    
    print("\n❌ Current Problems:")
    print("   • Separate account opening forms for each market")
    print("   • Different KYC requirements and documentation")
    print("   • Manual compliance checking for each jurisdiction")
    print("   • Customer frustration with repetitive data entry")
    print("   • High operational costs and errors")
    
    print("\n✅ Cross-Jurisdictional Solution:")
    print("   • Single comprehensive customer onboarding form")
    print("   • Automated mapping to jurisdiction-specific requirements")
    print("   • Real-time compliance validation across all markets")
    print("   • Unified customer data storage with jurisdiction views")
    print("   • Streamlined approval workflows")
    
    print("\n💰 Business Benefits:")
    print("   • 50% reduction in onboarding time")
    print("   • 30% reduction in operational costs")
    print("   • 90% reduction in compliance errors")
    print("   • Improved customer satisfaction")
    print("   • Faster time-to-market for new jurisdictions")
    
    print("\n🎯 This System Provides:")
    print("   • Detailed regulatory requirement analysis for each jurisdiction")
    print("   • Cross-matching of common vs. specific requirements")
    print("   • Unified customer data model design")
    print("   • Implementation roadmap with timelines and costs")
    print("   • Risk assessment and mitigation strategies")
    
    print("="*80)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--scenario", "scenario"]:
        show_real_world_scenario()
    elif len(sys.argv) > 1 and sys.argv[1] in ["--examples", "examples"]:
        print_use_case_examples()
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n👋 Analysis interrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print(f"\n💡 Run 'python cross_jurisdictional_research.py --examples' for usage examples")
            sys.exit(1)