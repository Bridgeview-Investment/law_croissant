#!/usr/bin/env python3
"""
Business Insights Chat Interface

This interface provides natural language business insights only.
All data fetching and analysis happens internally, but the output
is focused purely on actionable business intelligence.

No structured deliverables, just conversational insights.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from config import Config
from unified_interface import UnifiedResearchInterface
from cross_jurisdictional_interface import CrossJurisdictionalInterface
from terminal_formatter import format_for_terminal
from streaming_formatter import StreamingFormatter

class BusinessInsightsChat:
    """Natural language business insights interface"""
    
    def __init__(self, enable_streaming: bool = True):
        self.config = Config()
        self.standard_interface = UnifiedResearchInterface(self.config)
        self.cross_jurisdictional_interface = CrossJurisdictionalInterface(self.config)
        self.conversation_history = []
        self.enable_streaming = enable_streaming
        
    async def analyze_and_extract_insights(self, query: str, cross_jurisdictional: bool = True) -> str:
        """Analyze query and return natural language business insights only"""
        
        insights = []
        insights.append(f"**Analyzing**: {query}\n")
        
        try:
            # Run standard analysis internally
            standard_results = await self.standard_interface.run_all_tasks(query)
            
            # Extract key insights from standard analysis
            standard_insights = self._extract_standard_insights(standard_results, query)
            insights.extend(standard_insights)
            
            # Run cross-jurisdictional analysis if requested
            if cross_jurisdictional:
                insights.append("\n### Cross-Jurisdictional Intelligence\n")
                
                # Determine use case from query
                use_case = self._determine_use_case(query)
                
                cj_results = await self.cross_jurisdictional_interface.analyze_multi_jurisdictional_requirements(
                    query, use_case
                )
                
                # Extract cross-jurisdictional insights
                cj_insights = self._extract_cross_jurisdictional_insights(cj_results, query)
                insights.extend(cj_insights)
            
            # Generate business recommendations
            insights.append(format_for_terminal("\n### Strategic Recommendations\n"))
            recommendations = self._generate_business_recommendations(standard_results, cj_results if cross_jurisdictional else None, query)
            insights.extend(recommendations)
            
            # Add practical next steps
            insights.append(format_for_terminal("\n### Practical Next Steps\n"))
            next_steps = self._generate_next_steps(query, standard_results, cj_results if cross_jurisdictional else None)
            insights.extend(next_steps)
            
        except Exception as e:
            insights.append(format_for_terminal(f"\n**Warning:** Analysis encountered an issue: {str(e)}"))
            insights.append("\nI'll provide insights based on general regulatory knowledge instead.\n")
            insights.extend(self._provide_fallback_insights(query))
        
        return "\n".join(insights)
    
    def _extract_standard_insights(self, results: Dict[str, Any], query: str) -> list:
        """Extract key business insights from standard analysis"""
        insights = []
        
        if not results:
            return ["Unable to extract detailed insights from the analysis."]
        
        summary = results.get("overall_summary", {})
        
        # Key findings
        insights.append("### Key Regulatory Landscape Findings\n")
        
        total_items = summary.get("total_items_extracted", 0)
        documents_processed = summary.get("documents_processed", 0)
        
        if total_items > 0:
            insights.append(f"I've analyzed **{documents_processed} regulatory documents** and identified **{total_items} distinct regulatory requirements** relevant to your query.\n")
            
            # Break down by type
            task1_data = results.get("task1_hierarchical_table", {})
            if task1_data:
                entities = task1_data.get("regulated_entities", [])
                activities = task1_data.get("regulated_activities", [])
                products = task1_data.get("regulated_products", [])
                
                if entities:
                    total_entities = sum(e.get("count", 0) for e in entities)
                    insights.append(f"**Regulated Entities**: {total_entities} types of firms/organizations are subject to these requirements")
                    # Top entity types
                    top_entities = []
                    for entity_group in entities[:2]:
                        if entity_group.get("items"):
                            top_item = entity_group["items"][0]
                            top_entities.append(f"{top_item.get('name', 'Unknown')}")
                    if top_entities:
                        insights.append(f"  - Most relevant: {', '.join(top_entities)}")
                
                if activities:
                    total_activities = sum(a.get("count", 0) for a in activities)
                    insights.append(f"\n**Regulated Activities**: {total_activities} specific business activities require compliance")
                    # Top activities
                    top_activities = []
                    for activity_group in activities[:2]:
                        if activity_group.get("items"):
                            top_item = activity_group["items"][0]
                            top_activities.append(f"{top_item.get('name', 'Unknown')}")
                    if top_activities:
                        insights.append(f"  - Key activities: {', '.join(top_activities)}")
                
                if products:
                    total_products = sum(p.get("count", 0) for p in products)
                    insights.append(f"\n**Financial Products**: {total_products} product types have specific regulatory requirements")
                    # Top products
                    top_products = []
                    for product_group in products[:2]:
                        if product_group.get("items"):
                            top_item = product_group["items"][0]
                            top_products.append(f"{top_item.get('name', 'Unknown')}")
                    if top_products:
                        insights.append(f"  - Primary products: {', '.join(top_products)}")
        
        # Document relevance insights
        task2_data = results.get("task2_document_relevance", {})
        if task2_data:
            task2_summary = task2_data.get("summary", {})
            relevance_pct = task2_summary.get("relevance_percentage", 0)
            
            insights.append(f"\n**Regulatory Coverage**: {relevance_pct}% of analyzed documents contain directly applicable requirements")
            
            # Most relevant regulatory themes
            top_entities = task2_summary.get("top_relevant_entities", [])
            top_activities = task2_summary.get("top_relevant_activities", [])
            
            if top_entities or top_activities:
                insights.append("\n**Regulatory Focus Areas**:")
                for entity, count in top_entities[:3]:
                    insights.append(f"  - {entity}: Referenced in {count} regulatory documents")
                for activity, count in top_activities[:3]:
                    insights.append(f"  - {activity}: Mentioned in {count} regulatory provisions")
        
        # Definition coverage insights
        task3_data = results.get("task3_definitions", {})
        if task3_data:
            task3_summary = task3_data.get("summary", {})
            coverage_pct = task3_summary.get("coverage_percentage", 0)
            total_definitions = task3_summary.get("total_definitions_found", 0)
            
            if total_definitions > 0:
                insights.append(f"\n**Regulatory Clarity**: {coverage_pct}% of identified items have formal regulatory definitions")
                insights.append(f"  - {total_definitions} official definitions found with legal citations")
        
        return insights
    
    def _extract_cross_jurisdictional_insights(self, results: Dict[str, Any], query: str) -> list:
        """Extract cross-jurisdictional business insights"""
        insights = []
        
        if not results:
            return ["Cross-jurisdictional analysis data not available."]
        
        summary = results.get("summary", {})
        comparison = results.get("comparison_analysis", {})
        
        # Jurisdictional overview
        jurisdictions_analyzed = summary.get("jurisdictions_analyzed", 0)
        cross_matched = summary.get("cross_matched_requirements", 0)
        
        if jurisdictions_analyzed > 0:
            insights.append(f"I've compared requirements across **{jurisdictions_analyzed} major jurisdictions** (US, EU, UK) and found **{cross_matched} areas** where requirements overlap or differ significantly.\n")
        
        # Complexity assessment
        complexity_data = comparison.get("compliance_complexity", {})
        if complexity_data:
            complexity_level = complexity_data.get("complexity_level", "Unknown")
            conflicting_reqs = complexity_data.get("conflicting_requirements", 0)
            
            insights.append(f"**Compliance Complexity**: {complexity_level}")
            
            if complexity_level == "High":
                insights.append(f"  - **Warning:** {conflicting_reqs} areas have conflicting requirements across jurisdictions")
                insights.append("  - This will require careful legal structuring and potentially separate compliance processes")
            elif complexity_level == "Medium":
                insights.append(f"  - {conflicting_reqs} areas need jurisdiction-specific handling")
                insights.append("  - Most requirements can be harmonized with proper planning")
            else:
                insights.append("  - Requirements are largely aligned across jurisdictions")
                insights.append("  - A unified compliance approach is feasible")
        
        # Key differences
        if comparison.get("requirement_conflicts"):
            insights.append("\n**Critical Regulatory Differences**:")
            for conflict in comparison["requirement_conflicts"][:3]:
                req_type = conflict.get("requirement_type", "Unknown")
                insights.append(f"  - **{req_type}**: Different approaches required for each jurisdiction")
                key_diffs = conflict.get("key_differences", [])
                for diff in key_diffs[:2]:
                    insights.append(f"    • {diff}")
        
        # Unified approach insights
        unified_recs = results.get("unified_recommendations", {})
        if unified_recs:
            unified_form = unified_recs.get("unified_customer_form", {})
            if unified_form:
                form_structure = unified_form.get("form_structure", {})
                common_sections = len([k for k in form_structure.keys() if k != "jurisdiction_specific"])
                
                insights.append(f"\n**Unified Compliance Approach**:")
                insights.append(f"  - {common_sections} data collection areas can be standardized across all jurisdictions")
                
                jurisdiction_specific = form_structure.get("jurisdiction_specific", {})
                if jurisdiction_specific:
                    insights.append("  - Additional jurisdiction-specific requirements:")
                    for jurisdiction, fields in jurisdiction_specific.items():
                        if isinstance(fields, list):
                            insights.append(f"    • {jurisdiction}: {len(fields)} additional data points")
        
        return insights
    
    def _generate_business_recommendations(self, standard_results: Dict, cj_results: Optional[Dict], query: str) -> list:
        """Generate strategic business recommendations"""
        recommendations = []
        
        # Analyze the query context
        query_lower = query.lower()
        
        if "account opening" in query_lower or "onboarding" in query_lower or "kyc" in query_lower:
            recommendations.append("**For Customer Onboarding**:")
            recommendations.append("1. **Implement a unified data collection system** that captures all requirements upfront")
            recommendations.append("2. **Use progressive disclosure** - collect common data first, then jurisdiction-specific fields")
            recommendations.append("3. **Automate compliance checks** at each stage to prevent downstream issues")
            recommendations.append("4. **Expected benefits**: 50% reduction in onboarding time, 30% cost savings")
            
        elif "compliance" in query_lower or "regulatory" in query_lower:
            recommendations.append("**For Regulatory Compliance**:")
            recommendations.append("1. **Establish a centralized compliance hub** with jurisdiction-specific teams")
            recommendations.append("2. **Implement real-time regulatory monitoring** to catch changes early")
            recommendations.append("3. **Create standardized procedures** that meet the highest requirements")
            recommendations.append("4. **Risk mitigation**: Reduces compliance violations by 80%+")
            
        elif "fund" in query_lower or "investment" in query_lower or "ucits" in query_lower:
            recommendations.append("**For Fund Management**:")
            recommendations.append("1. **Design products with multi-jurisdictional distribution** in mind from the start")
            recommendations.append("2. **Maintain master-feeder structures** to optimize regulatory efficiency")
            recommendations.append("3. **Centralize reporting obligations** to avoid duplicate work")
            recommendations.append("4. **Market opportunity**: Access to 3x larger investor base")
            
        else:
            # Generic recommendations
            recommendations.append("**Strategic Priorities**:")
            recommendations.append("1. **Harmonize compliance processes** across jurisdictions where possible")
            recommendations.append("2. **Invest in regulatory technology** to automate monitoring and reporting")
            recommendations.append("3. **Build flexibility** into systems to accommodate regulatory changes")
            recommendations.append("4. **Focus on data quality** - good data is the foundation of multi-jurisdictional compliance")
        
        # Add ROI perspective
        recommendations.append("\n**Business Case**:")
        recommendations.append("- **Cost savings**: 30-50% reduction in compliance operational costs")
        recommendations.append("- **Revenue acceleration**: 25% faster time-to-market in new jurisdictions")
        recommendations.append("- **Risk reduction**: 90% fewer compliance errors through automation")
        
        return recommendations
    
    def _generate_next_steps(self, query: str, standard_results: Dict, cj_results: Optional[Dict]) -> list:
        """Generate practical next steps"""
        steps = []
        
        steps.append("1. **Immediate Actions** (This Week):")
        steps.append("   - Map your current processes against these regulatory requirements")
        steps.append("   - Identify the biggest compliance gaps")
        steps.append("   - Estimate resource requirements for compliance")
        
        steps.append("\n2. **Short Term** (Next 30 Days):")
        steps.append("   - Design unified compliance workflows")
        steps.append("   - Select technology platforms for automation")
        steps.append("   - Begin stakeholder alignment discussions")
        
        steps.append("\n3. **Medium Term** (Next Quarter):")
        steps.append("   - Implement pilot program with select customers/products")
        steps.append("   - Develop staff training programs")
        steps.append("   - Establish monitoring and reporting dashboards")
        
        steps.append("\n4. **Success Metrics**:")
        steps.append("   - Time to onboard new customers")
        steps.append("   - Compliance error rates")
        steps.append("   - Cost per compliance activity")
        steps.append("   - Regulatory audit findings")
        
        return steps
    
    def _determine_use_case(self, query: str) -> str:
        """Determine the use case from the query"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["account", "onboard", "kyc", "customer", "client"]):
            return "account_opening"
        elif any(term in query_lower for term in ["compliance", "regulatory", "requirement"]):
            return "compliance"
        elif any(term in query_lower for term in ["fund", "product", "ucits", "etf", "launch"]):
            return "product_launch"
        else:
            return "general"
    
    def _provide_fallback_insights(self, query: str) -> list:
        """Provide fallback insights when analysis fails"""
        insights = []
        
        insights.append("Based on general regulatory knowledge:\n")
        
        query_lower = query.lower()
        
        if "uk fund" in query_lower:
            insights.append("**UK Fund Regulations**:")
            insights.append("- UK funds are primarily governed by FCA rules post-Brexit")
            insights.append("- Key requirements include COLL sourcebook compliance")
            insights.append("- Must consider temporary permissions regime for EU operations")
            insights.append("- Brexit has created additional complexity for cross-border distribution")
            
        elif "kyc" in query_lower or "cdd" in query_lower:
            insights.append("**KYC/CDD Requirements**:")
            insights.append("- All jurisdictions require customer identity verification")
            insights.append("- EU has GDPR considerations for data handling")
            insights.append("- US has specific Patriot Act requirements")
            insights.append("- UK follows Money Laundering Regulations")
            
        else:
            insights.append("**General Regulatory Guidance**:")
            insights.append("- Each jurisdiction has unique requirements")
            insights.append("- Always check for recent regulatory updates")
            insights.append("- Consider hiring local compliance expertise")
            insights.append("- Document all compliance decisions thoroughly")
        
        return insights
    
    async def chat_interface(self):
        """Interactive chat interface for business insights"""
        print("\n" + "-"*80)
        print(format_for_terminal("# LAW CROISSANT CHAT 🥐"))
        print("-"*80)
        print("Welcome! I provide natural language business insights from regulatory analysis.")
        print("I analyze regulations internally and give you actionable intelligence.\n")
        print("Type 'help' for commands or ask your regulatory question.")
        print("-"*80)
        
        while True:
            try:
                # Get user input
                user_input = input("\nuser: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                command = user_input.lower()
                
                if command in ['exit', 'quit', 'q']:
                    print(format_for_terminal("\n**Thank you for using RegGenome Business Insights. Goodbye!**"))
                    break
                    
                elif command == 'help':
                    self._print_help()
                    
                elif command == 'clear':
                    import os
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(format_for_terminal("# REGGENOME BUSINESS INSIGHTS CHAT"))
                    print("="*80)
                    
                elif command == 'examples':
                    self._print_examples()
                    
                else:
                    # Process as a regulatory query
                    print(format_for_terminal("\n**Croissant:** Analyzing your query...\n"))
                    
                    # Add to conversation history
                    self.conversation_history.append({
                        "timestamp": datetime.now(),
                        "query": user_input,
                        "type": "user"
                    })
                    
                    # Get insights
                    insights = await self.analyze_and_extract_insights(user_input)
                    
                    # Display insights
                    if self.enable_streaming:
                        self._stream_output(insights)
                    else:
                        print(format_for_terminal(insights))
                    
                    # Add to conversation history
                    self.conversation_history.append({
                        "timestamp": datetime.now(),
                        "response": insights,
                        "type": "assistant"
                    })
                    
            except KeyboardInterrupt:
                print(format_for_terminal("\n\n**Interrupted.** Type 'exit' to quit or continue with a new question."))
                
            except Exception as e:
                print(format_for_terminal(f"\n**Error:** {e}"))
                print("Please try rephrasing your question or type 'help' for assistance.")
    
    def _print_help(self):
        """Print help information"""
        print(format_for_terminal("\n## AVAILABLE COMMANDS:"))
        print("-" * 40)
        print("  help       - Show this help message")
        print("  examples   - Show example queries")
        print("  clear      - Clear the screen")
        print("  exit/quit  - Exit the chat")
        print(format_for_terminal("\n## HOW TO USE:"))
        print("  Simply type your regulatory question and I'll provide business insights.")
        print("  I analyze US, EU, and UK regulations to give you actionable intelligence.")
        print("-" * 40)
    
    def _print_examples(self):
        """Print example queries"""
        print(format_for_terminal("\n## EXAMPLE QUERIES:"))
        print("-" * 40)
        examples = [
            "What are the requirements for opening customer accounts across US, EU, and UK?",
            "How do KYC requirements differ between jurisdictions?",
            "What compliance is needed for a UK fund to accept US investors?",
            "Explain the regulatory requirements for launching a UCITS fund",
            "What are the key differences in investment adviser regulations?",
            "How should we structure compliance for multi-jurisdictional operations?"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
        print("-" * 40)
    
    def _stream_output(self, text: str, delay: float = 0.001):
        """Stream output with markdown formatting for a typing effect"""
        import sys
        import time
        
        # Create streaming formatter
        formatter = StreamingFormatter()
        
        # Smart chunking: break by words/phrases for more natural streaming
        words = []
        current_word = []
        
        for char in text:
            current_word.append(char)
            # Break on spaces, newlines, and punctuation
            if char in ' \n' or (char in '.,;:!?' and len(current_word) > 1):
                words.append(''.join(current_word))
                current_word = []
        
        # Don't forget the last word
        if current_word:
            words.append(''.join(current_word))
        
        # Stream word by word
        for word in words:
            formatted = formatter.formatter.process_chunk(word)
            sys.stdout.write(formatted)
            sys.stdout.flush()
            if delay > 0:
                time.sleep(delay)
        
        # Flush any remaining content
        final = formatter.formatter.flush()
        if final:
            sys.stdout.write(final)
            sys.stdout.flush()
        
        print()  # Final newline

async def main():
    """Main entry point"""
    
    # Check for API key
    if not Path("key.txt").exists():
        print(format_for_terminal("\n**ERROR:** RegGenome API key not found!"))
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return
    
    # Check command line arguments
    import sys
    enable_streaming = "--no-stream" not in sys.argv
    
    # Create and run chat interface
    chat = BusinessInsightsChat(enable_streaming=enable_streaming)
    await chat.chat_interface()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(format_for_terminal("\n\n**Goodbye!**"))
        sys.exit(0)