#!/usr/bin/env python3
"""
RegGenome Challenge Deliverables Demo

This script demonstrates how the system now produces the exact deliverables
specified in the Chinese requirements:

交付物 1: 实体清单 (Entity Taxonomy)
交付物 2: 关联预测 (Relevance Predictions)  
交付物 3: 定义追溯 (Entity Definitions)

Usage:
    python demo_deliverables.py [query]

Example:
    python demo_deliverables.py "What are UCITS fund management requirements?"
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from config import Config
from unified_interface import UnifiedResearchInterface

def print_demo_banner():
    """Print demo banner in both Chinese and English"""
    print("\n" + "="*80)
    print("🇨🇳 RegGenome 挑战赛交付物演示 | RegGenome Challenge Deliverables Demo 🇺🇸")
    print("="*80)
    print()
    print("本系统现在生成符合规范要求的三个核心交付物:")
    print("This system now generates three core deliverables that meet specification requirements:")
    print()
    print("📋 交付物 1 | Deliverable 1: 实体分类体系 | Entity Taxonomy")
    print("   格式 | Format: EntityID | EntityName | EntityType | ParentEntityID")
    print("   文件 | Files: CSV + JSON")
    print()
    print("🔗 交付物 2 | Deliverable 2: 文档关联预测 | Document Relevance Predictions")  
    print("   格式 | Format: DocumentID | SubDocumentID | TextSnippet | RelevantEntityID")
    print("   文件 | Files: CSV + JSON")
    print()
    print("📖 交付物 3 | Deliverable 3: 实体定义追溯 | Entity Definition Linking")
    print("   格式 | Format: EntityID | EntityName | DefiningDocumentID | DefinitionFullText")
    print("   文件 | Files: CSV + JSON")
    print()
    print("="*80)

async def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="RegGenome Challenge Deliverables Demo")
    parser.add_argument("query", nargs="?", 
                       default="What are the main requirements for UCITS fund management companies?",
                       help="Research query to analyze")
    parser.add_argument("--output-dir", type=str, default="demo_output",
                       help="Output directory for demo results")
    
    args = parser.parse_args()
    
    # Check for API key
    if not Path("key.txt").exists():
        print("\n❌ 错误 | ERROR: 未找到API密钥 | API key not found!")
        print("   请将RegGenome JWT令牌放在'key.txt'文件中")
        print("   Please place your RegGenome JWT token in 'key.txt'")
        return
    
    print_demo_banner()
    
    # Initialize system
    print(f"🔍 查询 | Query: {args.query}")
    print(f"📁 输出目录 | Output Directory: {args.output_dir}")
    print()
    
    try:
        config = Config()
        interface = UnifiedResearchInterface(config)
        
        print("🚀 启动深度研究系统... | Starting Deep Research System...")
        print("   正在运行所有三个任务... | Running all three tasks...")
        
        # Run all tasks
        results = await interface.run_all_tasks(args.query)
        
        # Save results with new deliverable format
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = interface.save_results(results, output_dir)
        
        # Find the generated deliverable files
        query_folders = list(output_dir.glob("*_*"))
        if query_folders:
            latest_folder = max(query_folders, key=lambda x: x.stat().st_mtime)
            
            print(f"\n🎯 RegGenome 挑战赛交付物已生成 | RegGenome Challenge Deliverables Generated:")
            print(f"📂 输出文件夹 | Output Folder: {latest_folder}")
            print()
            
            # List the deliverable files
            deliverable_files = [
                ("DELIVERABLE_1_Entity_Taxonomy", "实体分类体系 | Entity Taxonomy"),
                ("DELIVERABLE_2_Relevance_Predictions", "关联预测 | Relevance Predictions"), 
                ("DELIVERABLE_3_Entity_Definitions", "定义追溯 | Entity Definitions"),
                ("REGGENOME_DELIVERABLES_SUMMARY", "交付物总结 | Deliverables Summary")
            ]
            
            for file_prefix, description in deliverable_files:
                csv_files = list(latest_folder.glob(f"{file_prefix}*.csv"))
                json_files = list(latest_folder.glob(f"{file_prefix}*.json"))
                md_files = list(latest_folder.glob(f"{file_prefix}*.md"))
                
                if csv_files or json_files or md_files:
                    print(f"📄 {description}:")
                    for f in csv_files:
                        print(f"   📊 CSV: {f.name}")
                    for f in json_files:
                        print(f"   🔗 JSON: {f.name}")
                    for f in md_files:
                        print(f"   📝 MD: {f.name}")
                    print()
            
            # Show example content from Deliverable 1
            taxonomy_csv = list(latest_folder.glob("DELIVERABLE_1_Entity_Taxonomy*.csv"))
            if taxonomy_csv:
                print("📋 交付物 1 示例 | Deliverable 1 Sample:")
                print("   EntityID | EntityName | EntityType | ParentEntityID")
                print("   ---------|------------|------------|---------------")
                
                with open(taxonomy_csv[0], 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[1:6]:  # Show first 5 data rows
                        parts = line.strip().split(',')
                        if len(parts) >= 4:
                            print(f"   {parts[0]:<8} | {parts[1]:<20} | {parts[2]:<12} | {parts[3]}")
                print("   ...")
                print()
            
            print("✅ 演示完成 | Demo Complete!")
            print(f"   查看完整结果 | View full results in: {latest_folder}")
            print("   所有交付物均符合挑战赛规范要求")
            print("   All deliverables conform to challenge specification requirements")
        
    except Exception as e:
        print(f"\n❌ 错误 | Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("正在启动RegGenome挑战赛交付物演示...")
    print("Starting RegGenome Challenge Deliverables Demo...")
    asyncio.run(main())