"""Product extraction agent for identifying regulated products in regulatory documents."""

import logging
import hashlib
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from ..models import RegGenomeDocument, RegulatedProduct, ProductType
from ..llm_utils import extract_structured_data, llm_manager

logger = logging.getLogger(__name__)


class ProductExtractionResult(BaseModel):
    """Result model for product extraction."""
    
    products: List[Dict[str, Any]] = Field(description="List of extracted products")
    confidence_score: float = Field(description="Overall confidence in extraction", ge=0.0, le=1.0)
    reasoning: str = Field(description="Explanation of extraction process")


class ProductExtractionAgent:
    """Agent for extracting regulated products from regulatory documents."""
    
    def __init__(self):
        self.extraction_prompt = self._build_extraction_prompt()
    
    def _build_extraction_prompt(self) -> str:
        """Build the product extraction prompt."""
        product_types = [p.value for p in ProductType]
        
        return f"""
You are an expert in regulatory document analysis specializing in identifying regulated financial products.

Your task is to extract all regulated products mentioned in the document. These include:

**Product Types to Look For:**
{', '.join(product_types)}

**What to Extract:**
1. **Product Name**: The exact name or term as it appears in the document
2. **Product Type**: Classify using the provided product types
3. **Description**: A clear description of what this product is
4. **Definition Context**: The surrounding text that defines or describes the product
5. **Regulatory Classification**: How the product is classified for regulatory purposes
6. **Compliance Requirements**: Any specific compliance requirements for this product
7. **Applicable Entities**: Types of entities that can offer or manage this product

**Instructions:**
- Focus on financial products that are explicitly regulated or defined
- Look for investment products, collective investment schemes, financial instruments
- Pay attention to product classifications, eligibility criteria, and regulatory treatment
- Include products subject to specific regulatory frameworks (UCITS, mutual funds, etc.)
- Capture distribution restrictions, licensing requirements, and compliance obligations
- Be precise with terminology - use exact terms from the document
- Provide confidence scores based on how clearly the product is defined

**Examples of Regulated Products:**
- Mutual funds, ETFs, hedge funds, private funds
- UCITS, collective investment schemes, investment trusts
- Securities, derivatives, structured products
- Pension funds, retirement products
- Insurance-linked products, annuities
- Alternative investment funds

Extract all relevant products with their complete regulatory context and classification.
"""
    
    async def extract_products(self, document: RegGenomeDocument) -> List[RegulatedProduct]:
        """Extract regulated products from a document."""
        logger.info(f"Extracting products from document: {document.title}")
        
        try:
            # Prepare content for extraction
            content = self._prepare_content(document)
            
            # Extract products using LLM
            extraction_result = await extract_structured_data(
                content=content,
                extraction_prompt=self.extraction_prompt,
                response_model=ProductExtractionResult,
                model=llm_manager.get_extraction_model()
            )
            
            # Convert to RegulatedProduct models
            products = []
            for product_data in extraction_result.products:
                product = self._create_regulated_product(product_data, document)
                products.append(product)
            
            logger.info(f"Extracted {len(products)} products from document {document.document_id}")
            return products
            
        except Exception as e:
            logger.error(f"Error extracting products from document {document.document_id}: {e}")
            return []
    
    def _prepare_content(self, document: RegGenomeDocument) -> str:
        """Prepare document content for product extraction."""
        content_parts = [
            f"**Document Title:** {document.title}",
            f"**Document Type:** {document.document_type}",
            f"**Jurisdiction:** {document.jurisdiction}",
            f"**Legislative Initiative:** {document.legislative_initiative}",
            f"**Publisher:** {document.publisher}",
        ]
        
        # Add thematic tags if available
        if document.thematic_tags:
            content_parts.append(f"**Thematic Tags:** {', '.join(document.thematic_tags)}")
        
        # Add main content
        content_parts.append("**Document Content:**")
        content_parts.append(document.content)
        
        # Add section information if available
        if document.sections:
            content_parts.append("**Document Sections:**")
            for section in document.sections:
                content_parts.append(f"- {section.get('title', 'Untitled')}: {section.get('content', '')}")
        
        return "\n\n".join(content_parts)
    
    def _create_regulated_product(self, product_data: Dict[str, Any], document: RegGenomeDocument) -> RegulatedProduct:
        """Create a RegulatedProduct from extracted data."""
        # Generate product ID based on name and type
        product_name = product_data.get("name", "").strip()
        product_type_str = product_data.get("product_type", "other").lower()
        
        # Map product type
        try:
            product_type = ProductType(product_type_str)
        except ValueError:
            product_type = ProductType.OTHER
        
        # Generate unique ID
        product_id = self._generate_product_id(product_name, product_type)
        
        # Extract applicable entities
        applicable_entities = product_data.get("applicable_entities", [])
        
        # Extract regulatory classification and compliance requirements
        regulatory_classification = product_data.get("regulatory_classification", [])
        compliance_requirements = product_data.get("compliance_requirements", [])
        
        # Add document context to classification
        if document.legislative_initiative:
            regulatory_classification.append(f"Subject to {document.legislative_initiative}")
        
        return RegulatedProduct(
            product_id=product_id,
            name=product_name,
            product_type=product_type,
            description=product_data.get("description", ""),
            applicable_entities=applicable_entities,
            regulatory_classification=list(set(regulatory_classification)),
            compliance_requirements=list(set(compliance_requirements)),
            source_documents=[document.document_id],
            definition_text=product_data.get("definition_context", ""),
            confidence_score=product_data.get("confidence_score", 0.5)
        )
    
    def _generate_product_id(self, name: str, product_type: ProductType) -> str:
        """Generate a unique product ID."""
        # Create a unique identifier based on name and type
        identifier = f"{product_type.value}_{name.lower().replace(' ', '_')}"
        
        # Hash to ensure consistent IDs for the same product
        hash_object = hashlib.md5(identifier.encode())
        hash_hex = hash_object.hexdigest()[:8]
        
        return f"product_{hash_hex}"
    
    async def extract_products_batch(self, documents: List[RegGenomeDocument]) -> List[RegulatedProduct]:
        """Extract products from multiple documents."""
        logger.info(f"Extracting products from {len(documents)} documents")
        
        all_products = []
        for document in documents:
            products = await self.extract_products(document)
            all_products.extend(products)
        
        return all_products


class ProductMerger:
    """Utility class for merging similar products."""
    
    def __init__(self):
        pass
    
    def merge_similar_products(self, products: List[RegulatedProduct]) -> List[RegulatedProduct]:
        """Merge products that refer to the same regulatory concept."""
        # Group products by type and similar names
        product_groups = self._group_similar_products(products)
        
        merged_products = []
        for group in product_groups:
            if len(group) == 1:
                merged_products.append(group[0])
            else:
                merged_product = self._merge_product_group(group)
                merged_products.append(merged_product)
        
        return merged_products
    
    def _group_similar_products(self, products: List[RegulatedProduct]) -> List[List[RegulatedProduct]]:
        """Group products that are likely referring to the same concept."""
        groups = []
        remaining_products = products.copy()
        
        while remaining_products:
            current_product = remaining_products.pop(0)
            current_group = [current_product]
            
            # Find similar products
            to_remove = []
            for other_product in remaining_products:
                if self._are_products_similar(current_product, other_product):
                    current_group.append(other_product)
                    to_remove.append(other_product)
            
            # Remove similar products from remaining list
            for product in to_remove:
                remaining_products.remove(product)
            
            groups.append(current_group)
        
        return groups
    
    def _are_products_similar(self, product1: RegulatedProduct, product2: RegulatedProduct) -> bool:
        """Check if two products are similar enough to merge."""
        # Same type and similar names
        if product1.product_type != product2.product_type:
            return False
        
        # Simple name similarity check
        name1 = product1.name.lower().strip()
        name2 = product2.name.lower().strip()
        
        # Exact match
        if name1 == name2:
            return True
        
        # Contains check (for variations)
        if name1 in name2 or name2 in name1:
            return True
        
        # Word overlap check
        words1 = set(name1.split())
        words2 = set(name2.split())
        overlap = len(words1.intersection(words2))
        total_words = len(words1.union(words2))
        
        # If significant word overlap, consider similar
        if total_words > 0 and overlap / total_words > 0.7:
            return True
        
        return False
    
    def _merge_product_group(self, products: List[RegulatedProduct]) -> RegulatedProduct:
        """Merge a group of similar products into one."""
        # Use the product with the highest confidence as the base
        base_product = max(products, key=lambda p: p.confidence_score)
        
        # Merge information from all products
        all_source_docs = []
        all_entities = []
        all_classifications = []
        all_requirements = []
        definition_texts = []
        
        for product in products:
            all_source_docs.extend(product.source_documents)
            all_entities.extend(product.applicable_entities)
            all_classifications.extend(product.regulatory_classification)
            all_requirements.extend(product.compliance_requirements)
            if product.definition_text:
                definition_texts.append(product.definition_text)
        
        # Create merged product
        merged_product = RegulatedProduct(
            product_id=base_product.product_id,
            name=base_product.name,
            product_type=base_product.product_type,
            description=base_product.description,
            applicable_entities=list(set(all_entities)),
            regulatory_classification=list(set(all_classifications)),
            compliance_requirements=list(set(all_requirements)),
            source_documents=list(set(all_source_docs)),
            definition_text=" | ".join(definition_texts),
            confidence_score=max(p.confidence_score for p in products)
        )
        
        return merged_product 