#!/usr/bin/env python3
"""
Business Insights Generator - Natural Language Only

This script provides pure business insights without any structured deliverables.
All analysis happens internally, output is conversational business intelligence.

Usage:
    python business_insights.py [query]
    
Examples:
    python business_insights.py "UK fund KYC requirements for US investors"
    python business_insights.py "Investment adviser compliance across jurisdictions"
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from business_insights_chat import BusinessInsightsChat

def print_insights_banner():
    """Print a clean banner for business insights"""
    print("\n" + "="*70)
    print("💡 REGGENOME BUSINESS INSIGHTS")
    print("="*70)
    print("Natural language regulatory intelligence for business decisions")
    print("="*70 + "\n")

async def generate_insights(query: str, cross_jurisdictional: bool = True, verbose: bool = False):
    """Generate business insights for a query"""
    
    if verbose:
        print_insights_banner()
    
    # Create insights generator
    insights_generator = BusinessInsightsChat()
    
    # Suppress print statements during analysis if not verbose
    if not verbose:
        # Temporarily redirect stdout
        import io
        import contextlib
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            insights = await insights_generator.analyze_and_extract_insights(query, cross_jurisdictional)
    else:
        insights = await insights_generator.analyze_and_extract_insights(query, cross_jurisdictional)
    
    return insights

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Generate natural language business insights from regulatory analysis"
    )
    parser.add_argument(
        "query", 
        nargs="?",
        default="What are the key regulatory requirements for a UK fund accepting US investors?",
        help="Your regulatory question or business scenario"
    )
    parser.add_argument(
        "--no-cross", 
        action="store_true",
        help="Skip cross-jurisdictional analysis"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show analysis progress"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show example queries and exit"
    )
    
    args = parser.parse_args()
    
    if args.examples:
        print("\n📝 EXAMPLE QUERIES FOR BUSINESS INSIGHTS:\n")
        examples = [
            "What are the compliance requirements for opening accounts across multiple jurisdictions?",
            "How should a UK fund structure KYC for international investors?",
            "What are the key differences in investment adviser regulations between US and EU?",
            "Explain the regulatory landscape for launching a multi-jurisdictional fund",
            "What compliance framework is needed for cross-border financial services?",
            "How do AML requirements differ between US, EU, and UK?",
            "What are the regulatory implications of Brexit for fund management?",
            "How can we streamline customer onboarding across jurisdictions?"
        ]
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example}")
        print()
        return
    
    # Check for API key
    if not Path("key.txt").exists():
        print("\n❌ ERROR: RegGenome API key not found!")
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return
    
    try:
        # Generate insights
        insights = await generate_insights(
            args.query, 
            cross_jurisdictional=not args.no_cross,
            verbose=args.verbose
        )
        
        # Print insights
        print(insights)
        
        # Add a footer with context
        print("\n" + "-"*70)
        print("📊 Analysis based on current regulatory documents from US, EU, and UK")
        print("📅 Generated:", Path(__file__).stat().st_mtime)
        print("⚠️  Always verify with current regulations and legal counsel")
        
    except Exception as e:
        print(f"\n❌ Error generating insights: {e}")
        print("\nTry a simpler query or check your API connection.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted.")
        sys.exit(0)