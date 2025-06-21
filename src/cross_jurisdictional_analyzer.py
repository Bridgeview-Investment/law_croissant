"""
Cross-Jurisdictional Regulatory Analysis System

This system addresses real-world business scenarios where firms need to comply
with multiple jurisdictions simultaneously. For example:
- A client wants to open US stocks, Hong Kong stocks, and A-share accounts
- A firm needs unified customer data collection that satisfies all jurisdictions
- Cross-border compliance requirements analysis

Key Features:
- Separate analysis for US, EU, UK regulations
- Cross-matching and merging of requirements
- Difference analysis and conflict identification
- Unified customer data mapping recommendations
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json
import logging
from datetime import datetime
from pathlib import Path

from src.config import Config
from src.api_client import RegGenomeAPIClient
from src.models import Document, RegulatedEntity, RegulatedActivity, RegulatedProduct
from src.deep_research_orchestrator import DeepResearchOrchestrator

@dataclass
class JurisdictionResult:
    """Results for a specific jurisdiction"""
    jurisdiction: str
    entities: List[RegulatedEntity]
    activities: List[RegulatedActivity] 
    products: List[RegulatedProduct]
    documents_processed: int
    specific_requirements: List[Dict[str, Any]]
    definitions: Dict[str, str]

@dataclass
class CrossJurisdictionalRequirement:
    """A requirement that spans multiple jurisdictions"""
    requirement_type: str  # e.g., "KYC", "AML", "Suitability Assessment"
    description: str
    jurisdictions: Dict[str, Dict[str, Any]]  # jurisdiction -> specific details
    differences: List[str]
    commonalities: List[str]
    unified_approach: Optional[str]

class JurisdictionSpecificAnalyzer:
    """Analyzer for a specific jurisdiction"""
    
    def __init__(self, jurisdiction: str, config: Config):
        self.jurisdiction = jurisdiction
        self.config = config
        self.orchestrator = DeepResearchOrchestrator(config)
        
        # Jurisdiction-specific initiative filters
        self.initiative_mapping = {
            "US": ["US - Investment Advisers Act (1940)", "US - Investment Company Act (1940)"],
            "EU": ["EU - UCITS Directives"],
            "UK": ["UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations, 2011 - 2016"]
        }
    
    async def analyze_jurisdiction(self, query: str) -> JurisdictionResult:
        """Analyze regulations for this specific jurisdiction"""
        
        print(f"🔍 Analyzing {self.jurisdiction} regulations for: {query}")
        
        # Modify query to be jurisdiction-specific
        jurisdiction_query = f"{query} - {self.jurisdiction} regulations and requirements"
        
        # Get jurisdiction-specific documents
        documents = await self._fetch_jurisdiction_documents()
        
        # Run analysis with jurisdiction focus
        result = await self.orchestrator.research(jurisdiction_query)
        
        # Extract jurisdiction-specific requirements
        specific_requirements = await self._extract_specific_requirements(documents, query)
        
        # Extract definitions
        definitions = await self._extract_definitions(documents, result)
        
        return JurisdictionResult(
            jurisdiction=self.jurisdiction,
            entities=result.entities,
            activities=result.activities,
            products=result.products,
            documents_processed=len(documents),
            specific_requirements=specific_requirements,
            definitions=definitions
        )
    
    async def _fetch_jurisdiction_documents(self) -> List[Document]:
        """Fetch documents specific to this jurisdiction"""
        initiatives = self.initiative_mapping.get(self.jurisdiction, [])
        
        async with RegGenomeAPIClient(self.config) as client:
            # Fetch documents for the jurisdiction's initiatives
            documents = await client.fetch_all_documents_for_initiatives(initiatives)
            
            return documents
    
    async def _extract_specific_requirements(self, documents: List[Document], query: str) -> List[Dict[str, Any]]:
        """Extract jurisdiction-specific requirements"""
        requirements = []
        
        # Focus on key regulatory areas
        key_areas = [
            "customer due diligence", "KYC", "know your customer",
            "anti-money laundering", "AML", 
            "suitability assessment", "appropriateness",
            "account opening", "onboarding",
            "record keeping", "documentation",
            "reporting requirements", "disclosure"
        ]
        
        for doc in documents[:20]:  # Limit for efficiency
            doc_text = self._get_document_text(doc)
            
            for area in key_areas:
                if area.lower() in doc_text.lower():
                    # Extract requirements for this area
                    requirement = await self._extract_requirement_details(doc, area, doc_text)
                    if requirement:
                        requirements.append(requirement)
        
        return requirements
    
    async def _extract_requirement_details(self, doc: Document, area: str, doc_text: str) -> Optional[Dict[str, Any]]:
        """Extract detailed requirements for a specific area"""
        
        # Find relevant sections
        relevant_sections = []
        lines = doc_text.split('\n')
        
        for i, line in enumerate(lines):
            if area.lower() in line.lower():
                # Extract surrounding context
                start = max(0, i - 2)
                end = min(len(lines), i + 5)
                context = '\n'.join(lines[start:end])
                relevant_sections.append(context)
        
        if not relevant_sections:
            return None
        
        return {
            "area": area,
            "jurisdiction": self.jurisdiction,
            "document_id": doc.document_id,
            "document_title": doc.title,
            "requirements": relevant_sections[:3],  # Top 3 most relevant
            "source_url": self._get_document_url(doc)
        }
    
    async def _extract_definitions(self, documents: List[Document], result) -> Dict[str, str]:
        """Extract key definitions for this jurisdiction"""
        definitions = {}
        
        # Key terms to find definitions for
        key_terms = []
        
        # Add entity names
        for entity in result.entities[:10]:
            key_terms.append(entity.name)
        
        # Add activity names  
        for activity in result.activities[:10]:
            key_terms.append(activity.name)
        
        # Add product names
        for product in result.products[:10]:
            key_terms.append(product.name)
        
        # Search for definitions
        for doc in documents[:10]:
            doc_text = self._get_document_text(doc)
            
            for term in key_terms:
                definition = self._find_definition(doc_text, term)
                if definition and term not in definitions:
                    definitions[term] = definition
        
        return definitions
    
    def _find_definition(self, text: str, term: str) -> Optional[str]:
        """Find definition of a term in text"""
        import re
        
        patterns = [
            rf'"{re.escape(term)}"\s+means\s+([^.]+\.)',
            rf'{re.escape(term)}\s+is\s+defined\s+as\s+([^.]+\.)',
            rf'{re.escape(term)}\s+refers\s+to\s+([^.]+\.)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _get_document_text(self, doc: Document) -> str:
        """Extract text from document"""
        text_parts = []
        
        if doc.title:
            text_parts.append(doc.title)
        
        if doc.source_text:
            for item in doc.source_text[:10]:  # Limit for efficiency
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
        
        return "\n".join(text_parts)
    
    def _get_document_url(self, doc: Document) -> Optional[str]:
        """Get document URL if available"""
        if doc.metadata and "source_urls" in doc.metadata:
            urls = doc.metadata["source_urls"]
            if urls and isinstance(urls, list) and len(urls) > 0:
                return urls[0]
        return None

class CrossJurisdictionalAnalyzer:
    """Main analyzer for cross-jurisdictional requirements"""
    
    def __init__(self, config: Config):
        self.config = config
        self.jurisdictions = ["US", "EU", "UK"]
        self.analyzers = {
            jurisdiction: JurisdictionSpecificAnalyzer(jurisdiction, config)
            for jurisdiction in self.jurisdictions
        }
    
    async def analyze_cross_jurisdictional_requirements(self, query: str) -> Dict[str, Any]:
        """Perform comprehensive cross-jurisdictional analysis"""
        
        print(f"\n{'='*80}")
        print("🌍 CROSS-JURISDICTIONAL REGULATORY ANALYSIS")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Jurisdictions: {', '.join(self.jurisdictions)}")
        print(f"{'='*80}\n")
        
        # Step 1: Analyze each jurisdiction separately
        print("📊 Step 1: Analyzing each jurisdiction separately...")
        jurisdiction_results = {}
        
        for jurisdiction in self.jurisdictions:
            result = await self.analyzers[jurisdiction].analyze_jurisdiction(query)
            jurisdiction_results[jurisdiction] = result
            
            print(f"✅ {jurisdiction}: {result.documents_processed} docs, "
                  f"{len(result.entities)} entities, {len(result.activities)} activities, "
                  f"{len(result.products)} products")
        
        # Step 2: Cross-match and merge requirements
        print(f"\n🔗 Step 2: Cross-matching requirements across jurisdictions...")
        cross_matched_requirements = await self._cross_match_requirements(jurisdiction_results)
        
        # Step 3: Identify differences and commonalities
        print(f"\n⚖️ Step 3: Analyzing differences and commonalities...")
        comparison_analysis = await self._analyze_differences(jurisdiction_results, cross_matched_requirements)
        
        # Step 4: Generate unified customer data recommendations
        print(f"\n📋 Step 4: Generating unified customer data recommendations...")
        unified_recommendations = await self._generate_unified_recommendations(cross_matched_requirements)
        
        # Compile comprehensive results
        comprehensive_results = {
            "query": query,
            "execution_timestamp": datetime.now().isoformat(),
            "analysis_type": "cross_jurisdictional",
            "jurisdictions_analyzed": self.jurisdictions,
            "jurisdiction_results": self._serialize_jurisdiction_results(jurisdiction_results),
            "cross_matched_requirements": cross_matched_requirements,
            "comparison_analysis": comparison_analysis,
            "unified_recommendations": unified_recommendations,
            "summary": self._generate_summary(jurisdiction_results, cross_matched_requirements)
        }
        
        print(f"\n✅ Cross-jurisdictional analysis complete!")
        return comprehensive_results
    
    async def _cross_match_requirements(self, jurisdiction_results: Dict[str, JurisdictionResult]) -> List[CrossJurisdictionalRequirement]:
        """Cross-match requirements across jurisdictions"""
        
        # Group requirements by type
        requirement_groups = defaultdict(lambda: defaultdict(list))
        
        for jurisdiction, result in jurisdiction_results.items():
            for req in result.specific_requirements:
                area = req["area"]
                requirement_groups[area][jurisdiction].append(req)
        
        cross_matched = []
        
        for area, jurisdiction_reqs in requirement_groups.items():
            if len(jurisdiction_reqs) > 1:  # Only if multiple jurisdictions have this requirement
                
                # Analyze differences and commonalities
                differences = []
                commonalities = []
                unified_approach = None
                
                # Compare requirements across jurisdictions
                all_requirements = {}
                for jurisdiction, reqs in jurisdiction_reqs.items():
                    all_requirements[jurisdiction] = {
                        "requirements": [r["requirements"] for r in reqs],
                        "documents": [r["document_title"] for r in reqs],
                        "sources": [r.get("source_url", "") for r in reqs]
                    }
                
                # Identify patterns
                differences, commonalities, unified_approach = await self._compare_jurisdiction_requirements(
                    area, all_requirements
                )
                
                cross_requirement = CrossJurisdictionalRequirement(
                    requirement_type=area,
                    description=f"Cross-jurisdictional requirements for {area}",
                    jurisdictions=all_requirements,
                    differences=differences,
                    commonalities=commonalities,
                    unified_approach=unified_approach
                )
                
                cross_matched.append(cross_requirement)
        
        return cross_matched
    
    async def _compare_jurisdiction_requirements(self, area: str, all_requirements: Dict[str, Dict[str, Any]]) -> Tuple[List[str], List[str], str]:
        """Compare requirements across jurisdictions to find differences and commonalities"""
        
        differences = []
        commonalities = []
        
        jurisdictions = list(all_requirements.keys())
        
        # Analyze differences
        if "US" in jurisdictions and "EU" in jurisdictions:
            differences.append(f"US focuses on SEC compliance while EU emphasizes MiFID II requirements")
        
        if "UK" in jurisdictions:
            differences.append(f"UK has post-Brexit specific requirements that may differ from EU")
        
        # Common patterns based on area
        if "KYC" in area.upper() or "customer due diligence" in area.lower():
            commonalities.extend([
                "Identity verification required across all jurisdictions",
                "Risk assessment mandatory",
                "Ongoing monitoring obligations"
            ])
            differences.extend([
                "US: Patriot Act compliance required",
                "EU: GDPR data protection considerations",
                "UK: Money Laundering Regulations specific requirements"
            ])
        
        elif "AML" in area.upper() or "anti-money laundering" in area.lower():
            commonalities.extend([
                "Suspicious transaction reporting required",
                "Customer risk profiling mandatory",
                "Record keeping obligations"
            ])
            differences.extend([
                "US: FinCEN reporting requirements",
                "EU: 5th Anti-Money Laundering Directive compliance",
                "UK: Proceeds of Crime Act considerations"
            ])
        
        elif "suitability" in area.lower() or "appropriateness" in area.lower():
            commonalities.extend([
                "Investment experience assessment required",
                "Risk tolerance evaluation mandatory",
                "Product matching obligations"
            ])
            differences.extend([
                "US: Reg BI suitability standards",
                "EU: MiFID II appropriateness requirements",
                "UK: FCA suitability rules"
            ])
        
        # Generate unified approach
        unified_approach = f"Implement comprehensive {area} framework that captures the most stringent requirements from all jurisdictions, ensuring compliance across US, EU, and UK markets."
        
        return differences, commonalities, unified_approach
    
    async def _analyze_differences(self, jurisdiction_results: Dict[str, JurisdictionResult], cross_matched: List[CrossJurisdictionalRequirement]) -> Dict[str, Any]:
        """Analyze key differences between jurisdictions"""
        
        analysis = {
            "entity_differences": self._analyze_entity_differences(jurisdiction_results),
            "activity_differences": self._analyze_activity_differences(jurisdiction_results),
            "product_differences": self._analyze_product_differences(jurisdiction_results),
            "requirement_conflicts": self._identify_requirement_conflicts(cross_matched),
            "compliance_complexity": self._assess_compliance_complexity(cross_matched)
        }
        
        return analysis
    
    def _analyze_entity_differences(self, jurisdiction_results: Dict[str, JurisdictionResult]) -> Dict[str, Any]:
        """Analyze differences in entity requirements"""
        entity_analysis = {}
        
        for jurisdiction, result in jurisdiction_results.items():
            entity_types = defaultdict(int)
            for entity in result.entities:
                entity_types[entity.entity_type.value] += 1
            
            entity_analysis[jurisdiction] = {
                "total_entities": len(result.entities),
                "entity_types": dict(entity_types),
                "key_entities": [e.name for e in result.entities[:5]]
            }
        
        return entity_analysis
    
    def _analyze_activity_differences(self, jurisdiction_results: Dict[str, JurisdictionResult]) -> Dict[str, Any]:
        """Analyze differences in activity requirements"""
        activity_analysis = {}
        
        for jurisdiction, result in jurisdiction_results.items():
            activity_types = defaultdict(int)
            for activity in result.activities:
                activity_types[activity.activity_type.value] += 1
            
            activity_analysis[jurisdiction] = {
                "total_activities": len(result.activities),
                "activity_types": dict(activity_types),
                "key_activities": [a.name for a in result.activities[:5]]
            }
        
        return activity_analysis
    
    def _analyze_product_differences(self, jurisdiction_results: Dict[str, JurisdictionResult]) -> Dict[str, Any]:
        """Analyze differences in product requirements"""
        product_analysis = {}
        
        for jurisdiction, result in jurisdiction_results.items():
            product_types = defaultdict(int)
            for product in result.products:
                product_types[product.product_type.value] += 1
            
            product_analysis[jurisdiction] = {
                "total_products": len(result.products),
                "product_types": dict(product_types),
                "key_products": [p.name for p in result.products[:5]]
            }
        
        return product_analysis
    
    def _identify_requirement_conflicts(self, cross_matched: List[CrossJurisdictionalRequirement]) -> List[Dict[str, Any]]:
        """Identify potential conflicts between jurisdictional requirements"""
        conflicts = []
        
        for req in cross_matched:
            if len(req.differences) > 2:  # Significant differences
                conflict = {
                    "requirement_type": req.requirement_type,
                    "conflict_description": f"Conflicting requirements across jurisdictions for {req.requirement_type}",
                    "affected_jurisdictions": list(req.jurisdictions.keys()),
                    "key_differences": req.differences[:3],
                    "resolution_approach": req.unified_approach
                }
                conflicts.append(conflict)
        
        return conflicts
    
    def _assess_compliance_complexity(self, cross_matched: List[CrossJurisdictionalRequirement]) -> Dict[str, Any]:
        """Assess overall compliance complexity"""
        total_requirements = len(cross_matched)
        conflicting_requirements = sum(1 for req in cross_matched if len(req.differences) > 1)
        
        complexity_score = (conflicting_requirements / total_requirements) if total_requirements > 0 else 0
        
        if complexity_score < 0.3:
            complexity_level = "Low"
        elif complexity_score < 0.6:
            complexity_level = "Medium"
        else:
            complexity_level = "High"
        
        return {
            "total_requirements": total_requirements,
            "conflicting_requirements": conflicting_requirements,
            "complexity_score": round(complexity_score, 2),
            "complexity_level": complexity_level,
            "recommendations": self._get_complexity_recommendations(complexity_level)
        }
    
    def _get_complexity_recommendations(self, complexity_level: str) -> List[str]:
        """Get recommendations based on complexity level"""
        if complexity_level == "Low":
            return [
                "Requirements are largely aligned across jurisdictions",
                "Standard compliance framework should suffice",
                "Minimal additional complexity for multi-jurisdictional operations"
            ]
        elif complexity_level == "Medium":
            return [
                "Some differences exist but manageable with proper planning",
                "Consider jurisdiction-specific compliance procedures",
                "Regular review of regulatory changes recommended"
            ]
        else:
            return [
                "Significant differences require careful compliance strategy",
                "Recommend dedicated compliance resources for each jurisdiction",
                "Legal consultation advised for complex requirements",
                "Consider phased implementation approach"
            ]
    
    async def _generate_unified_recommendations(self, cross_matched: List[CrossJurisdictionalRequirement]) -> Dict[str, Any]:
        """Generate recommendations for unified customer data collection"""
        
        # Extract all data fields mentioned across jurisdictions
        unified_fields = set()
        jurisdiction_specific_fields = defaultdict(set)
        
        for req in cross_matched:
            # Extract field requirements from each jurisdiction
            for jurisdiction, details in req.jurisdictions.items():
                fields = self._extract_data_fields(req.requirement_type, details)
                unified_fields.update(fields["common"])
                jurisdiction_specific_fields[jurisdiction].update(fields["specific"])
        
        # Generate unified customer onboarding form
        unified_form = self._generate_unified_form(unified_fields, jurisdiction_specific_fields)
        
        # Generate data mapping strategy
        data_mapping = self._generate_data_mapping_strategy(unified_fields, jurisdiction_specific_fields)
        
        return {
            "unified_customer_form": unified_form,
            "data_mapping_strategy": data_mapping,
            "implementation_approach": self._generate_implementation_approach(),
            "compliance_checklist": self._generate_compliance_checklist(cross_matched)
        }
    
    def _extract_data_fields(self, requirement_type: str, details: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract data fields based on requirement type"""
        
        common_fields = []
        specific_fields = []
        
        if "KYC" in requirement_type.upper() or "customer due diligence" in requirement_type.lower():
            common_fields.extend([
                "Full legal name", "Date of birth", "Address", "Phone number",
                "Email address", "Government ID number", "Occupation",
                "Source of funds", "Investment experience", "Risk tolerance"
            ])
        
        if "AML" in requirement_type.upper():
            common_fields.extend([
                "PEP status", "Sanctions screening", "Beneficial ownership",
                "Source of wealth documentation"
            ])
        
        if "suitability" in requirement_type.lower():
            common_fields.extend([
                "Investment objectives", "Time horizon", "Financial situation",
                "Investment knowledge", "Risk capacity"
            ])
        
        return {"common": common_fields, "specific": specific_fields}
    
    def _generate_unified_form(self, unified_fields: set, jurisdiction_specific_fields: Dict[str, set]) -> Dict[str, Any]:
        """Generate unified customer onboarding form"""
        
        form_sections = {
            "personal_information": [
                "Full legal name", "Date of birth", "Address", "Phone number", "Email address"
            ],
            "identification": [
                "Government ID number", "ID document type", "ID expiry date"
            ],
            "financial_information": [
                "Occupation", "Annual income", "Net worth", "Source of funds", "Source of wealth"
            ],
            "investment_profile": [
                "Investment objectives", "Time horizon", "Risk tolerance", "Investment experience"
            ],
            "compliance_screening": [
                "PEP status", "Sanctions screening", "Beneficial ownership information"
            ],
            "jurisdiction_specific": {}
        }
        
        # Add jurisdiction-specific fields
        for jurisdiction, fields in jurisdiction_specific_fields.items():
            form_sections["jurisdiction_specific"][jurisdiction] = list(fields)
        
        return {
            "form_structure": form_sections,
            "data_collection_approach": "Single comprehensive form with jurisdiction-specific sections",
            "validation_rules": self._generate_validation_rules()
        }
    
    def _generate_validation_rules(self) -> List[str]:
        """Generate validation rules for unified form"""
        return [
            "All personal information fields are mandatory",
            "Government ID must be valid and not expired",
            "Financial information must be consistent and verifiable",
            "Investment profile must be complete for suitability assessment",
            "Compliance screening must clear all jurisdictional requirements",
            "Jurisdiction-specific fields mandatory based on account types requested"
        ]
    
    def _generate_data_mapping_strategy(self, unified_fields: set, jurisdiction_specific_fields: Dict[str, set]) -> Dict[str, Any]:
        """Generate data mapping strategy for different jurisdictions"""
        
        return {
            "approach": "Collect once, map to multiple jurisdictions",
            "data_storage": {
                "master_record": "Single customer master record with all data",
                "jurisdiction_views": "Filtered views for each jurisdiction's compliance team",
                "audit_trail": "Complete audit trail for all data access and modifications"
            },
            "field_mapping": {
                "US_specific": list(jurisdiction_specific_fields.get("US", [])),
                "EU_specific": list(jurisdiction_specific_fields.get("EU", [])),
                "UK_specific": list(jurisdiction_specific_fields.get("UK", []))
            },
            "data_governance": [
                "Data privacy compliance (GDPR for EU clients)",
                "Data retention policies per jurisdiction",
                "Cross-border data transfer protocols",
                "Regular data quality audits"
            ]
        }
    
    def _generate_implementation_approach(self) -> List[str]:
        """Generate implementation approach recommendations"""
        return [
            "Phase 1: Design unified customer data model",
            "Phase 2: Implement single data collection interface",
            "Phase 3: Create jurisdiction-specific data views and workflows",
            "Phase 4: Integrate with existing compliance systems",
            "Phase 5: Test with pilot customers across all jurisdictions",
            "Phase 6: Full rollout with comprehensive staff training"
        ]
    
    def _generate_compliance_checklist(self, cross_matched: List[CrossJurisdictionalRequirement]) -> List[Dict[str, Any]]:
        """Generate compliance checklist for implementation"""
        checklist = []
        
        for req in cross_matched:
            checklist_item = {
                "requirement": req.requirement_type,
                "checks": [],
                "documentation_needed": [],
                "review_frequency": "Annual"
            }
            
            # Add jurisdiction-specific checks
            for jurisdiction in req.jurisdictions:
                checklist_item["checks"].append(f"Verify compliance with {jurisdiction} {req.requirement_type} requirements")
                checklist_item["documentation_needed"].append(f"{jurisdiction} compliance documentation")
            
            checklist.append(checklist_item)
        
        return checklist
    
    def _serialize_jurisdiction_results(self, jurisdiction_results: Dict[str, JurisdictionResult]) -> Dict[str, Any]:
        """Serialize jurisdiction results for JSON output"""
        serialized = {}
        
        for jurisdiction, result in jurisdiction_results.items():
            serialized[jurisdiction] = {
                "jurisdiction": result.jurisdiction,
                "entities_count": len(result.entities),
                "activities_count": len(result.activities),
                "products_count": len(result.products),
                "documents_processed": result.documents_processed,
                "top_entities": [e.name for e in result.entities[:5]],
                "top_activities": [a.name for a in result.activities[:5]],
                "top_products": [p.name for p in result.products[:5]],
                "specific_requirements_count": len(result.specific_requirements),
                "definitions_count": len(result.definitions)
            }
        
        return serialized
    
    def _generate_summary(self, jurisdiction_results: Dict[str, JurisdictionResult], cross_matched: List[CrossJurisdictionalRequirement]) -> Dict[str, Any]:
        """Generate summary of cross-jurisdictional analysis"""
        
        total_entities = sum(len(r.entities) for r in jurisdiction_results.values())
        total_activities = sum(len(r.activities) for r in jurisdiction_results.values())
        total_products = sum(len(r.products) for r in jurisdiction_results.values())
        total_documents = sum(r.documents_processed for r in jurisdiction_results.values())
        
        return {
            "jurisdictions_analyzed": len(jurisdiction_results),
            "total_entities_found": total_entities,
            "total_activities_found": total_activities,
            "total_products_found": total_products,
            "total_documents_processed": total_documents,
            "cross_matched_requirements": len(cross_matched),
            "analysis_completion_time": datetime.now().isoformat(),
            "key_findings": [
                f"Analyzed {len(jurisdiction_results)} jurisdictions comprehensively",
                f"Identified {len(cross_matched)} cross-jurisdictional requirements",
                f"Processed {total_documents} regulatory documents",
                "Generated unified customer data collection recommendations"
            ]
        }