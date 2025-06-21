"""LLM utilities for RegGenome Deep Research System."""

import logging
from typing import Optional, List, Dict, Any, Type, TypeVar
from pydantic import BaseModel
import json

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

from .config import config

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMManager:
    """Manager for different LLM providers and models."""
    
    def __init__(self):
        self._models_cache: Dict[str, BaseChatModel] = {}
    
    def get_model(self, model_name: Optional[str] = None, provider: Optional[str] = None) -> BaseChatModel:
        """Get an LLM model instance."""
        provider = provider or config.llm.provider
        model_name = model_name or config.llm.default_model
        
        cache_key = f"{provider}:{model_name}"
        
        if cache_key not in self._models_cache:
            if provider.lower() == "openai":
                if not config.llm.openai_api_key:
                    raise ValueError("OpenAI API key not configured")
                
                self._models_cache[cache_key] = ChatOpenAI(
                    model=model_name,
                    api_key=config.llm.openai_api_key,
                    temperature=config.llm.temperature,
                    max_tokens=config.llm.max_tokens
                )
            
            elif provider.lower() == "anthropic":
                if not config.llm.anthropic_api_key:
                    raise ValueError("Anthropic API key not configured")
                
                self._models_cache[cache_key] = ChatAnthropic(
                    model=model_name,
                    api_key=config.llm.anthropic_api_key,
                    temperature=config.llm.temperature,
                    max_tokens=config.llm.max_tokens
                )
            
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        
        return self._models_cache[cache_key]
    
    def get_research_model(self) -> BaseChatModel:
        """Get the configured research model."""
        return self.get_model(config.llm.research_model, config.llm.provider)
    
    def get_extraction_model(self) -> BaseChatModel:
        """Get the configured extraction model."""
        return self.get_model(config.llm.extraction_model, config.llm.provider)
    
    def get_classification_model(self) -> BaseChatModel:
        """Get the configured classification model."""
        return self.get_model(config.llm.classification_model, config.llm.provider)


# Global LLM manager instance
llm_manager = LLMManager()


async def extract_structured_data(
    content: str,
    extraction_prompt: str,
    response_model: Type[T],
    model: Optional[BaseChatModel] = None
) -> T:
    """Extract structured data from content using LLM."""
    
    if model is None:
        model = llm_manager.get_extraction_model()
    
    # Create parser for the response model
    parser = PydanticOutputParser(pydantic_object=response_model)
    format_instructions = parser.get_format_instructions()
    
    # Prepare messages
    system_prompt = f"""You are an expert in regulatory document analysis. Your task is to extract structured information from regulatory documents.

{extraction_prompt}

{format_instructions}

Important guidelines:
- Be precise and accurate in your extractions
- Use the exact terminology from the source document
- Provide confidence scores based on the clarity of the information
- If information is unclear or missing, indicate this appropriately
- Include relevant context and source references"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please analyze the following regulatory document content and extract the requested information:\n\n{content}")
    ]
    
    try:
        # Generate response
        response = await model.ainvoke(messages)
        
        # Parse the response
        parsed_response = parser.parse(response.content)
        return parsed_response
        
    except Exception as e:
        logger.error(f"Error in structured data extraction: {e}")
        logger.debug(f"Response content: {response.content if 'response' in locals() else 'No response'}")
        raise


async def classify_relevance(
    content: str,
    classification_prompt: str,
    model: Optional[BaseChatModel] = None
) -> Dict[str, float]:
    """Classify relevance of content to different categories."""
    
    if model is None:
        model = llm_manager.get_classification_model()
    
    system_prompt = f"""You are an expert in regulatory document classification. Your task is to assess the relevance of regulatory content to different categories.

{classification_prompt}

Respond with a JSON object containing relevance scores (0.0 to 1.0) for each category.
Be precise and provide reasoning for your scores.

Example response format:
{{
    "category1": 0.85,
    "category2": 0.23,
    "category3": 0.91,
    "reasoning": "Brief explanation of the scoring rationale"
}}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please classify the relevance of the following content:\n\n{content}")
    ]
    
    try:
        response = await model.ainvoke(messages)
        
        # Parse JSON response
        result = json.loads(response.content)
        return result
        
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error in relevance classification: {e}")
        logger.debug(f"Response content: {response.content if 'response' in locals() else 'No response'}")
        return {}


async def synthesize_and_deduplicate(
    items: List[Dict[str, Any]],
    synthesis_prompt: str,
    model: Optional[BaseChatModel] = None
) -> List[Dict[str, Any]]:
    """Synthesize and deduplicate similar items using LLM."""
    
    if model is None:
        model = llm_manager.get_research_model()
    
    system_prompt = f"""You are an expert in regulatory data analysis and deduplication. Your task is to identify duplicates, near-duplicates, and merge similar items while preserving important distinctions.

{synthesis_prompt}

Guidelines:
- Identify items that refer to the same concept but may have different wording
- Merge similar items while preserving unique characteristics
- Maintain hierarchical relationships
- Preserve source attribution for merged items
- Be conservative - only merge when you're confident items are truly the same or very similar

Respond with a JSON array of the deduplicated and merged items."""

    items_json = json.dumps(items, indent=2)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please analyze and deduplicate the following items:\n\n{items_json}")
    ]
    
    try:
        response = await model.ainvoke(messages)
        
        # Parse JSON response
        result = json.loads(response.content)
        return result
        
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error in synthesis and deduplication: {e}")
        logger.debug(f"Response content: {response.content if 'response' in locals() else 'No response'}")
        return items  # Return original items if deduplication fails


async def generate_hierarchical_structure(
    items: List[Dict[str, Any]],
    structure_prompt: str,
    model: Optional[BaseChatModel] = None
) -> Dict[str, Any]:
    """Generate hierarchical structure for items using LLM."""
    
    if model is None:
        model = llm_manager.get_research_model()
    
    system_prompt = f"""You are an expert in regulatory taxonomy and hierarchical organization. Your task is to organize regulatory items into a logical hierarchical structure.

{structure_prompt}

Guidelines:
- Create logical parent-child relationships
- Group related items under appropriate categories
- Maintain consistency in terminology
- Ensure the hierarchy is practical and useful for regulatory analysis
- Include cross-references where items may belong to multiple categories

Respond with a JSON object representing the hierarchical structure."""

    items_json = json.dumps(items, indent=2)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Please organize the following items into a hierarchical structure:\n\n{items_json}")
    ]
    
    try:
        response = await model.ainvoke(messages)
        
        # Parse JSON response
        result = json.loads(response.content)
        return result
        
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error in hierarchical structure generation: {e}")
        logger.debug(f"Response content: {response.content if 'response' in locals() else 'No response'}")
        return {"items": items, "error": str(e)} 