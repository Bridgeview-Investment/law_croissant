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
from .auth import token_manager


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
        
        # Use JWT authentication if available and enabled
        self.use_jwt = config.reggenome.use_jwt_auth
        
        if self.use_jwt:
            jwt_token = token_manager.get_access_token()
            if jwt_token:
                logger.info("Using JWT authentication for RegGenome API")
                if token_manager.is_token_expired():
                    logger.warning("JWT token appears to be expired")
                else:
                    token_info = token_manager.get_token_info()
                    if token_info.get('expires_at'):
                        logger.info(f"JWT token expires at: {token_info['expires_at']}")
            else:
                logger.warning("JWT authentication enabled but no token available")
                self.use_jwt = False
        
        if not self.use_jwt and not self.api_key:
            logger.warning("No RegGenome authentication available. Some functionality may be limited.")
    
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
            
            # Set up authentication headers
            if self.use_jwt:
                jwt_token = token_manager.get_access_token()
                if jwt_token:
                    auth_header = f'Bearer {jwt_token}'
                    logger.debug("Using JWT Bearer token for authentication")
                else:
                    logger.error("JWT authentication enabled but no token available")
                    auth_header = ''
            else:
                auth_header = f'Bearer {self.api_key}' if self.api_key else ''
                logger.debug("Using API key for authentication")
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'RegGenome-DeepResearch/1.0'
            }
            
            if auth_header:
                headers['Authorization'] = auth_header
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _check_token_refresh(self):
        """Check if JWT token needs to be refreshed."""
        if self.use_jwt and token_manager.is_token_expired():
            logger.warning("JWT token has expired. Consider refreshing the token.")
            # Note: Token refresh would need to be implemented based on RegGenome's refresh mechanism
            # For now, we'll continue with the expired token and let the API return 401 if needed
    
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
        
        # Check token status if using JWT
        self._check_token_refresh()
        
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
                    if self.use_jwt:
                        token_info = token_manager.get_token_info()
                        if token_info.get('is_expired'):
                            raise RegGenomeAPIError("JWT token has expired. Please refresh your authentication.")
                        else:
                            raise RegGenomeAPIError("JWT authentication failed. Check your token validity.")
                    else:
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
        endpoint = f"/api/v1/customer/documents/{document_id}"
        return await self._make_request("GET", endpoint)
    
    async def get_document_file(self, document_id: str) -> str:
        """Get document file URL (returns presigned S3 URL)."""
        endpoint = f"/api/v1/customer/documents/{document_id}/file"
        # This endpoint returns a 307 redirect to S3 presigned URL
        response = await self._make_request("GET", endpoint)
        return response
    
    async def search_documents(
        self,
        query: Optional[str] = None,
        publishers: Optional[List[Dict[str, Any]]] = None,
        initiatives: Optional[List[int]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        doctypes: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """Search for documents using RegGenome API filters."""
        endpoint = "/api/v1/customer/documents"
        
        # Build filter payload according to RegGenome API documentation
        filter_data = {
            "remove_near_duplicates": False,
            "document_restriction": ["unrestricted", "partially_restricted"]
        }
        
        # Add optional filters
        if publishers:
            filter_data["publishers"] = publishers
        if initiatives:
            filter_data["initiatives"] = initiatives
        if start_date:
            filter_data["start_date"] = start_date
        if end_date:
            filter_data["end_date"] = end_date
        if doctypes:
            filter_data["doctypes"] = doctypes
        if query:
            filter_data["title"] = query
            
        # Add pagination
        params = {
            "page": page,
            "page_size": page_size
        }
            
        return await self._make_request("POST", endpoint, params=params, data=filter_data)
    
    async def get_legislative_initiatives(self) -> List[Dict[str, Any]]:
        """Get available legislative initiatives."""
        endpoint = "/api/v1/customer/initiatives"
        try:
            response = await self._make_request("GET", endpoint)
            return response.get("initiatives", [])
        except RegGenomeAPIError:
            # Fallback to configured initiatives if API call fails
            return [{"name": initiative, "id": i+1} for i, initiative in enumerate(config.research.legislative_initiatives)]
    
    async def get_documents_by_legislative_initiative(
        self,
        initiative_id: int,
        page_size: int = 100,
        max_documents: int = 10  # Limit documents per initiative
    ) -> AsyncGenerator[RegGenomeDocument, None]:
        """Get documents for a specific legislative initiative with limit."""
        page = 1
        total_yielded = 0
        
        while total_yielded < max_documents:
            try:
                response = await self.search_documents(
                    initiatives=[initiative_id],
                    page=page,
                    page_size=min(page_size, config.reggenome.max_documents_per_batch)
                )
                
                documents = response if isinstance(response, list) else response.get("documents", [])
                if not documents:
                    break
                
                for doc_data in documents:
                    if total_yielded >= max_documents:
                        break
                        
                    # Extract content from source_text if available
                    try:
                        if doc_data.get("source_text") and isinstance(doc_data["source_text"], list):
                            doc_data["content"] = "\n".join([
                                text.get("text", "") for text in doc_data["source_text"] 
                                if isinstance(text, dict) and text.get("text")
                            ])
                        if not doc_data.get("content"):
                            doc_data["content"] = doc_data.get("title", "")
                    except Exception as e:
                        logger.warning(f"Failed to extract content for document {doc_data.get('document_id', 'unknown')}: {e}")
                        doc_data["content"] = doc_data.get("title", "")
                    
                    yield self._parse_document(doc_data)
                    total_yielded += 1
                
                # Check if we've reached the limit or end of documents
                if total_yielded >= max_documents or len(documents) < min(page_size, config.reggenome.max_documents_per_batch):
                    break
                    
                page += 1
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except RegGenomeAPIError as e:
                logger.error(f"Error fetching documents for initiative {initiative_id}: {e}")
                break
    
    async def get_all_relevant_documents(self) -> AsyncGenerator[RegGenomeDocument, None]:
        """Get all documents from configured legislative initiatives."""
        initiatives = await self.get_legislative_initiatives()
        
        for initiative in initiatives:
            initiative_name = initiative.get("name", f"Initiative {initiative.get('id', 'unknown')}")
            initiative_id = initiative.get("id")
            
            if initiative_id:
                logger.info(f"Fetching documents for initiative: {initiative_name} (ID: {initiative_id})")
                async for document in self.get_documents_by_legislative_initiative(initiative_id, max_documents=5):
                    yield document
            else:
                logger.warning(f"Skipping initiative without ID: {initiative_name}")
    
    def _parse_document(self, doc_data: Dict[str, Any]) -> RegGenomeDocument:
        """Parse API response data into RegGenomeDocument model."""
        # Parse publication date
        publication_date = None
        if doc_data.get("published"):
            try:
                publication_date = datetime.fromisoformat(doc_data["published"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse publication date: {doc_data.get('published')}")
        
        # Parse document type
        document_type = None
        if doc_data.get("doctype"):
            try:
                document_type = DocumentType(doc_data["doctype"].lower())
            except ValueError:
                document_type = DocumentType.OTHER
        
        # Extract content from source_text if available
        content = doc_data.get("content", "")
        if not content and doc_data.get("source_text"):
            content = "\n".join([text.get("text", "") for text in doc_data["source_text"] if text.get("text")])
        
        # Extract publisher information
        publisher = None
        if doc_data.get("publishers") and len(doc_data["publishers"]) > 0:
            publisher = doc_data["publishers"][0].get("name", doc_data["publishers"][0].get("id", ""))
        
        # Extract jurisdiction from publishers
        jurisdiction = None
        if doc_data.get("publishers"):
            for pub in doc_data["publishers"]:
                if pub.get("jurisdiction"):
                    jurisdiction = pub["jurisdiction"]
                    break
        
        # Extract initiative information
        legislative_initiative = None
        if doc_data.get("initiatives") and len(doc_data["initiatives"]) > 0:
            legislative_initiative = doc_data["initiatives"][0].get("name", "")
        
        return RegGenomeDocument(
            document_id=doc_data.get("document_id", ""),
            title=doc_data.get("title", ""),
            content=content,
            url=doc_data.get("source_urls", [None])[0] if doc_data.get("source_urls") else None,
            publisher=publisher,
            publication_date=publication_date,
            document_type=document_type,
            jurisdiction=jurisdiction,
            legislative_initiative=legislative_initiative,
            metadata={
                "authoritative": doc_data.get("authoritative", []),
                "sector": doc_data.get("sector", {}),
                "reg_scores": doc_data.get("reg_scores", {}),
                "languages": doc_data.get("languages", {}),
                "restriction": doc_data.get("restriction", ""),
                "last_updated": doc_data.get("last_updated", "")
            },
            sections=doc_data.get("signposts") or [],
            thematic_tags=[],  # Not directly available in new API
            relevance_scores={
                domain: score.get("reg_score", 0.0) if isinstance(score, dict) else score 
                for domain, score in doc_data.get("reg_scores", {}).items()
            }
        )


class MockRegGenomeAPIClient(RegGenomeAPIClient):
    """Mock client for testing without actual API access."""
    
    def __init__(self):
        super().__init__(api_key="mock_key", base_url="https://mock.reg-genome.com")
    
    async def get_legislative_initiatives(self) -> List[Dict[str, Any]]:
        """Return mock initiatives."""
        return [
            {"id": 1, "name": "US - Investment Advisers Act (1940)"},
            {"id": 2, "name": "EU - UCITS Directives"}
        ]
    
    async def get_all_relevant_documents(self) -> AsyncGenerator[RegGenomeDocument, None]:
        """Return mock documents for testing."""
        mock_documents = [
            {
                "document_id": "mock_doc_1",
                "title": "Investment Advisers Act of 1940 - Section 3(a)(1)",
                "published": "1940-08-22",
                "doctype": "act",
                "publishers": [{"name": "SEC", "jurisdiction": "US"}],
                "initiatives": [{"name": "US - Investment Advisers Act (1940)", "id": 1}],
                "source_text": [
                    {
                        "text": """For the purposes of this title, the term "investment adviser" means any person who, 
                        for compensation, engages in the business of advising others, either directly or 
                        through publications or writings, as to the value of securities or as to the 
                        advisability of investing in, purchasing, or selling securities, or who, for 
                        compensation and as part of a regular business, issues or promulgates analyses 
                        or reports concerning securities."""
                    }
                ],
                "authoritative": ["securities"],
                "sector": {"level_1": "financial_services"},
                "reg_scores": {"securities": 0.95},
                "languages": {"en": 1.0},
                "restriction": "unrestricted",
                "signposts": [{"id": "3a1", "title": "Definition of Investment Adviser"}],
                "source_urls": ["https://www.sec.gov/about/laws/iaa40.pdf"]
            },
            {
                "document_id": "mock_doc_2", 
                "title": "UCITS Directive - Definition of UCITS",
                "published": "2009-07-13",
                "doctype": "directive",
                "publishers": [{"name": "European Commission", "jurisdiction": "EU"}],
                "initiatives": [{"name": "EU - UCITS Directives", "id": 2}],
                "source_text": [
                    {
                        "text": """'UCITS' means an undertaking for collective investment in transferable securities
                        which is subject to the restrictions on the types of assets in which it may invest.
                        Such undertakings may be constituted according to the law of contract (as common funds
                        managed by management companies) or trust law (as unit trusts) or under statute
                        (as investment companies)."""
                    }
                ],
                "authoritative": ["investment_funds"],
                "sector": {"level_1": "financial_services"},
                "reg_scores": {"investment_funds": 0.90},
                "languages": {"en": 1.0},
                "restriction": "unrestricted",
                "signposts": [{"id": "art1", "title": "Definitions"}],
                "source_urls": ["https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009L0065"]
            }
        ]
        
        for doc_data in mock_documents:
            yield self._parse_document(doc_data)
            await asyncio.sleep(0.1)  # Simulate API delay 