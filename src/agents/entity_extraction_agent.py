"""Entity extraction agent for identifying regulated entities in regulatory documents."""

import logging
import hashlib
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from ..models import RegGenomeDocument, RegulatedEntity, EntityType
from ..llm_utils import extract_structured_data, llm_manager

logger = logging.getLogger(__name__)


class EntityExtractionResult(BaseModel):
    """Result model for entity extraction."""
    
    entities: List[Dict[str, Any]] = Field(description="List of extracted entities")
    confidence_score: float = Field(description="Overall confidence in extraction", ge=0.0, le=1.0)
    reasoning: str = Field(description="Explanation of extraction process")


class EntityExtractionAgent:
    """Agent for extracting regulated entities from regulatory documents."""
    
    def __init__(self):
        self.extraction_prompt = self._build_extraction_prompt()
    
    def _build_extraction_prompt(self) -> str:
        """Build the entity extraction prompt."""
        entity_types = [e.value for e in EntityType]
        
        return f"""
You are an expert in regulatory document analysis specializing in identifying regulated entities.

Your task is to extract all regulated entities mentioned in the document. These include:

**Entity Types to Look For:**
{', '.join(entity_types)}

**What to Extract:**
1. **Entity Name**: The exact name or term as it appears in the document
2. **Entity Type**: Classify using the provided entity types
3. **Description**: A clear description of what this entity is
4. **Definition Context**: The surrounding text that defines or describes the entity
5. **Regulatory Framework**: Any regulatory frameworks or rules that apply to this entity
6. **Jurisdictions**: Geographic or regulatory jurisdictions where this applies

**Instructions:**
- Focus on entities that are explicitly defined or regulated in the document
- Look for definitions, classifications, and regulatory requirements
- Pay attention to section headings, defined terms, and glossaries
- Include entities that are subject to licensing, registration, or regulatory oversight
- Capture hierarchical relationships (e.g., subcategories of investment companies)
- Be precise with terminology - use exact terms from the document
- Provide confidence scores based on how clearly the entity is defined

**Examples of Regulated Entities:**
- Investment advisers, investment companies, broker-dealers
- Mutual funds, ETFs, hedge funds, pension funds
- Banks, credit unions, insurance companies
- UCITS, collective investment schemes
- Licensed/registered financial service providers

Extract all relevant entities with their complete context and regulatory significance.
"""
    
    async def extract_entities(self, document: RegGenomeDocument) -> List[RegulatedEntity]:
        """Extract regulated entities from a document."""
        logger.info(f"Extracting entities from document: {document.title}")
        
        try:
            # Prepare content for extraction
            content = self._prepare_content(document)
            
            # Extract entities using LLM
            extraction_result = await extract_structured_data(
                content=content,
                extraction_prompt=self.extraction_prompt,
                response_model=EntityExtractionResult,
                model=llm_manager.get_extraction_model()
            )
            
            # Convert to RegulatedEntity models
            entities = []
            for entity_data in extraction_result.entities:
                entity = self._create_regulated_entity(entity_data, document)
                entities.append(entity)
            
            logger.info(f"Extracted {len(entities)} entities from document {document.document_id}")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities from document {document.document_id}: {e}")
            return []
    
    def _prepare_content(self, document: RegGenomeDocument) -> str:
        """Prepare document content for entity extraction."""
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
    
    def _create_regulated_entity(self, entity_data: Dict[str, Any], document: RegGenomeDocument) -> RegulatedEntity:
        """Create a RegulatedEntity from extracted data."""
        # Generate entity ID based on name and type
        entity_name = entity_data.get("name", "").strip()
        entity_type_str = entity_data.get("entity_type", "other").lower()
        
        # Map entity type
        try:
            entity_type = EntityType(entity_type_str)
        except ValueError:
            entity_type = EntityType.OTHER
        
        # Generate unique ID
        entity_id = self._generate_entity_id(entity_name, entity_type)
        
        # Extract jurisdictions
        jurisdictions = []
        if document.jurisdiction:
            jurisdictions.append(document.jurisdiction)
        if entity_data.get("jurisdictions"):
            jurisdictions.extend(entity_data["jurisdictions"])
        
        # Extract regulatory framework
        regulatory_framework = []
        if document.legislative_initiative:
            regulatory_framework.append(document.legislative_initiative)
        if entity_data.get("regulatory_framework"):
            regulatory_framework.extend(entity_data["regulatory_framework"])
        
        return RegulatedEntity(
            entity_id=entity_id,
            name=entity_name,
            entity_type=entity_type,
            description=entity_data.get("description", ""),
            applicable_jurisdictions=list(set(jurisdictions)),
            regulatory_framework=list(set(regulatory_framework)),
            source_documents=[document.document_id],
            definition_text=entity_data.get("definition_context", ""),
            confidence_score=entity_data.get("confidence_score", 0.5)
        )
    
    def _generate_entity_id(self, name: str, entity_type: EntityType) -> str:
        """Generate a unique entity ID."""
        # Create a unique identifier based on name and type
        identifier = f"{entity_type.value}_{name.lower().replace(' ', '_')}"
        
        # Hash to ensure consistent IDs for the same entity
        hash_object = hashlib.md5(identifier.encode())
        hash_hex = hash_object.hexdigest()[:8]
        
        return f"entity_{hash_hex}"
    
    async def extract_entities_batch(self, documents: List[RegGenomeDocument]) -> List[RegulatedEntity]:
        """Extract entities from multiple documents."""
        logger.info(f"Extracting entities from {len(documents)} documents")
        
        all_entities = []
        for document in documents:
            entities = await self.extract_entities(document)
            all_entities.extend(entities)
        
        return all_entities


class EntityMerger:
    """Utility class for merging similar entities."""
    
    def __init__(self):
        pass
    
    def merge_similar_entities(self, entities: List[RegulatedEntity]) -> List[RegulatedEntity]:
        """Merge entities that refer to the same regulatory concept."""
        # Group entities by type and similar names
        entity_groups = self._group_similar_entities(entities)
        
        merged_entities = []
        for group in entity_groups:
            if len(group) == 1:
                merged_entities.append(group[0])
            else:
                merged_entity = self._merge_entity_group(group)
                merged_entities.append(merged_entity)
        
        return merged_entities
    
    def _group_similar_entities(self, entities: List[RegulatedEntity]) -> List[List[RegulatedEntity]]:
        """Group entities that are likely referring to the same concept."""
        groups = []
        remaining_entities = entities.copy()
        
        while remaining_entities:
            current_entity = remaining_entities.pop(0)
            current_group = [current_entity]
            
            # Find similar entities
            to_remove = []
            for other_entity in remaining_entities:
                if self._are_entities_similar(current_entity, other_entity):
                    current_group.append(other_entity)
                    to_remove.append(other_entity)
            
            # Remove similar entities from remaining list
            for entity in to_remove:
                remaining_entities.remove(entity)
            
            groups.append(current_group)
        
        return groups
    
    def _are_entities_similar(self, entity1: RegulatedEntity, entity2: RegulatedEntity) -> bool:
        """Check if two entities are similar enough to merge."""
        # Same type and similar names
        if entity1.entity_type != entity2.entity_type:
            return False
        
        # Simple name similarity check
        name1 = entity1.name.lower().strip()
        name2 = entity2.name.lower().strip()
        
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
    
    def _merge_entity_group(self, entities: List[RegulatedEntity]) -> RegulatedEntity:
        """Merge a group of similar entities into one."""
        # Use the entity with the highest confidence as the base
        base_entity = max(entities, key=lambda e: e.confidence_score)
        
        # Merge information from all entities
        all_source_docs = []
        all_jurisdictions = []
        all_frameworks = []
        definition_texts = []
        
        for entity in entities:
            all_source_docs.extend(entity.source_documents)
            all_jurisdictions.extend(entity.applicable_jurisdictions)
            all_frameworks.extend(entity.regulatory_framework)
            if entity.definition_text:
                definition_texts.append(entity.definition_text)
        
        # Create merged entity
        merged_entity = RegulatedEntity(
            entity_id=base_entity.entity_id,
            name=base_entity.name,
            entity_type=base_entity.entity_type,
            description=base_entity.description,
            applicable_jurisdictions=list(set(all_jurisdictions)),
            regulatory_framework=list(set(all_frameworks)),
            source_documents=list(set(all_source_docs)),
            definition_text=" | ".join(definition_texts),
            confidence_score=max(e.confidence_score for e in entities)
        )
        
        return merged_entity 