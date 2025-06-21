"""Configuration module for RegGenome Deep Research System."""

import os
import json
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_json_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file."""
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {config_path}: {e}")
            return {}
    return {}


# Load JSON configuration
json_config = load_json_config()


class LLMConfig(BaseModel):
    """LLM configuration for different agents."""
    
    # Load from JSON first, then fall back to environment variables
    provider: str = Field(default_factory=lambda: json_config.get("llm", {}).get("provider") or os.getenv("DEFAULT_LLM_PROVIDER", "openai"))
    
    # Model configurations
    research_model: str = Field(default_factory=lambda: json_config.get("llm", {}).get("models", {}).get("research") or os.getenv("RESEARCH_MODEL", "gpt-4o"))
    extraction_model: str = Field(default_factory=lambda: json_config.get("llm", {}).get("models", {}).get("extraction") or os.getenv("EXTRACTION_MODEL", "gpt-4o-mini"))
    classification_model: str = Field(default_factory=lambda: json_config.get("llm", {}).get("models", {}).get("classification") or os.getenv("CLASSIFICATION_MODEL", "gpt-4o-mini"))
    default_model: str = Field(default_factory=lambda: json_config.get("llm", {}).get("models", {}).get("default") or os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"))
    
    # API Keys - prioritize environment variables for security
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY") or json_config.get("llm", {}).get("api_keys", {}).get("openai", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY") or json_config.get("llm", {}).get("api_keys", {}).get("anthropic", ""))
    
    # LLM Parameters
    temperature: float = Field(default_factory=lambda: json_config.get("llm", {}).get("parameters", {}).get("temperature", 0.1))
    max_tokens: int = Field(default_factory=lambda: json_config.get("llm", {}).get("parameters", {}).get("max_tokens", 4000))
    timeout: int = Field(default_factory=lambda: json_config.get("llm", {}).get("parameters", {}).get("timeout", 60))


class RegGenomeConfig(BaseModel):
    """RegGenome API configuration."""
    
    # JWT authentication is now handled by auth module, but keep fallback for environment
    api_key: str = Field(default_factory=lambda: os.getenv("REGGENOME_API_KEY", ""))
    base_url: str = Field(default_factory=lambda: json_config.get("reggenome", {}).get("api", {}).get("base_url") or os.getenv("REGGENOME_BASE_URL", "https://api.reg-genome.com"))
    max_documents_per_batch: int = Field(default_factory=lambda: json_config.get("reggenome", {}).get("api", {}).get("max_documents_per_batch") or int(os.getenv("MAX_DOCUMENTS_PER_BATCH", "50")))
    max_retries: int = Field(default_factory=lambda: json_config.get("reggenome", {}).get("api", {}).get("max_retries") or int(os.getenv("MAX_RETRIES", "3")))
    request_timeout: int = Field(default_factory=lambda: json_config.get("reggenome", {}).get("api", {}).get("request_timeout") or int(os.getenv("REQUEST_TIMEOUT", "30")))
    
    # JWT token configuration
    use_jwt_auth: bool = Field(default_factory=lambda: json_config.get("reggenome", {}).get("authentication", {}).get("use_jwt") if json_config.get("reggenome") else os.getenv("USE_JWT_AUTH", "true").lower() == "true")
    jwt_token_file: str = Field(default_factory=lambda: json_config.get("reggenome", {}).get("authentication", {}).get("jwt_token_file") or os.getenv("JWT_TOKEN_FILE", "key.txt"))


class ResearchConfig(BaseModel):
    """Research configuration."""
    
    legislative_initiatives: List[str] = Field(
        default_factory=lambda: json_config.get("research", {}).get("legislative_initiatives") or os.getenv(
            "LEGISLATIVE_INITIATIVES", 
            "US - Investment Advisers Act (1940),US - Investment Company Act (1940),EU - UCITS Directives,UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations"
        ).split(",")
    )
    
    # Extraction settings
    entity_types: List[str] = Field(default_factory=lambda: json_config.get("research", {}).get("extraction_settings", {}).get("entity_types", [
        "investment_adviser", "investment_company", "mutual_fund", "hedge_fund", "pension_fund",
        "insurance_company", "bank", "credit_union", "broker_dealer", "investment_bank",
        "asset_manager", "fund_administrator", "other"
    ]))
    
    activity_types: List[str] = Field(default_factory=lambda: json_config.get("research", {}).get("extraction_settings", {}).get("activity_types", [
        "investment_advisory", "portfolio_management", "trading", "compliance", "risk_management",
        "reporting", "custody", "administration", "distribution", "marketing",
        "due_diligence", "governance", "audit", "other"
    ]))
    
    product_types: List[str] = Field(default_factory=lambda: json_config.get("research", {}).get("extraction_settings", {}).get("product_types", [
        "mutual_fund", "etf", "hedge_fund", "private_equity", "ucits", "pension_fund",
        "insurance_product", "structured_product", "derivatives", "securities", "bonds", "other"
    ]))
    
    confidence_threshold: float = Field(default_factory=lambda: json_config.get("research", {}).get("confidence_threshold", 0.7))
    enable_caching: bool = Field(default_factory=lambda: json_config.get("research", {}).get("enable_caching") if json_config.get("research") else os.getenv("ENABLE_CACHING", "true").lower() == "true")
    max_documents_to_process: int = Field(default_factory=lambda: json_config.get("research", {}).get("max_documents_to_process", 20))
    
    # Output configuration
    output_format: str = Field(default_factory=lambda: json_config.get("output", {}).get("format", "json"))
    include_metadata: bool = Field(default_factory=lambda: json_config.get("output", {}).get("include_metadata", True))
    include_sources: bool = Field(default_factory=lambda: json_config.get("output", {}).get("include_sources", True))
    include_confidence_scores: bool = Field(default_factory=lambda: json_config.get("output", {}).get("include_confidence_scores", True))
    default_output_dir: str = Field(default_factory=lambda: json_config.get("output", {}).get("default_output_dir", "output"))
    auto_timestamp: bool = Field(default_factory=lambda: json_config.get("output", {}).get("auto_timestamp", True))


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    log_level: str = Field(default_factory=lambda: json_config.get("logging", {}).get("level") or os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = Field(default_factory=lambda: json_config.get("logging", {}).get("file") or os.getenv("LOG_FILE", "reggenome_research.log"))
    console_output: bool = Field(default_factory=lambda: json_config.get("logging", {}).get("console_output", True))
    max_file_size_mb: int = Field(default_factory=lambda: json_config.get("logging", {}).get("max_file_size_mb", 10))
    backup_count: int = Field(default_factory=lambda: json_config.get("logging", {}).get("backup_count", 5))


class Config(BaseModel):
    """Main configuration class."""
    
    reggenome: RegGenomeConfig = Field(default_factory=RegGenomeConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        
        # Check authentication options
        jwt_available = self.reggenome.use_jwt_auth
        api_key_available = bool(self.reggenome.api_key)
        
        if not jwt_available and not api_key_available:
            errors.append("Either JWT authentication (key.txt) or REGGENOME_API_KEY is required")
            
        if not self.llm.openai_api_key and not self.llm.anthropic_api_key:
            errors.append("At least one LLM API key (OpenAI or Anthropic) is required")
            
        return errors
    
    def get_model_for_task(self, task: str) -> str:
        """Get the appropriate model for a specific task."""
        model_map = {
            "research": self.llm.research_model,
            "extraction": self.llm.extraction_model,
            "classification": self.llm.classification_model,
            "default": self.llm.default_model
        }
        return model_map.get(task, self.llm.default_model)
    
    def save_config(self, output_path: str = "config.json"):
        """Save current configuration to JSON file."""
        config_dict = {
            "llm": {
                "provider": self.llm.provider,
                "models": {
                    "research": self.llm.research_model,
                    "extraction": self.llm.extraction_model,
                    "classification": self.llm.classification_model,
                    "default": self.llm.default_model
                },
                "api_keys": {
                    "openai": "",  # Don't save API keys
                    "anthropic": ""
                },
                "parameters": {
                    "temperature": self.llm.temperature,
                    "max_tokens": self.llm.max_tokens,
                    "timeout": self.llm.timeout
                }
            },
            "reggenome": {
                "authentication": {
                    "use_jwt": self.reggenome.use_jwt_auth,
                    "jwt_token_file": self.reggenome.jwt_token_file
                },
                "api": {
                    "base_url": self.reggenome.base_url,
                    "max_documents_per_batch": self.reggenome.max_documents_per_batch,
                    "max_retries": self.reggenome.max_retries,
                    "request_timeout": self.reggenome.request_timeout
                }
            },
            "research": {
                "legislative_initiatives": self.research.legislative_initiatives,
                "extraction_settings": {
                    "entity_types": self.research.entity_types,
                    "activity_types": self.research.activity_types,
                    "product_types": self.research.product_types
                },
                "confidence_threshold": self.research.confidence_threshold,
                "enable_caching": self.research.enable_caching
            },
            "output": {
                "format": self.research.output_format,
                "include_metadata": self.research.include_metadata,
                "include_sources": self.research.include_sources,
                "include_confidence_scores": self.research.include_confidence_scores,
                "default_output_dir": self.research.default_output_dir,
                "auto_timestamp": self.research.auto_timestamp
            },
            "logging": {
                "level": self.logging.log_level,
                "file": self.logging.log_file,
                "console_output": self.logging.console_output,
                "max_file_size_mb": self.logging.max_file_size_mb,
                "backup_count": self.logging.backup_count
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)


# Global configuration instance
config = Config() 