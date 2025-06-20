"""RegGenome API client for document retrieval."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
import aiohttp
import time
from urllib.parse import urljoin

from .config import config
from .models import RegGenomeDocument, DocumentType


logger = logging.getLogger(__name__)


class RegGenomeAPIError(Exception):
    """RegGenome API specific exception."""
    pass


class RegGenomeAPIClient:
    """Client for interacting with RegGenome API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the API client."""
        self.api_key = api_key or config.reggenome.api_key
        self.base_url = base_url or config.reggenome.base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_timeout = config.reggenome.request_timeout
        self.max_retries = config.reggenome.max_retries
        
        if not self.api_key:
            logger.warning("No RegGenome API key provided. Some functionality may be limited.")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.request_timeout)
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'RegGenome-DeepResearch/1.0'
            }
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retries: int = 0
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        await self._ensure_session()
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:  # Rate limited
                    if retries < self.max_retries:
                        wait_time = 2 ** retries
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(method, endpoint, params, data, retries + 1)
                    else:
                        raise RegGenomeAPIError(f"Rate limited after {self.max_retries} retries")
                elif response.status == 401:
                    raise RegGenomeAPIError("Authentication failed. Check your API key.")
                elif response.status == 404:
                    raise RegGenomeAPIError(f"Endpoint not found: {endpoint}")
                else:
                    error_text = await response.text()
                    raise RegGenomeAPIError(f"API request failed with status {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            if retries < self.max_retries:
                wait_time = 2 ** retries
                logger.warning(f"Request failed: {e}. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                return await self._make_request(method, endpoint, params, data, retries + 1)
            else:
                raise RegGenomeAPIError(f"Request failed after {self.max_retries} retries: {e}")
    
    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get metadata for a specific document."""
        endpoint = f"/customer/documents/{document_id}"
        return await self._make_request("GET", endpoint)
    
    async def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Get full content for a specific document."""
        endpoint = f"/customer/documents/{document_id}/content"
        return await self._make_request("GET", endpoint)
    
    async def search_documents(
        self,
        query: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        publisher: Optional[str] = None,
        document_type: Optional[str] = None,
        legislative_initiative: Optional[str] = None,
        publication_date_from: Optional[str] = None,
        publication_date_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search for documents based on criteria."""
        endpoint = "/customer/documents/search"
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # Add optional parameters
        if query:
            params["query"] = query
        if jurisdiction:
            params["jurisdiction"] = jurisdiction
        if publisher:
            params["publisher"] = publisher
        if document_type:
            params["document_type"] = document_type
        if legislative_initiative:
            params["legislative_initiative"] = legislative_initiative
        if publication_date_from:
            params["publication_date_from"] = publication_date_from
        if publication_date_to:
            params["publication_date_to"] = publication_date_to
            
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_legislative_initiatives(self) -> List[str]:
        """Get available legislative initiatives."""
        endpoint = "/customer/legislative-initiatives"
        try:
            response = await self._make_request("GET", endpoint)
            return response.get("initiatives", [])
        except RegGenomeAPIError:
            # Fallback to configured initiatives if API call fails
            return config.research.legislative_initiatives
    
    async def get_documents_by_legislative_initiative(
        self,
        initiative: str,
        limit: int = 100
    ) -> AsyncGenerator[RegGenomeDocument, None]:
        """Get all documents for a specific legislative initiative."""
        offset = 0
        
        while True:
            try:
                response = await self.search_documents(
                    legislative_initiative=initiative,
                    limit=min(limit, config.reggenome.max_documents_per_batch),
                    offset=offset
                )
                
                documents = response.get("documents", [])
                if not documents:
                    break
                
                for doc_data in documents:
                    # Get full content for each document
                    try:
                        content_response = await self.get_document_content(doc_data["id"])
                        doc_data["content"] = content_response.get("content", "")
                    except RegGenomeAPIError as e:
                        logger.warning(f"Failed to get content for document {doc_data['id']}: {e}")
                        doc_data["content"] = ""
                    
                    yield self._parse_document(doc_data)
                
                # Check if we've reached the end
                if len(documents) < config.reggenome.max_documents_per_batch:
                    break
                    
                offset += len(documents)
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except RegGenomeAPIError as e:
                logger.error(f"Error fetching documents for initiative {initiative}: {e}")
                break
    
    async def get_all_relevant_documents(self) -> AsyncGenerator[RegGenomeDocument, None]:
        """Get all documents from configured legislative initiatives."""
        initiatives = await self.get_legislative_initiatives()
        
        for initiative in initiatives:
            logger.info(f"Fetching documents for initiative: {initiative}")
            async for document in self.get_documents_by_legislative_initiative(initiative):
                yield document
    
    def _parse_document(self, doc_data: Dict[str, Any]) -> RegGenomeDocument:
        """Parse API response data into RegGenomeDocument model."""
        # Parse publication date
        publication_date = None
        if doc_data.get("publication_date"):
            try:
                publication_date = datetime.fromisoformat(doc_data["publication_date"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse publication date: {doc_data.get('publication_date')}")
        
        # Parse document type
        document_type = None
        if doc_data.get("document_type"):
            try:
                document_type = DocumentType(doc_data["document_type"].lower())
            except ValueError:
                document_type = DocumentType.OTHER
        
        return RegGenomeDocument(
            document_id=doc_data["id"],
            title=doc_data.get("title", ""),
            content=doc_data.get("content", ""),
            url=doc_data.get("url"),
            publisher=doc_data.get("publisher"),
            publication_date=publication_date,
            document_type=document_type,
            jurisdiction=doc_data.get("jurisdiction"),
            legislative_initiative=doc_data.get("legislative_initiative"),
            metadata=doc_data.get("metadata", {}),
            sections=doc_data.get("sections", []),
            thematic_tags=doc_data.get("thematic_tags", []),
            relevance_scores=doc_data.get("relevance_scores", {})
        )


class MockRegGenomeAPIClient(RegGenomeAPIClient):
    """Mock client for testing without actual API access."""
    
    def __init__(self):
        super().__init__(api_key="mock_key", base_url="https://mock.reg-genome.com")
    
    async def get_all_relevant_documents(self) -> AsyncGenerator[RegGenomeDocument, None]:
        """Return mock documents for testing."""
        mock_documents = [
            {
                "id": "mock_doc_1",
                "title": "Investment Advisers Act of 1940 - Section 3(a)(1)",
                "content": """
                For the purposes of this title, the term "investment adviser" means any person who, 
                for compensation, engages in the business of advising others, either directly or 
                through publications or writings, as to the value of securities or as to the 
                advisability of investing in, purchasing, or selling securities, or who, for 
                compensation and as part of a regular business, issues or promulgates analyses 
                or reports concerning securities.
                """,
                "publisher": "SEC",
                "publication_date": "1940-08-22T00:00:00Z",
                "document_type": "act",
                "jurisdiction": "US",
                "legislative_initiative": "US - Investment Advisers Act (1940)",
                "metadata": {"section": "3(a)(1)"},
                "sections": [{"id": "3a1", "title": "Definition of Investment Adviser"}],
                "thematic_tags": ["definition", "investment_adviser"]
            },
            {
                "id": "mock_doc_2",
                "title": "UCITS Directive - Definition of UCITS",
                "content": """
                'UCITS' means an undertaking for collective investment in transferable securities
                which is subject to the restrictions on the types of assets in which it may invest.
                Such undertakings may be constituted according to the law of contract (as common funds
                managed by management companies) or trust law (as unit trusts) or under statute
                (as investment companies).
                """,
                "publisher": "European Commission",
                "publication_date": "2009-07-13T00:00:00Z",
                "document_type": "directive",
                "jurisdiction": "EU",
                "legislative_initiative": "EU - UCITS Directives",
                "metadata": {"article": "1"},
                "sections": [{"id": "art1", "title": "Definitions"}],
                "thematic_tags": ["definition", "ucits", "collective_investment"]
            }
        ]
        
        for doc_data in mock_documents:
            yield self._parse_document(doc_data)
            await asyncio.sleep(0.1)  # Simulate API delay 