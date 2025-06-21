#!/usr/bin/env python3
"""
RegGenome Deep Research System with Google Gemini 2.5 Pro

Enhanced version of the RegGenome research system using Google's Gemini 2.5 Pro
for improved entity extraction, definition finding, and document analysis.

Usage:
    python reggenome_gemini.py [query]
    
Environment Setup:
    export GEMINI_API_KEY="your_gemini_api_key"
    # OR create a file: echo "your_key" > gemini_key.txt

Example:
    python reggenome_gemini.py "What are UCITS fund management requirements?"
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from config import Config
from gemini_orchestrator import GeminiUnifiedInterface
from deliverable_formatter import DeliverableFormatter

def print_gemini_banner():
    """Print Gemini enhancement banner"""
    print("\n" + "="*80)
    print("🤖 RegGenome Deep Research System - GEMINI 2.5 PRO ENHANCED")
    print("="*80)
    print("🚀 Powered by Google Gemini 2.5 Pro for Enhanced Accuracy")
    print("📋 Advanced Financial Context Understanding")
    print("🎯 Improved Entity Classification & Definition Extraction")
    print("="*80)

def check_requirements():
    """Check if all requirements are available"""
    
    # Check for RegGenome API key
    if not Path("key.txt").exists():
        print("\n❌ ERROR: RegGenome API key not found!")
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return False
    
    # Check for Gemini API key
    import os
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_key_file = Path("gemini_key.txt")
    
    if not gemini_key and not gemini_key_file.exists():
        print("\n❌ ERROR: Gemini API key not found!")
        print("   Please either:")
        print("   1. Set environment variable: export GEMINI_API_KEY='your_key'")
        print("   2. Create gemini_key.txt file with your API key")
        print("\n   Get your Gemini API key from: https://makersuite.google.com/app/apikey")
        return False
    
    # Check for google-generativeai library
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI library available")
    except ImportError:
        print("\n❌ ERROR: Google Generative AI library not found!")
        print("   Please install with: pip install google-generativeai")
        return False
    
    return True

async def main():
    """Main function with Gemini enhancement"""
    
    parser = argparse.ArgumentParser(description="RegGenome Research with Gemini 2.5 Pro")
    parser.add_argument("query", nargs="?", 
                       default="What are the main requirements for UCITS fund management companies in the EU?",
                       help="Research query to analyze")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Output directory for results")
    parser.add_argument("--format", type=str, choices=["standard", "deliverables", "both"], 
                       default="both", help="Output format type")
    
    args = parser.parse_args()
    
    print_gemini_banner()
    
    # Check requirements
    if not check_requirements():
        return
    
    print(f"\n🔍 Research Query: {args.query}")
    print(f"📁 Output Directory: {args.output_dir}")
    print()
    
    try:
        # Initialize Gemini-enhanced system
        config = Config()
        gemini_interface = GeminiUnifiedInterface(config)
        
        print("🚀 Starting Gemini-Enhanced Research...")
        print("   This may take several minutes due to AI processing...")
        
        # Run all tasks with Gemini enhancement
        results = await gemini_interface.run_all_tasks_with_gemini(args.query)
        
        # Save results
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Save using existing unified interface save method
        from unified_interface import UnifiedResearchInterface
        regular_interface = UnifiedResearchInterface(config)
        timestamp = regular_interface.save_results(results, output_dir)
        
        # Find the generated folder
        query_folders = list(output_dir.glob("*_*"))
        if query_folders:
            latest_folder = max(query_folders, key=lambda x: x.stat().st_mtime)
            
            print(f"\n🎯 Results Summary:")
            print(f"📂 Output Folder: {latest_folder}")
            print()
            
            # Show enhancement benefits
            enhancement_info = results.get("ai_enhancement", {})
            print(f"🤖 AI Enhancement Details:")
            print(f"   Model: {enhancement_info.get('model', 'N/A')}")
            print(f"   Enhanced Tasks: {', '.join(enhancement_info.get('enhanced_tasks', []))}")
            print(f"   Benefits:")
            for benefit in enhancement_info.get('enhancement_benefits', []):
                print(f"     • {benefit}")
            print()
            
            # Show file outputs
            print(f"📄 Generated Files:")
            for file_path in sorted(latest_folder.glob("*")):
                if file_path.is_file():
                    print(f"   • {file_path.name}")
            print()
            
            # Show RegGenome deliverables
            deliverable_files = list(latest_folder.glob("DELIVERABLE_*.csv"))
            if deliverable_files:
                print(f"🎯 RegGenome Challenge Deliverables (Enhanced by Gemini):")
                for file_path in sorted(deliverable_files):
                    print(f"   📊 {file_path.name}")
                print()
            
            print("✅ Gemini-Enhanced Research Complete!")
            print(f"   View results in: {latest_folder}")
            print("   All outputs benefit from Gemini 2.5 Pro's enhanced understanding")
        
    except Exception as e:
        print(f"\n❌ Error during Gemini-enhanced research: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 Troubleshooting Tips:")
        print("   1. Verify your Gemini API key is correct")
        print("   2. Check your internet connection")
        print("   3. Ensure you have sufficient API quota")
        print("   4. Try with a shorter/simpler query")

def setup_instructions():
    """Print setup instructions"""
    print("\n📋 SETUP INSTRUCTIONS:")
    print("="*50)
    print()
    print("1. Install required dependencies:")
    print("   pip install google-generativeai")
    print()
    print("2. Get your Gemini API key:")
    print("   Visit: https://makersuite.google.com/app/apikey")
    print() 
    print("3. Set up your API key (choose one):")
    print("   Option A: Environment variable")
    print("     export GEMINI_API_KEY='your_api_key_here'")
    print()
    print("   Option B: Key file")
    print("     echo 'your_api_key_here' > gemini_key.txt")
    print()
    print("4. Ensure RegGenome API key is in key.txt")
    print()
    print("5. Run the enhanced system:")
    print("   python reggenome_gemini.py 'Your research query'")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--setup", "setup", "help"]:
        setup_instructions()
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n\n👋 Research interrupted. Goodbye!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("\n💡 Run 'python reggenome_gemini.py setup' for setup instructions")
            sys.exit(1)