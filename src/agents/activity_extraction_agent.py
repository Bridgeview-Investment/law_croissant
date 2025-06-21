from typing import List, Dict, Any, Optional
import re
from src.models import Document, RegulatedActivity, ActivityType

class ActivityExtractionAgent:
    """Agent specialized in extracting regulated activities from documents"""
    
    def __init__(self):
        # Activity patterns and keywords
        self.activity_patterns = {
            ActivityType.ASSET_MANAGEMENT: [
                r"asset management",
                r"portfolio management",
                r"managing (?:client|investor) assets",
                r"discretionary (?:asset|portfolio) management",
                r"collective investment management"
            ],
            ActivityType.INVESTMENT_ADVICE: [
                r"investment advice",
                r"investment advisory",
                r"providing (?:investment )?advice",
                r"advising (?:on|regarding) investments",
                r"investment recommendations"
            ],
            ActivityType.PORTFOLIO_MANAGEMENT: [
                r"portfolio management",
                r"managing portfolios",
                r"discretionary management",
                r"portfolio construction",
                r"portfolio optimization"
            ],
            ActivityType.CUSTODY: [
                r"custody (?:services|of assets)",
                r"safekeeping (?:services|of assets)",
                r"custodial services",
                r"asset custody",
                r"holding client assets"
            ],
            ActivityType.DISTRIBUTION: [
                r"distribution (?:of funds|services)",
                r"marketing (?:of funds|services)",
                r"fund distribution",
                r"selling (?:fund )?shares",
                r"placement of units"
            ],
            ActivityType.FUND_ADMINISTRATION: [
                r"fund administration",
                r"administrative services",
                r"transfer agency",
                r"registrar services",
                r"fund accounting"
            ],
            ActivityType.RISK_MANAGEMENT: [
                r"risk management",
                r"risk (?:assessment|monitoring)",
                r"risk control",
                r"managing (?:investment )?risks",
                r"risk mitigation"
            ],
            ActivityType.COMPLIANCE: [
                r"compliance (?:monitoring|services)",
                r"regulatory compliance",
                r"compliance oversight",
                r"ensuring compliance",
                r"compliance procedures"
            ],
            ActivityType.REPORTING: [
                r"regulatory reporting",
                r"reporting (?:requirements|obligations)",
                r"filing reports",
                r"disclosure requirements",
                r"transparency reporting"
            ]
        }
        
        self.activity_verbs = [
            "managing", "advising", "providing", "offering", "conducting",
            "performing", "executing", "administering", "distributing",
            "marketing", "selling", "holding", "safekeeping", "monitoring"
        ]
    
    def extract_activities(self, document: Document) -> List[RegulatedActivity]:
        """Extract regulated activities from a document"""
        activities = []
        processed_activities = set()
        
        full_text = self._get_full_text(document)
        
        for activity_type, patterns in self.activity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                
                for match in matches:
                    activity_name = match.group(0)
                    context = self._extract_context(full_text, match.start(), match.end())
                    
                    # Create unique key
                    activity_key = f"{activity_name.lower()}_{activity_type.value}"
                    
                    if activity_key not in processed_activities:
                        processed_activities.add(activity_key)
                        
                        activity = RegulatedActivity(
                            name=self._normalize_activity_name(activity_name),
                            type="activity",
                            activity_type=activity_type,
                            description=self._generate_description(activity_name, context),
                            source_document_id=document.document_id,
                            source_text=context,
                            confidence=self._calculate_confidence(activity_name, context),
                            metadata={
                                "document_title": document.title or "Unknown",
                                "publishers": [p.get("name", "") for p in document.publishers] if document.publishers else [],
                                "published_date": document.published or "Unknown"
                            },
                            applicable_entities=self._extract_applicable_entities(context),
                            requirements=self._extract_requirements(context)
                        )
                        activities.append(activity)
        
        # Also look for activities defined in signposts
        activities.extend(self._extract_from_signposts(document))
        
        return activities
    
    def _get_full_text(self, document: Document) -> str:
        """Combine all text sources from document"""
        text_parts = []
        
        if document.title:
            text_parts.append(document.title)
        
        if document.source_text:
            for text_item in document.source_text:
                if isinstance(text_item, dict) and "text" in text_item:
                    text_parts.append(text_item["text"])
                elif isinstance(text_item, str):
                    text_parts.append(text_item)
        
        if document.signposts:
            for signpost in document.signposts:
                if isinstance(signpost, dict) and "text" in signpost:
                    text_parts.append(signpost["text"])
        
        return " ".join(text_parts)
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 300) -> str:
        """Extract context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _normalize_activity_name(self, activity_name: str) -> str:
        """Normalize activity name for consistency"""
        # Remove extra spaces and capitalize properly
        normalized = " ".join(activity_name.split())
        return normalized.title()
    
    def _generate_description(self, activity_name: str, context: str) -> str:
        """Generate description based on activity and context"""
        activity_lower = activity_name.lower()
        
        descriptions = {
            "asset management": "Professional management of client assets and investments",
            "investment advice": "Providing recommendations and guidance on investment decisions",
            "portfolio management": "Managing investment portfolios on behalf of clients",
            "custody": "Safekeeping and administration of financial assets",
            "distribution": "Marketing and selling of investment products",
            "fund administration": "Administrative and operational services for investment funds",
            "risk management": "Identifying, assessing and mitigating investment risks",
            "compliance": "Ensuring adherence to regulatory requirements",
            "reporting": "Preparing and submitting regulatory reports and disclosures"
        }
        
        for key, desc in descriptions.items():
            if key in activity_lower:
                return desc
        
        return f"Regulated activity involving {activity_name}"
    
    def _calculate_confidence(self, activity_name: str, context: str) -> float:
        """Calculate confidence score for extracted activity"""
        score = 0.6  # Base score
        
        # Check for activity verbs
        for verb in self.activity_verbs:
            if verb in context.lower():
                score += 0.1
                break
        
        # Check for regulatory context
        regulatory_indicators = ["must", "shall", "required", "obligation", "duty", "prohibited"]
        for indicator in regulatory_indicators:
            if indicator in context.lower():
                score += 0.15
                break
        
        # Check for formal definition
        if any(phrase in context.lower() for phrase in ["means", "defined as", "includes"]):
            score += 0.15
        
        return min(score, 1.0)
    
    def _extract_applicable_entities(self, context: str) -> List[str]:
        """Extract entities to which the activity applies"""
        entities = []
        
        entity_patterns = [
            r"investment adviser[s]?",
            r"investment compan(?:y|ies)",
            r"management compan(?:y|ies)",
            r"UCITS",
            r"fund[s]?",
            r"depositar(?:y|ies)",
            r"firm[s]?"
        ]
        
        for pattern in entity_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                entities.append(pattern.replace(r"[s]?", "").replace(r"(?:y|ies)", "y"))
        
        return entities
    
    def _extract_requirements(self, context: str) -> List[str]:
        """Extract specific requirements for the activity"""
        requirements = []
        
        # Look for requirement patterns
        req_patterns = [
            r"must [\w\s]+",
            r"shall [\w\s]+",
            r"required to [\w\s]+",
            r"obligation to [\w\s]+"
        ]
        
        for pattern in req_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                req_text = match.group(0).strip()
                if len(req_text) < 100:  # Avoid very long matches
                    requirements.append(req_text)
        
        return requirements[:5]  # Limit to top 5 requirements
    
    def _extract_from_signposts(self, document: Document) -> List[RegulatedActivity]:
        """Extract activities from document signposts"""
        activities = []
        
        if not document.signposts:
            return activities
            
        for signpost in document.signposts:
            if isinstance(signpost, dict):
                tags = signpost.get("tags", [])
                text = signpost.get("text", "")
                
                # Map signpost tags to activity types
                tag_to_activity = {
                    "asset-management": ActivityType.ASSET_MANAGEMENT,
                    "investment-advice": ActivityType.INVESTMENT_ADVICE,
                    "portfolio-management": ActivityType.PORTFOLIO_MANAGEMENT,
                    "custody": ActivityType.CUSTODY,
                    "distribution": ActivityType.DISTRIBUTION,
                    "risk-management": ActivityType.RISK_MANAGEMENT,
                    "compliance": ActivityType.COMPLIANCE,
                    "reporting": ActivityType.REPORTING
                }
                
                for tag in tags:
                    tag_lower = tag.lower()
                    for tag_key, activity_type in tag_to_activity.items():
                        if tag_key in tag_lower:
                            activity = RegulatedActivity(
                                name=tag.replace("-", " ").title(),
                                type="activity",
                                activity_type=activity_type,
                                description=f"Activity identified from regulatory signpost: {tag}",
                                source_document_id=document.document_id,
                                source_text=text[:500] if text else tag,
                                confidence=0.8,  # High confidence for signpost-based extraction
                                metadata={
                                    "document_title": document.title or "Unknown",
                                    "signpost_tag": tag,
                                    "extraction_method": "signpost"
                                }
                            )
                            activities.append(activity)
                            break
        
        return activities