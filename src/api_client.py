import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from src.config import Config
from src.models import Document

class RegGenomeAPIClient:
    """Async client for RegGenome API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.api_base_url
        self.headers = config.headers
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_documents(self, 
                            initiatives: Optional[List[int]] = None,
                            page: int = 1,
                            page_size: int = 100) -> Dict[str, Any]:
        """Fetch documents with filters"""
        url = f"{self.base_url}/customer/documents"
        
        payload = {
            "page_size": page_size,
            "document_restriction": ["unrestricted", "partially_restricted"]
        }
        
        if initiatives:
            payload["initiatives"] = initiatives
            
        params = {"page": page, "page_size": page_size}
        
        async with self.session.post(url, json=payload, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get detailed document metadata"""
        url = f"{self.base_url}/customer/documents/{document_id}"
        
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_initiatives(self) -> List[Dict[str, Any]]:
        """Get list of available initiatives"""
        url = f"{self.base_url}/customer/initiatives"
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    # print(f"[info] Initiatives API returned status: {response.status}")
                    # print(f"[info] URL: {url}")
                    # print(f"[info] Headers: {self.session.headers}")
                    response.raise_for_status()
                data = await response.json()
                return data.get("initiatives", [])
        except Exception as e:
            # print(f"[info] Error fetching initiatives: {e}")
            # Return empty list if initiatives endpoint fails
            # We can still proceed with document fetching
            return []
    
    async def fetch_all_documents_for_initiatives(self, 
                                                initiative_names: List[str]) -> List[Document]:
        """Fetch all documents for specified initiatives"""
        # First try to get initiative mappings
        all_initiatives = await self.get_initiatives()
        
        # Map initiative names to IDs if we got them
        initiative_ids = []
        if all_initiatives:
            for init in all_initiatives:
                if any(name in init.get("name", "") for name in initiative_names):
                    initiative_ids.append(init["id"])
            # print(f"[info] Found {len(initiative_ids)} matching initiatives")
        else:
            # print("[info] No initiatives data available, proceeding without initiative filter")
            pass
        
        documents = []
        page = 1
        
        while len(documents) < self.config.max_pages_per_query * self.config.page_size:
            try:
                # Only pass initiatives if we have them
                kwargs = {
                    "page": page,
                    "page_size": self.config.page_size
                }
                if initiative_ids:
                    kwargs["initiatives"] = initiative_ids
                    
                response = await self.fetch_documents(**kwargs)
                
                batch = response if isinstance(response, list) else response.get("documents", [])
                if not batch:
                    break
                    
                # Convert to Document objects
                for doc_data in batch:
                    doc = Document(
                        document_id=doc_data["document_id"],
                        title=doc_data["title"],
                        publishers=doc_data.get("publishers", []),
                        published=doc_data.get("published", ""),
                        source_text=doc_data.get("source_text", []),
                        signposts=doc_data.get("signposts", []),
                        initiatives=doc_data.get("initiatives", []),
                        metadata=doc_data
                    )
                    documents.append(doc)
                
                page += 1
                # print(f"[info] Fetched page {page}, total documents: {len(documents)}")
                
            except Exception as e:
                # print(f"[info] Error fetching page {page}: {e}")
                break
                
        return documents