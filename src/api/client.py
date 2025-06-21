import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from dotenv import load_dotenv

from .exceptions import (
    RegGenomeAPIError,
    AuthenticationError,
    RateLimitError,
    DataNotFoundError,
    ValidationError
)

load_dotenv()


class RegGenomeClient:
    """Async client for RegGenome API with JWT authentication"""
    
    def __init__(self, access_token: Optional[str] = None):
        # Try access token from parameter, then environment, then file
        self.access_token = access_token or os.getenv("REGGENOME_ACCESS_TOKEN")
        
        if not self.access_token:
            # Try to load from API response file
            api_file = os.getenv("REGGENOME_API_FILE", "../reggenome_api.md")
            if os.path.exists(api_file):
                self.access_token = self._extract_token_from_file(api_file)
        
        if not self.access_token:
            raise AuthenticationError("RegGenome access token not provided")
        
        self.base_url = os.getenv("REGGENOME_API_URL", "https://api.reg-genome.com/api/v1")
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting
        self.max_concurrent = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Client configuration
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "60"))
        self.client = None
        
        logger.info(f"RegGenome client initialized with base URL: {self.base_url}")
    
    def _extract_token_from_file(self, filepath: str) -> Optional[str]:
        """Extract access token from authentication response file"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                # Remove any trailing characters after JSON
                content = content.strip()
                if content.endswith('%'):
                    content = content[:-1]
                # Parse JSON response
                auth_data = json.loads(content)
                if "AuthenticationResult" in auth_data:
                    return auth_data["AuthenticationResult"]["AccessToken"]
        except Exception as e:
            logger.error(f"Failed to extract token from file: {e}")
        return None
    
    async def __aenter__(self):
        # Create client with SSL verification handling
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            http2=True,
            verify=False  # Disable SSL verification for development
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make an API request with retry logic"""
        async with self.semaphore:
            url = f"{self.base_url}{endpoint}"
            
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    raise AuthenticationError("Authentication failed")
                elif response.status_code == 404:
                    raise DataNotFoundError(f"Resource not found: {endpoint}")
                elif response.status_code == 422:
                    raise ValidationError(f"Validation error: {response.text}")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                else:
                    raise RegGenomeAPIError(f"API error: {response.status_code} - {response.text}")
                    
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise RegGenomeAPIError(f"Request failed: {str(e)}")
    
    async def get_documents(
        self,
        publishers: Optional[List[Dict]] = None,
        initiatives: Optional[List[int]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        doctypes: Optional[List[str]] = None,
        required_tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 100
    ) -> List[Dict]:
        """Fetch documents with filtering"""
        
        json_data = {
            "publishers": publishers,
            "initiatives": initiatives,
            "start_date": start_date,
            "end_date": end_date,
            "doctypes": doctypes,
            "required_tags": required_tags,
            "remove_near_duplicates": True
        }
        
        # Remove None values
        json_data = {k: v for k, v in json_data.items() if v is not None}
        
        params = {"page": page, "page_size": page_size}
        
        logger.info(f"Fetching documents page {page} with filters: {json_data}")
        
        result = await self._make_request(
            method="POST",
            endpoint="/customer/documents",
            params=params,
            json_data=json_data
        )
        
        return result
    
    async def get_document_metadata(self, document_id: str) -> Dict:
        """Get detailed metadata for a specific document"""
        logger.info(f"Fetching metadata for document: {document_id}")
        
        return await self._make_request(
            method="GET",
            endpoint=f"/customer/documents/{document_id}"
        )
    
    async def get_initiatives(self) -> List[Dict]:
        """Get list of available initiatives"""
        logger.info("Fetching available initiatives")
        
        result = await self._make_request(
            method="GET",
            endpoint="/customer/initiatives"
        )
        
        return result.get("initiatives", [])
    
    async def get_publishers(self, jurisdictions: Optional[List[str]] = None) -> List[str]:
        """Get list of publishers"""
        params = {"jurisdictions": jurisdictions} if jurisdictions else None
        
        result = await self._make_request(
            method="GET",
            endpoint="/customer/publishers",
            params=params
        )
        
        return result.get("publishers", [])
    
    async def get_document_counts(self, filters: Dict) -> int:
        """Get count of documents matching filters"""
        result = await self._make_request(
            method="POST",
            endpoint="/customer/document_counts",
            json_data=filters
        )
        
        return result.get("count", 0)
    
    async def fetch_all_documents_for_initiatives(
        self,
        initiative_ids_or_names: List[Any],
        batch_size: int = 100
    ) -> List[Dict]:
        """Fetch all documents for specified initiatives (by ID or name)"""
        
        initiative_ids = []
        
        # Check if we have IDs or names
        for item in initiative_ids_or_names:
            if isinstance(item, int):
                # It's already an ID
                initiative_ids.append(item)
            else:
                # It's a name, need to find ID
                initiatives = await self.get_initiatives()
                for init in initiatives:
                    if init.get("name") == str(item):
                        initiative_ids.append(init.get("id"))
                        break
        
        if not initiative_ids:
            logger.warning(f"No initiatives found matching: {initiative_ids_or_names}")
            return []
        
        logger.info(f"Using initiative IDs: {initiative_ids}")
        
        # Get total count
        count = await self.get_document_counts({"initiatives": initiative_ids})
        logger.info(f"Total documents to fetch: {count}")
        
        # Fetch all pages
        all_documents = []
        total_pages = (count + batch_size - 1) // batch_size
        
        tasks = []
        for page in range(1, total_pages + 1):
            task = self.get_documents(
                initiatives=initiative_ids,
                page=page,
                page_size=batch_size
            )
            tasks.append(task)
        
        # Execute in batches to avoid overwhelming the API
        batch_results = []
        for i in range(0, len(tasks), self.max_concurrent):
            batch = tasks[i:i + self.max_concurrent]
            results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Error fetching batch: {result}")
                else:
                    batch_results.extend(result)
        
        logger.info(f"Successfully fetched {len(batch_results)} documents")
        return batch_results
    
    async def interrogator_search(
        self,
        query: str,
        publishers: Optional[List[Dict]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        doctypes: Optional[List[str]] = None
    ) -> List[Dict]:
        """Search using Interrogator API (initiatives filtering not supported)"""
        
        json_data = {
            "query": query,
            "publishers": publishers,
            "start_date": start_date,
            "end_date": end_date,
            "doctypes": doctypes
        }
        
        # Remove None values
        json_data = {k: v for k, v in json_data.items() if v is not None}
        
        result = await self._make_request(
            method="POST",
            endpoint="/customer/interrogator/search",
            json_data=json_data
        )
        
        return result.get("results", [])