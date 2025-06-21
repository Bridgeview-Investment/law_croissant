from typing import Optional
import os
from pathlib import Path

class Config:
    """Configuration for the Deep Research System"""
    
    def __init__(self):
        self.api_key_path = Path("key.txt")
        self.api_base_url = "https://api.reg-genome.com/api/v1"
        self.max_pages_per_query = 10
        self.page_size = 100
        self.concurrent_agents = 3
        self.extraction_model = "gpt-4"  # placeholder for LLM model
        
        # Initiative IDs from the task description
        self.initiative_filters = {
            "us_investment_advisers": "US - Investment Advisers Act (1940)",
            "us_investment_company": "US - Investment Company Act, 1940", 
            "eu_ucits": "EU - UCITS Directives",
            "uk_ucits": "UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations, 2011 - 2016"
        }
        
    def get_api_key(self) -> str:
        """Load API key from file"""
        if self.api_key_path.exists():
            content = self.api_key_path.read_text().strip()
            # The key.txt contains multiple tokens, extract just the access token
            # which is the first part before ","ExpiresIn"
            if '","ExpiresIn"' in content:
                # Extract just the JWT token part
                token = content.split('","ExpiresIn"')[0]
                # Remove any leading quotes
                token = token.strip('"')
                return token
            else:
                # If it's already just a token, return as is
                return content
        raise ValueError(f"API key not found at {self.api_key_path}")
    
    @property
    def headers(self) -> dict:
        """Get request headers with authorization"""
        return {
            "Authorization": f"Bearer {self.get_api_key()}",
            "Content-Type": "application/json"
        }