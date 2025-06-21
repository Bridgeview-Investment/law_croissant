"""
Mistral AI Client for RegGenome Challenge
Implements LLM-based entity extraction and definition validation
"""
import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import httpx
from loguru import logger


@dataclass
class LLMResponse:
    """Response from LLM API call"""
    content: str
    tokens_used: int
    model: str
    success: bool
    error: Optional[str] = None


class MistralClient:
    """Mistral AI API client for regulatory document processing"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment")
        
        self.base_url = "https://api.mistral.ai/v1"
        self.model = "mistral-medium-latest"
        self.timeout = 120
        
        # Rate limiting
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        
        logger.info(f"Mistral client initialized with model: {self.model}")
    
    async def _make_request(self, messages: List[Dict], temperature: float = 0.1) -> LLMResponse:
        """Make async request to Mistral API with rate limiting"""
        
        # Rate limiting
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4000
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                self.last_request_time = asyncio.get_event_loop().time()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                
                return LLMResponse(
                    content=content,
                    tokens_used=tokens_used,
                    model=self.model,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"Mistral API request failed: {e}")
            return LLMResponse(
                content="",
                tokens_used=0,
                model=self.model,
                success=False,
                error=str(e)
            )
    
    async def extract_regulatory_terms(self, document_text: str, doc_id: str) -> List[Dict]:
        """Extract regulatory terms using ExtractorPrompt"""
        
        extractor_prompt = """You are a specialized legal AI trained to extract regulatory terminology from financial regulatory documents. Your task is to identify and categorize three types of regulatory elements:

1. **ENTITIES**: Organizations, institutions, regulatory bodies, or legal persons that are subject to or enforce regulations
2. **PRODUCTS**: Financial instruments, securities, investment vehicles, or financial products that are regulated
3. **ACTIVITIES**: Actions, processes, operations, or business activities that require regulatory compliance or authorization

INSTRUCTIONS:
- Extract terms that have clear regulatory significance
- Focus on terms that would need formal definition or regulatory clarity
- Avoid common words, dates, or procedural language
- Each term should be substantial enough to warrant definition

OUTPUT FORMAT: Return ONLY a valid JSON array with this exact structure (no markdown, no explanation, just the JSON):
[
  {
    "term_name": "exact term as it appears",
    "term_type": "ENTITY|PRODUCT|ACTIVITY", 
    "contextual_explanation": "brief explanation of regulatory significance"
  }
]

IMPORTANT: Your response must be valid JSON that can be parsed directly. Do not include any text before or after the JSON array.

DOCUMENT TEXT:
""" + document_text[:8000]  # Limit to avoid token limits
        
        messages = [
            {"role": "system", "content": "You are a precise legal terminology extractor. Return only valid JSON."},
            {"role": "user", "content": extractor_prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.1)
        
        if not response.success:
            logger.error(f"Term extraction failed for doc {doc_id}: {response.error}")
            return []
        
        try:
            # First try to parse as direct JSON
            terms_data = json.loads(response.content)
            
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()
            
            # Look for ```json blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    try:
                        json_content = content[start:end].strip()
                        terms_data = json.loads(json_content)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse markdown JSON for doc {doc_id}: {e}")
                        logger.error(f"Raw response: {response.content[:500]}")
                        return []
                else:
                    logger.error(f"Failed to extract JSON from markdown for doc {doc_id}")
                    logger.error(f"Raw response: {response.content[:500]}")
                    return []
            else:
                # Try to find JSON array directly
                import re
                json_match = re.search(r'\[[^\]]*\]', content, re.DOTALL)
                if json_match:
                    try:
                        json_content = json_match.group(0)
                        terms_data = json.loads(json_content)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse extracted JSON for doc {doc_id}")
                        logger.error(f"Raw response: {response.content[:500]}")
                        return []
                else:
                    logger.error(f"No JSON found in response for doc {doc_id}")
                    logger.error(f"Raw response: {response.content[:500]}")
                    return []
        
        # Add source document ID to each term
        if isinstance(terms_data, list):
            for term in terms_data:
                if isinstance(term, dict):
                    term["source_doc_id"] = doc_id
        
        logger.info(f"Extracted {len(terms_data)} terms from document {doc_id}")
        return terms_data
    
    async def validate_definition(self, term_name: str, sentence_text: str) -> bool:
        """Validate if sentence provides formal definition using JudgePrompt"""
        
        judge_prompt = f"""You are a precise legal analyzer. Does the following sentence provide a formal definition for the term "{term_name}"? 

A formal definition should:
- Explain what the term means
- Provide scope or boundaries
- Use definitive language (e.g., "means", "refers to", "is defined as")
- Not be merely a mention or example

Answer only with "YES" or "NO".

Sentence: "{sentence_text}"
"""
        
        messages = [
            {"role": "system", "content": "You are a legal definition validator. Answer only YES or NO."},
            {"role": "user", "content": judge_prompt}
        ]
        
        response = await self._make_request(messages, temperature=0.0)
        
        if not response.success:
            logger.error(f"Definition validation failed for term '{term_name}': {response.error}")
            return False
        
        return response.content.strip().upper() == "YES"
    
    async def batch_extract_terms(self, documents: List[Dict], batch_size: int = 5) -> List[Dict]:
        """Extract terms from multiple documents in batches"""
        
        all_terms = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            tasks = [
                self.extract_regulatory_terms(doc.get("source_text", ""), doc.get("document_id", str(i)))
                for doc in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    continue
                all_terms.extend(result)
        
        logger.info(f"Total terms extracted from {len(documents)} documents: {len(all_terms)}")
        return all_terms