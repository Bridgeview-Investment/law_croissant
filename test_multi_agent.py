"""
Test Multi-Agent RegGenome Processor
Implements instruction.md specification
"""
import asyncio
import os
from pathlib import Path
from loguru import logger
import sys

from src.api.client import RegGenomeClient
from src.llm.mistral_client import MistralClient
from src.processors.multi_agent_processor import MultiAgentProcessor


async def test_multi_agent_processing():
    """Test the multi-agent processor following instruction.md"""
    
    logger.info("=== Starting Multi-Agent RegGenome Processing ===")
    
    # Initialize clients with async context manager
    async with RegGenomeClient() as reggenome_client:
        llm_client = MistralClient()
        
        # Initialize processor
        processor = MultiAgentProcessor(reggenome_client, llm_client)
        
        try:
            # Execute Phase 1: Initialization & Strategic Reconnaissance
            phase1_results = await processor.execute_phase_1()
            logger.info(f"Phase 1 Results: {phase1_results}")
            
            # Execute Phase 2: Data Ingestion & Structuring
            phase2_results = await processor.execute_phase_2()
            logger.info(f"Phase 2 Results: {phase2_results}")
            
            # Execute Phase 3: Core Intelligence Extraction & Synthesis
            phase3_results = await processor.execute_phase_3()
            logger.info(f"Phase 3 Results: {phase3_results}")
            
            # Export results
            output_dir = Path("outputs") / "multi_agent" / "20250621_test"
            export_results = await processor.export_results(output_dir)
            logger.info(f"Export Results: {export_results}")
            
            # Summary
            logger.info("=== MULTI-AGENT PROCESSING COMPLETED ===")
            logger.info(f"Target Initiatives: {processor.target_initiative_ids}")
            logger.info(f"Documents Processed: {len(processor.documents_df)}")
            logger.info(f"Terms Extracted: {len(processor.terms_df)}")
            logger.info(f"Relevance Mappings: {len(processor.relevance_df)}")
            logger.info(f"Definitions Found: {len(processor.terms_df[processor.terms_df['definition_text'].notna()])}")
            
            # Display sample results
            logger.info("\n=== SAMPLE TERMS ===")
            for _, row in processor.terms_df.head(10).iterrows():
                logger.info(f"- {row['term_name']} ({row['term_type']})")
            
            return {
                "success": True,
                "phase1_results": phase1_results,
                "phase2_results": phase2_results,
                "phase3_results": phase3_results,
                "export_paths": export_results
            }
            
        except Exception as e:
            logger.error(f"Multi-agent processing failed: {e}")
            raise


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    
    # Run the test
    asyncio.run(test_multi_agent_processing())