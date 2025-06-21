"""
Google Gemini 2.5 Pro Integration for RegGenome Deep Research System

This module integrates Google's Gemini 2.5 Pro model for enhanced text processing
in entity extraction, definition finding, and document analysis tasks.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
import json
import logging
from dataclasses import dataclass

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google Generative AI library not available. Install with: pip install google-generativeai")

@dataclass
class GeminiConfig:
    """Configuration for Gemini API"""
    api_key: str
    model_name: str = "gemini-2.0-flash-exp"  # Using latest available model
    temperature: float = 0.1
    max_output_tokens: int = 8192
    
class GeminiClient:
    """Client for interacting with Google Gemini 2.5 Pro"""
    
    def __init__(self, config: GeminiConfig):
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI library is required. Install with: pip install google-generativeai")
        
        self.config = config
        genai.configure(api_key=config.api_key)
        
        # Initialize the model
        generation_config = {
            "temperature": config.temperature,
            "max_output_tokens": config.max_output_tokens,
            "response_mime_type": "text/plain",
        }
        
        self.model = genai.GenerativeModel(
            model_name=config.model_name,
            generation_config=generation_config,
        )
        
        logging.info(f"Initialized Gemini client with model: {config.model_name}")
    
    async def extract_entities(self, text: str, context: str = "") -> Dict[str, Any]:
        """Extract regulated entities from text using Gemini"""
        
        prompt = f"""
        You are an expert in financial regulation analysis. Extract ALL mentions of regulated entities, activities, and products from the following regulatory text.

        Context: {context}
        
        Text to analyze:
        {text}
        
        Please identify and extract:
        1. ENTITIES: Investment advisers, fund managers, banks, financial institutions, regulatory bodies
        2. ACTIVITIES: Portfolio management, trading, custody, reporting, compliance activities  
        3. PRODUCTS: Mutual funds, UCITS, ETFs, securities, derivatives, investment products
        
        For each item found, provide:
        - name: The exact term as mentioned
        - type: entity/activity/product
        - category: Specific subcategory (e.g., investment_adviser, portfolio_management, mutual_fund)
        - description: Brief description of what it is
        - confidence: Score 0-1 indicating confidence in classification
        
        Return as JSON format:
        {{
            "entities": [
                {{
                    "name": "investment adviser",
                    "type": "entity", 
                    "category": "investment_adviser",
                    "description": "Person or firm providing investment advice",
                    "confidence": 0.95
                }}
            ],
            "activities": [...],
            "products": [...]
        }}
        
        Only extract items clearly mentioned in the text. Be precise and avoid duplicates.
        """
        
        try:
            response = await self._generate_async(prompt)
            
            # Parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                return json.loads(json_text)
            else:
                logging.warning("Could not parse JSON from Gemini response")
                return {"entities": [], "activities": [], "products": []}
                
        except Exception as e:
            logging.error(f"Error in Gemini entity extraction: {e}")
            return {"entities": [], "activities": [], "products": []}
    
    async def find_definitions(self, text: str, entity_name: str) -> List[Dict[str, Any]]:
        """Find formal definitions of an entity in text using Gemini"""
        
        prompt = f"""
        You are an expert legal text analyst. Find ALL formal definitions of the term "{entity_name}" in the following regulatory text.

        Text to search:
        {text}
        
        Look for patterns like:
        - "{entity_name}" means...
        - "{entity_name}" is defined as...
        - "{entity_name}" refers to...
        - For purposes of this [Act/Regulation], "{entity_name}"...
        
        For each definition found, extract:
        - definition_text: The complete definition text
        - context: Surrounding text for reference
        - section: Section or clause reference if available
        - confidence: Score 0-1 for how certain this is a formal definition
        
        Return as JSON:
        {{
            "definitions": [
                {{
                    "definition_text": "means any person who...",
                    "context": "surrounding context...",
                    "section": "Section 202(a)(11)",
                    "confidence": 0.9
                }}
            ]
        }}
        
        Only return actual formal definitions, not general mentions.
        """
        
        try:
            response = await self._generate_async(prompt)
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                result = json.loads(json_text)
                return result.get("definitions", [])
            else:
                return []
                
        except Exception as e:
            logging.error(f"Error in Gemini definition extraction: {e}")
            return []
    
    async def predict_document_relevance(self, document_text: str, entities: List[str], 
                                       activities: List[str], products: List[str]) -> Dict[str, Any]:
        """Predict document relevance to entities using Gemini"""
        
        all_items = entities + activities + products
        items_text = ", ".join(all_items[:20])  # Limit for prompt size
        
        prompt = f"""
        You are an expert regulatory analyst. Analyze the following document and determine its relevance to these financial entities, activities, and products:

        Target items: {items_text}
        
        Document text:
        {document_text[:4000]}...
        
        For each relevant item, provide:
        - item_name: Name of the entity/activity/product
        - relevance_score: Score 0-1 indicating how relevant the document is
        - explanation: Brief explanation of why it's relevant
        - sections: Any specific sections that mention this item
        
        Return as JSON:
        {{
            "relevant_items": [
                {{
                    "item_name": "investment adviser",
                    "relevance_score": 0.85,
                    "explanation": "Document contains specific requirements for investment advisers",
                    "sections": ["section 3.1", "section 4.2"]
                }}
            ],
            "overall_relevance": 0.7,
            "primary_focus": "investment adviser regulation"
        }}
        
        Only include items with relevance_score > 0.3.
        """
        
        try:
            response = await self._generate_async(prompt)
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                return json.loads(json_text)
            else:
                return {"relevant_items": [], "overall_relevance": 0.0, "primary_focus": "general"}
                
        except Exception as e:
            logging.error(f"Error in Gemini relevance prediction: {e}")
            return {"relevant_items": [], "overall_relevance": 0.0, "primary_focus": "general"}
    
    async def _generate_async(self, prompt: str) -> str:
        """Generate response using Gemini model (async wrapper)"""
        try:
            # Gemini API is synchronous, so we run it in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self._generate_sync, prompt)
            return response
        except Exception as e:
            logging.error(f"Error generating Gemini response: {e}")
            raise
    
    def _generate_sync(self, prompt: str) -> str:
        """Generate response using Gemini model (synchronous)"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Error in Gemini generation: {e}")
            raise

class GeminiEnhancedExtractor:
    """Enhanced extraction using Gemini for better accuracy"""
    
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client
    
    async def extract_from_document(self, document) -> Dict[str, Any]:
        """Extract entities from a document using Gemini"""
        
        # Prepare document text
        doc_text = self._prepare_document_text(document)
        context = f"Document: {document.title or 'Unknown'} from {document.publishers[0].get('name', 'Unknown') if document.publishers else 'Unknown'}"
        
        # Extract using Gemini
        extraction_result = await self.gemini.extract_entities(doc_text, context)
        
        # Enhance with document metadata
        for item_list in [extraction_result.get("entities", []), 
                         extraction_result.get("activities", []), 
                         extraction_result.get("products", [])]:
            for item in item_list:
                item["source_document_id"] = document.document_id
                item["source_title"] = document.title
        
        return extraction_result
    
    async def find_entity_definitions(self, documents, entity_name: str) -> List[Dict[str, Any]]:
        """Find definitions across multiple documents using Gemini"""
        
        all_definitions = []
        
        for doc in documents[:10]:  # Limit for API efficiency
            doc_text = self._prepare_document_text(doc)
            
            definitions = await self.gemini.find_definitions(doc_text, entity_name)
            
            # Add document metadata
            for defn in definitions:
                defn["document_id"] = doc.document_id
                defn["document_title"] = doc.title
                defn["document_url"] = self._get_document_url(doc)
            
            all_definitions.extend(definitions)
        
        # Sort by confidence
        all_definitions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return all_definitions[:3]  # Return top 3 definitions
    
    def _prepare_document_text(self, document) -> str:
        """Prepare document text for Gemini processing"""
        text_parts = []
        
        if document.title:
            text_parts.append(f"Title: {document.title}")
        
        if document.source_text:
            for item in document.source_text[:10]:  # Limit for API efficiency
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
        
        full_text = "\n".join(text_parts)
        
        # Limit text length for API
        return full_text[:10000] + "..." if len(full_text) > 10000 else full_text
    
    def _get_document_url(self, doc) -> Optional[str]:
        """Get document URL if available"""
        if doc.metadata and "source_urls" in doc.metadata:
            urls = doc.metadata["source_urls"]
            if urls and isinstance(urls, list) and len(urls) > 0:
                return urls[0]
        return None

def create_gemini_client() -> Optional[GeminiClient]:
    """Create Gemini client with API key from environment or config"""
    
    # Try to get API key from various sources
    api_key = None
    
    # 1. Environment variable
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    # 2. From config file
    if not api_key:
        try:
            from pathlib import Path
            gemini_key_file = Path("gemini_key.txt")
            if gemini_key_file.exists():
                api_key = gemini_key_file.read_text().strip()
        except Exception:
            pass
    
    # 3. From Google Cloud credentials
    if not api_key:
        try:
            import google.auth
            credentials, project = google.auth.default()
            # This would require additional setup for service account
        except Exception:
            pass
    
    if not api_key:
        print("❌ Gemini API key not found. Please set GEMINI_API_KEY environment variable or create gemini_key.txt file")
        return None
    
    try:
        config = GeminiConfig(api_key=api_key)
        return GeminiClient(config)
    except Exception as e:
        print(f"❌ Error creating Gemini client: {e}")
        return None