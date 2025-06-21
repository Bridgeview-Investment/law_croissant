"""
Multi-Agent Processor for RegGenome Challenge
Implements the instruction.md specification using LLM agents
"""
import asyncio
import pandas as pd
from typing import List, Dict, Optional, Any
from loguru import logger
from pathlib import Path
import json

from ..api.client import RegGenomeClient
from ..llm.mistral_client import MistralClient


class MultiAgentProcessor:
    """
    Multi-agent processor following instruction.md specification
    Implements Phases 1-3 of the RegGenome challenge solution
    """
    
    def __init__(self, reggenome_client: RegGenomeClient, llm_client: MistralClient):
        self.reggenome_client = reggenome_client
        self.llm_client = llm_client
        
        # Target initiative names - using actual RegGenome API names
        self.target_initiative_names = [
            "US - Investment Advisers Act (IAA), 1940",
            "US - Investment Company Act (ICA), 1940", 
            "EU - Undertaking for Collective Investment in Transferrable Securities (UCITS) Directives",
            "UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations, 2011 and 2016"
        ]
        
        # Data schemas as per instruction.md Step 1.3
        self.documents_df = pd.DataFrame(columns=[
            'doc_id', 'title', 'published_date', 'source_text', 'rg_signposts', 'rg_reg_scores'
        ])
        
        self.terms_df = pd.DataFrame(columns=[
            'term_id', 'term_name', 'term_type', 'definition_text', 
            'definition_source_doc_id', 'definition_source_text'
        ])
        
        self.relevance_df = pd.DataFrame(columns=[
            'doc_id', 'term_id', 'mention_context'
        ])
        
        self.target_initiative_ids = []
        self.raw_extracted_terms = []
        
        logger.info("Multi-agent processor initialized")
    
    async def execute_phase_1(self) -> Dict[str, Any]:
        """
        PHASE 1: Initialization & Strategic Reconnaissance
        Steps 1.1-1.3 from instruction.md
        """
        logger.info("=== PHASE 1: Initialization & Strategic Reconnaissance ===")
        
        # STEP 1.2: Scope Definition via API
        await self._step_1_2_scope_definition()
        
        # STEP 1.3: Data Schema Definition (already done in __init__)
        logger.info("STEP 1.3: Data schemas defined")
        
        return {
            "target_initiative_ids": self.target_initiative_ids,
            "documents_schema": list(self.documents_df.columns),
            "terms_schema": list(self.terms_df.columns),
            "relevance_schema": list(self.relevance_df.columns)
        }
    
    async def _step_1_2_scope_definition(self):
        """STEP 1.2: Find initiative IDs from names"""
        logger.info("STEP 1.2: Finding initiative IDs...")
        
        # Get all initiatives
        initiatives = await self.reggenome_client.get_initiatives()
        
        # Match names to IDs
        for target_name in self.target_initiative_names:
            for initiative in initiatives:
                if initiative.get("name") == target_name:
                    self.target_initiative_ids.append(initiative.get("id"))
                    logger.info(f"Found ID {initiative.get('id')} for '{target_name}'")
                    break
            else:
                logger.warning(f"Initiative not found: '{target_name}'")
        
        logger.info(f"TARGET_INITIATIVE_IDS: {self.target_initiative_ids}")
    
    async def execute_phase_2(self) -> Dict[str, Any]:
        """
        PHASE 2: Data Ingestion & Structuring
        Step 2.1 from instruction.md
        """
        logger.info("=== PHASE 2: Data Ingestion & Structuring ===")
        
        # STEP 2.1: Full Document Retrieval
        await self._step_2_1_document_retrieval()
        
        return {
            "documents_retrieved": len(self.documents_df),
            "total_characters": self.documents_df['source_text'].str.len().sum(),
            "documents_sample": self.documents_df.head(3).to_dict('records')
        }
    
    async def _step_2_1_document_retrieval(self):
        """STEP 2.1: Populate documents_df with all target documents"""
        logger.info("STEP 2.1: Retrieving all documents...")
        
        if not self.target_initiative_ids:
            logger.error("No target initiative IDs available")
            return
        
        # Fetch all documents for target initiatives
        documents = await self.reggenome_client.fetch_all_documents_for_initiatives(
            self.target_initiative_ids
        )
        
        # Populate documents_df
        document_records = []
        for doc in documents:
            # Extract text from structured source_text if needed
            source_text = doc.get('source_text', '')
            if isinstance(source_text, list):
                # Extract text from blocks structure
                text_parts = []
                for block in source_text:
                    if isinstance(block, dict) and 'blocks' in block:
                        for text_block in block['blocks']:
                            if isinstance(text_block, dict) and 'text' in text_block:
                                text_parts.append(text_block['text'])
                source_text = ' '.join(text_parts)
            
            record = {
                'doc_id': doc.get('document_id'),
                'title': doc.get('title', ''),
                'published_date': doc.get('published', ''),
                'source_text': source_text,
                'rg_signposts': doc.get('signposts', []),
                'rg_reg_scores': doc.get('reg_scores', {})
            }
            document_records.append(record)
        
        self.documents_df = pd.DataFrame(document_records)
        logger.info(f"Retrieved {len(self.documents_df)} documents")
    
    async def execute_phase_3(self) -> Dict[str, Any]:
        """
        PHASE 3: Core Intelligence Extraction & Synthesis
        Steps 3.1-3.3 from instruction.md
        """
        logger.info("=== PHASE 3: Core Intelligence Extraction & Synthesis ===")
        
        # STEP 3.1: Terminology Extraction
        await self._step_3_1_terminology_extraction()
        
        # STEP 3.2: Relevance Prediction & Correlation
        await self._step_3_2_relevance_prediction()
        
        # STEP 3.3: Definitional Sourcing
        await self._step_3_3_definitional_sourcing()
        
        definitions_found = 0
        if len(self.terms_df) > 0 and 'definition_text' in self.terms_df.columns:
            definitions_found = len(self.terms_df[self.terms_df['definition_text'].notna()])
        
        return {
            "terms_extracted": len(self.terms_df),
            "relevance_mappings": len(self.relevance_df),
            "definitions_found": definitions_found,
            "top_terms": self.terms_df.head(10).to_dict('records')
        }
    
    async def _step_3_1_terminology_extraction(self):
        """STEP 3.1: Extract and classify terms using LLM"""
        logger.info("STEP 3.1: Extracting terminology using LLM...")
        
        # Extract terms from all documents using Mistral
        self.raw_extracted_terms = await self.llm_client.batch_extract_terms(
            self.documents_df.to_dict('records')
        )
        
        # Deduplication and normalization
        unique_terms = {}
        for term in self.raw_extracted_terms:
            term_name = term.get("term_name", "").strip().lower()
            if term_name and term_name not in unique_terms:
                unique_terms[term_name] = term
        
        # Populate terms_df
        term_records = []
        for i, (term_name, term_data) in enumerate(unique_terms.items()):
            record = {
                'term_id': f"term_{i+1:04d}",
                'term_name': term_data.get("term_name", ""),
                'term_type': term_data.get("term_type", ""),
                'definition_text': None,  # To be filled in step 3.3
                'definition_source_doc_id': None,
                'definition_source_text': None
            }
            term_records.append(record)
        
        self.terms_df = pd.DataFrame(term_records)
        logger.info(f"Extracted and deduplicated {len(self.terms_df)} unique terms")
    
    async def _step_3_2_relevance_prediction(self):
        """STEP 3.2: Create relevance mappings"""
        logger.info("STEP 3.2: Creating relevance mappings...")
        
        # Create term_id mapping
        term_name_to_id = {
            row['term_name']: row['term_id'] 
            for _, row in self.terms_df.iterrows()
        }
        
        # Populate relevance_df from raw_extracted_terms
        relevance_records = []
        for term in self.raw_extracted_terms:
            term_name = term.get("term_name", "")
            term_id = term_name_to_id.get(term_name)
            
            if term_id:
                record = {
                    'doc_id': term.get("source_doc_id"),
                    'term_id': term_id,
                    'mention_context': term.get("contextual_explanation", "")
                }
                relevance_records.append(record)
        
        self.relevance_df = pd.DataFrame(relevance_records)
        logger.info(f"Created {len(self.relevance_df)} relevance mappings")
    
    async def _step_3_3_definitional_sourcing(self):
        """STEP 3.3: Find definitions using Strategy A and B"""
        logger.info("STEP 3.3: Finding definitions...")
        
        definitions_found = 0
        
        for idx, row in self.terms_df.iterrows():
            term_name = row['term_name']
            term_id = row['term_id']
            
            # Strategy A: Interrogator API
            definition_found = await self._strategy_a_interrogator(term_name, idx)
            
            if not definition_found:
                # Strategy B: LLM Judge
                definition_found = await self._strategy_b_llm_judge(term_name, idx)
            
            if definition_found:
                definitions_found += 1
        
        logger.info(f"Found definitions for {definitions_found}/{len(self.terms_df)} terms")
    
    async def _strategy_a_interrogator(self, term_name: str, term_idx: int) -> bool:
        """Strategy A: Use Interrogator API to find definitions"""
        
        query = f"What is the official legal definition of '{term_name}'?"
        
        try:
            results = await self.reggenome_client.interrogator_search(
                query=query,
                initiative_ids=self.target_initiative_ids
            )
            
            if results and len(results) > 0:
                top_result = results[0]
                
                # Extract definition from top result
                definition_text = top_result.get("content", "")
                source_doc_id = top_result.get("document_id", "")
                
                if definition_text and source_doc_id:
                    # Update terms_df
                    self.terms_df.at[term_idx, 'definition_text'] = definition_text
                    self.terms_df.at[term_idx, 'definition_source_doc_id'] = source_doc_id
                    self.terms_df.at[term_idx, 'definition_source_text'] = definition_text
                    
                    logger.debug(f"Strategy A found definition for '{term_name}'")
                    return True
                    
        except Exception as e:
            logger.error(f"Strategy A failed for term '{term_name}': {e}")
        
        return False
    
    async def _strategy_b_llm_judge(self, term_name: str, term_idx: int) -> bool:
        """Strategy B: Use LLM to judge definition sentences"""
        
        # Find all sentences mentioning the term
        candidate_sentences = []
        
        for _, doc_row in self.documents_df.iterrows():
            source_text = doc_row['source_text']
            doc_id = doc_row['doc_id']
            
            if term_name.lower() in source_text.lower():
                # Split into sentences (simple approach)
                sentences = source_text.split('.')
                
                for sentence in sentences:
                    if term_name.lower() in sentence.lower():
                        candidate_sentences.append({
                            'sentence': sentence.strip(),
                            'doc_id': doc_id
                        })
        
        # Judge each sentence
        for candidate in candidate_sentences[:10]:  # Limit to avoid too many API calls
            sentence = candidate['sentence']
            doc_id = candidate['doc_id']
            
            try:
                is_definition = await self.llm_client.validate_definition(term_name, sentence)
                
                if is_definition:
                    # Update terms_df
                    self.terms_df.at[term_idx, 'definition_text'] = sentence
                    self.terms_df.at[term_idx, 'definition_source_doc_id'] = doc_id
                    self.terms_df.at[term_idx, 'definition_source_text'] = sentence
                    
                    logger.debug(f"Strategy B found definition for '{term_name}'")
                    return True
                    
            except Exception as e:
                logger.error(f"Strategy B validation failed for term '{term_name}': {e}")
                continue
        
        return False
    
    async def export_results(self, output_dir: Path) -> Dict[str, str]:
        """Export all DataFrames and results"""
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export DataFrames
        documents_path = output_dir / "documents_df.csv"
        terms_path = output_dir / "terms_df.csv"
        relevance_path = output_dir / "relevance_df.csv"
        
        self.documents_df.to_csv(documents_path, index=False)
        self.terms_df.to_csv(terms_path, index=False)
        self.relevance_df.to_csv(relevance_path, index=False)
        
        # Export summary
        definitions_found = 0
        if len(self.terms_df) > 0 and 'definition_text' in self.terms_df.columns:
            definitions_found = len(self.terms_df[self.terms_df['definition_text'].notna()])
        
        term_breakdown = {}
        if len(self.terms_df) > 0 and 'term_type' in self.terms_df.columns:
            term_breakdown = self.terms_df['term_type'].value_counts().to_dict()
        
        summary = {
            "target_initiative_ids": self.target_initiative_ids,
            "documents_processed": len(self.documents_df),
            "terms_extracted": len(self.terms_df),
            "relevance_mappings": len(self.relevance_df),
            "definitions_found": definitions_found,
            "term_breakdown": term_breakdown
        }
        
        summary_path = output_dir / "processing_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Results exported to {output_dir}")
        
        return {
            "documents_df": str(documents_path),
            "terms_df": str(terms_path),
            "relevance_df": str(relevance_path),
            "summary": str(summary_path)
        }