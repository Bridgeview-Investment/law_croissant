"""Configuration module for RegGenome Deep Research System."""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class RegGenomeConfig(BaseModel):
    """RegGenome API configuration."""
    
    api_key: str = Field(default_factory=lambda: os.getenv("REGGENOME_API_KEY", ""))
    base_url: str = Field(default_factory=lambda: os.getenv("REGGENOME_BASE_URL", "https://api.reg-genome.com/api/v1"))
    max_documents_per_batch: int = Field(default_factory=lambda: int(os.getenv("MAX_DOCUMENTS_PER_BATCH", "50")))
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    request_timeout: int = Field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30")))


class LLMConfig(BaseModel):
    """LLM configuration for different agents."""
    
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    
    default_provider: str = Field(default_factory=lambda: os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
    default_model: str = Field(default_factory=lambda: os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"))
    research_model: str = Field(default_factory=lambda: os.getenv("RESEARCH_MODEL", "gpt-4o"))
    extraction_model: str = Field(default_factory=lambda: os.getenv("EXTRACTION_MODEL", "gpt-4o-mini"))
    classification_model: str = Field(default_factory=lambda: os.getenv("CLASSIFICATION_MODEL", "gpt-4o-mini"))


class ResearchConfig(BaseModel):
    """Research configuration."""
    
    legislative_initiatives: List[str] = Field(
        default_factory=lambda: os.getenv(
            "LEGISLATIVE_INITIATIVES", 
            "US - Investment Advisers Act (1940),US - Investment Company Act (1940),EU - UCITS Directives,UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations"
        ).split(",")
    )
    enable_caching: bool = Field(default_factory=lambda: os.getenv("ENABLE_CACHING", "true").lower() == "true")
    
    # Output configuration
    output_format: str = "json"
    include_metadata: bool = True
    include_sources: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = Field(default_factory=lambda: os.getenv("LOG_FILE", "reggenome_research.log"))


class Config(BaseModel):
    """Main configuration class."""
    
    reggenome: RegGenomeConfig = Field(default_factory=RegGenomeConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        if not self.reggenome.api_key:
            errors.append("REGGENOME_API_KEY is required")
            
        if not self.llm.openai_api_key and not self.llm.anthropic_api_key:
            errors.append("At least one LLM API key (OpenAI or Anthropic) is required")
            
        return errors


# Global configuration instance
config = Config() 