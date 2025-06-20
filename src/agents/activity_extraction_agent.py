"""Activity extraction agent for identifying regulated activities in regulatory documents."""

import logging
import hashlib
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from ..models import RegGenomeDocument, RegulatedActivity, ActivityType
from ..llm_utils import extract_structured_data, llm_manager

logger = logging.getLogger(__name__)


class ActivityExtractionResult(BaseModel):
    """Result model for activity extraction."""
    
    activities: List[Dict[str, Any]] = Field(description="List of extracted activities")
    confidence_score: float = Field(description="Overall confidence in extraction", ge=0.0, le=1.0)
    reasoning: str = Field(description="Explanation of extraction process")


class ActivityExtractionAgent:
    """Agent for extracting regulated activities from regulatory documents."""
    
    def __init__(self):
        self.extraction_prompt = self._build_extraction_prompt()
    
    def _build_extraction_prompt(self) -> str:
        """Build the activity extraction prompt."""
        activity_types = [a.value for a in ActivityType]
        
        return f"""
You are an expert in regulatory document analysis specializing in identifying regulated activities.

Your task is to extract all regulated activities mentioned in the document. These include:

**Activity Types to Look For:**
{', '.join(activity_types)}

**What to Extract:**
1. **Activity Name**: The exact name or term as it appears in the document
2. **Activity Type**: Classify using the provided activity types
3. **Description**: A clear description of what this activity involves
4. **Definition Context**: The surrounding text that defines or describes the activity
5. **Regulatory Requirements**: Any specific regulatory requirements, licenses, or permissions needed
6. **Applicable Entities**: Types of entities that can perform this activity
7. **Jurisdictions**: Geographic or regulatory jurisdictions where this applies

**Instructions:**
- Focus on activities that are explicitly regulated, licensed, or supervised
- Look for definitions of business activities, services, or operations
- Pay attention to licensing requirements, registration obligations, and regulatory oversight
- Include activities that require regulatory approval or notification
- Capture compliance requirements and restrictions
- Be precise with terminology - use exact terms from the document
- Provide confidence scores based on how clearly the activity is defined

**Examples of Regulated Activities:**
- Investment advisory services, portfolio management
- Securities trading, market making, underwriting
- Fund management, custody services
- Research services, prime brokerage
- Risk management, compliance monitoring
- Financial advice, wealth management
- Clearing and settlement services

Extract all relevant activities with their complete regulatory context and requirements.
"""
    
    async def extract_activities(self, document: RegGenomeDocument) -> List[RegulatedActivity]:
        """Extract regulated activities from a document."""
        logger.info(f"Extracting activities from document: {document.title}")
        
        try:
            # Prepare content for extraction
            content = self._prepare_content(document)
            
            # Extract activities using LLM
            extraction_result = await extract_structured_data(
                content=content,
                extraction_prompt=self.extraction_prompt,
                response_model=ActivityExtractionResult,
                model=llm_manager.get_extraction_model()
            )
            
            # Convert to RegulatedActivity models
            activities = []
            for activity_data in extraction_result.activities:
                activity = self._create_regulated_activity(activity_data, document)
                activities.append(activity)
            
            logger.info(f"Extracted {len(activities)} activities from document {document.document_id}")
            return activities
            
        except Exception as e:
            logger.error(f"Error extracting activities from document {document.document_id}: {e}")
            return []
    
    def _prepare_content(self, document: RegGenomeDocument) -> str:
        """Prepare document content for activity extraction."""
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
    
    def _create_regulated_activity(self, activity_data: Dict[str, Any], document: RegGenomeDocument) -> RegulatedActivity:
        """Create a RegulatedActivity from extracted data."""
        # Generate activity ID based on name and type
        activity_name = activity_data.get("name", "").strip()
        activity_type_str = activity_data.get("activity_type", "other").lower()
        
        # Map activity type
        try:
            activity_type = ActivityType(activity_type_str)
        except ValueError:
            activity_type = ActivityType.OTHER
        
        # Generate unique ID
        activity_id = self._generate_activity_id(activity_name, activity_type)
        
        # Extract applicable entities
        applicable_entities = activity_data.get("applicable_entities", [])
        
        # Extract regulatory requirements
        regulatory_requirements = activity_data.get("regulatory_requirements", [])
        required_licenses = activity_data.get("required_licenses", [])
        
        # Add document context to requirements
        if document.legislative_initiative:
            regulatory_requirements.append(f"Subject to {document.legislative_initiative}")
        
        return RegulatedActivity(
            activity_id=activity_id,
            name=activity_name,
            activity_type=activity_type,
            description=activity_data.get("description", ""),
            applicable_entities=applicable_entities,
            required_licenses=required_licenses,
            regulatory_requirements=list(set(regulatory_requirements)),
            source_documents=[document.document_id],
            definition_text=activity_data.get("definition_context", ""),
            confidence_score=activity_data.get("confidence_score", 0.5)
        )
    
    def _generate_activity_id(self, name: str, activity_type: ActivityType) -> str:
        """Generate a unique activity ID."""
        # Create a unique identifier based on name and type
        identifier = f"{activity_type.value}_{name.lower().replace(' ', '_')}"
        
        # Hash to ensure consistent IDs for the same activity
        hash_object = hashlib.md5(identifier.encode())
        hash_hex = hash_object.hexdigest()[:8]
        
        return f"activity_{hash_hex}"
    
    async def extract_activities_batch(self, documents: List[RegGenomeDocument]) -> List[RegulatedActivity]:
        """Extract activities from multiple documents."""
        logger.info(f"Extracting activities from {len(documents)} documents")
        
        all_activities = []
        for document in documents:
            activities = await self.extract_activities(document)
            all_activities.extend(activities)
        
        return all_activities


class ActivityMerger:
    """Utility class for merging similar activities."""
    
    def __init__(self):
        pass
    
    def merge_similar_activities(self, activities: List[RegulatedActivity]) -> List[RegulatedActivity]:
        """Merge activities that refer to the same regulatory concept."""
        # Group activities by type and similar names
        activity_groups = self._group_similar_activities(activities)
        
        merged_activities = []
        for group in activity_groups:
            if len(group) == 1:
                merged_activities.append(group[0])
            else:
                merged_activity = self._merge_activity_group(group)
                merged_activities.append(merged_activity)
        
        return merged_activities
    
    def _group_similar_activities(self, activities: List[RegulatedActivity]) -> List[List[RegulatedActivity]]:
        """Group activities that are likely referring to the same concept."""
        groups = []
        remaining_activities = activities.copy()
        
        while remaining_activities:
            current_activity = remaining_activities.pop(0)
            current_group = [current_activity]
            
            # Find similar activities
            to_remove = []
            for other_activity in remaining_activities:
                if self._are_activities_similar(current_activity, other_activity):
                    current_group.append(other_activity)
                    to_remove.append(other_activity)
            
            # Remove similar activities from remaining list
            for activity in to_remove:
                remaining_activities.remove(activity)
            
            groups.append(current_group)
        
        return groups
    
    def _are_activities_similar(self, activity1: RegulatedActivity, activity2: RegulatedActivity) -> bool:
        """Check if two activities are similar enough to merge."""
        # Same type and similar names
        if activity1.activity_type != activity2.activity_type:
            return False
        
        # Simple name similarity check
        name1 = activity1.name.lower().strip()
        name2 = activity2.name.lower().strip()
        
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
    
    def _merge_activity_group(self, activities: List[RegulatedActivity]) -> RegulatedActivity:
        """Merge a group of similar activities into one."""
        # Use the activity with the highest confidence as the base
        base_activity = max(activities, key=lambda a: a.confidence_score)
        
        # Merge information from all activities
        all_source_docs = []
        all_entities = []
        all_licenses = []
        all_requirements = []
        definition_texts = []
        
        for activity in activities:
            all_source_docs.extend(activity.source_documents)
            all_entities.extend(activity.applicable_entities)
            all_licenses.extend(activity.required_licenses)
            all_requirements.extend(activity.regulatory_requirements)
            if activity.definition_text:
                definition_texts.append(activity.definition_text)
        
        # Create merged activity
        merged_activity = RegulatedActivity(
            activity_id=base_activity.activity_id,
            name=base_activity.name,
            activity_type=base_activity.activity_type,
            description=base_activity.description,
            applicable_entities=list(set(all_entities)),
            required_licenses=list(set(all_licenses)),
            regulatory_requirements=list(set(all_requirements)),
            source_documents=list(set(all_source_docs)),
            definition_text=" | ".join(definition_texts),
            confidence_score=max(a.confidence_score for a in activities)
        )
        
        return merged_activity 