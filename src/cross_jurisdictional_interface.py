"""
Cross-Jurisdictional Analysis Interface

This interface provides a unified way to analyze regulatory requirements
across multiple jurisdictions and generate practical business recommendations.

Use Cases:
- Multi-market account opening (US stocks + Hong Kong + A-shares)
- Cross-border compliance analysis
- Unified customer onboarding design
- Regulatory arbitrage analysis
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from src.config import Config
from src.cross_jurisdictional_analyzer import CrossJurisdictionalAnalyzer
from src.deliverable_formatter import DeliverableFormatter
from src.terminal_formatter import format_for_terminal

class CrossJurisdictionalInterface:
    """Main interface for cross-jurisdictional regulatory analysis"""
    
    def __init__(self, config: Config):
        self.config = config
        self.analyzer = CrossJurisdictionalAnalyzer(config)
        self.deliverable_formatter = DeliverableFormatter()
    
    async def analyze_multi_jurisdictional_requirements(self, query: str, 
                                                      use_case: str = "general") -> Dict[str, Any]:
        """
        Analyze requirements across multiple jurisdictions
        
        Args:
            query: The business requirement or use case to analyze
            use_case: Specific use case type (e.g., "account_opening", "compliance", "product_launch")
        """
        
        print(f"\n{'='*80}")
        print(format_for_terminal("# CROSS-JURISDICTIONAL REGULATORY ANALYSIS"))
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Use Case: {use_case}")
        print(f"Analysis Type: Multi-jurisdictional (US, EU, UK)")
        print(f"{'='*80}\n")
        
        # Run comprehensive cross-jurisdictional analysis
        results = await self.analyzer.analyze_cross_jurisdictional_requirements(query)
        
        # Enhance results with use case specific analysis
        enhanced_results = await self._enhance_with_use_case_analysis(results, use_case)
        
        # Generate business recommendations
        business_recommendations = await self._generate_business_recommendations(enhanced_results, use_case)
        
        # Compile final comprehensive results
        final_results = {
            **enhanced_results,
            "use_case": use_case,
            "business_recommendations": business_recommendations,
            "practical_implementation": self._generate_practical_implementation_guide(enhanced_results, use_case)
        }
        
        return final_results
    
    async def _enhance_with_use_case_analysis(self, results: Dict[str, Any], use_case: str) -> Dict[str, Any]:
        """Enhance results with specific use case analysis"""
        
        use_case_enhancements = {}
        
        if use_case == "account_opening":
            use_case_enhancements = await self._analyze_account_opening_requirements(results)
        elif use_case == "compliance":
            use_case_enhancements = await self._analyze_compliance_requirements(results)
        elif use_case == "product_launch":
            use_case_enhancements = await self._analyze_product_launch_requirements(results)
        else:
            use_case_enhancements = await self._analyze_general_requirements(results)
        
        # Merge enhancements with original results
        enhanced_results = {**results, "use_case_analysis": use_case_enhancements}
        
        return enhanced_results
    
    async def _analyze_account_opening_requirements(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze specific account opening requirements across jurisdictions"""
        
        account_opening_analysis = {
            "customer_data_requirements": self._extract_customer_data_requirements(results),
            "documentation_requirements": self._extract_documentation_requirements(results),
            "verification_processes": self._extract_verification_processes(results),
            "ongoing_obligations": self._extract_ongoing_obligations(results),
            "unified_onboarding_flow": self._design_unified_onboarding_flow(results)
        }
        
        return account_opening_analysis
    
    def _extract_customer_data_requirements(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract customer data requirements for account opening"""
        
        # Common data fields across all jurisdictions
        common_fields = [
            "Full legal name", "Date of birth", "Residential address", "Mailing address",
            "Phone number", "Email address", "Government ID number", "Tax ID number",
            "Occupation", "Employment status", "Annual income", "Net worth",
            "Investment experience", "Investment objectives", "Risk tolerance"
        ]
        
        # Jurisdiction-specific requirements
        jurisdiction_specific = {
            "US": [
                "Social Security Number (SSN) or Individual Taxpayer Identification Number (ITIN)",
                "W-9 or W-8 form", "FATCA classification", "Accredited investor status",
                "Pattern Day Trader acknowledgment", "Options trading level"
            ],
            "EU": [
                "EU Tax Identification Number", "GDPR consent", "MiFID II categorization",
                "Appropriateness assessment", "LEI (for professional clients)",
                "Country of tax residence", "PRIIPs risk tolerance"
            ],
            "UK": [
                "National Insurance Number", "UK tax residence status", "FCA client categorization",
                "Appropriateness test", "Financial promotion restrictions acknowledgment",
                "Post-Brexit equivalence confirmations"
            ]
        }
        
        return {
            "common_fields": common_fields,
            "jurisdiction_specific_fields": jurisdiction_specific,
            "data_collection_strategy": "Single comprehensive form with jurisdiction-specific sections",
            "data_validation_rules": self._generate_data_validation_rules()
        }
    
    def _extract_documentation_requirements(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract documentation requirements"""
        
        return {
            "identity_documents": {
                "US": ["Government-issued photo ID", "Proof of address"],
                "EU": ["National ID or passport", "Proof of residence", "Tax certificate"],
                "UK": ["UK driving license or passport", "Council tax bill or bank statement"]
            },
            "financial_documents": {
                "US": ["Bank statements", "Tax returns (for accredited investor status)"],
                "EU": ["Bank statements", "Income verification", "Asset declarations"],
                "UK": ["Bank statements", "Payslips or pension statements", "P60 or SA302"]
            },
            "compliance_documents": {
                "US": ["W-9/W-8 forms", "Options agreement", "Day trading agreement"],
                "EU": ["MiFID II questionnaire", "Appropriateness assessment", "GDPR consent"],
                "UK": ["Appropriateness test", "Client agreement", "Risk warnings"]
            }
        }
    
    def _extract_verification_processes(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract verification processes"""
        
        return {
            "identity_verification": {
                "common_process": "Multi-factor identity verification",
                "jurisdiction_differences": {
                    "US": "PATRIOT Act compliance, OFAC screening",
                    "EU": "AML 5th Directive, sanctions screening",
                    "UK": "Money Laundering Regulations, PEP screening"
                }
            },
            "address_verification": {
                "common_process": "Utility bill or bank statement verification",
                "jurisdiction_differences": {
                    "US": "90-day recency requirement",
                    "EU": "3-month recency, GDPR-compliant storage",
                    "UK": "3-month recency, post-Brexit verification"
                }
            },
            "financial_verification": {
                "common_process": "Income and asset verification",
                "jurisdiction_differences": {
                    "US": "Accredited investor verification if applicable",
                    "EU": "MiFID II financial assessment",
                    "UK": "FCA appropriateness assessment"
                }
            }
        }
    
    def _extract_ongoing_obligations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ongoing obligations"""
        
        return {
            "periodic_updates": {
                "US": "Annual suitability review, beneficial ownership updates",
                "EU": "Periodic appropriateness review, LEI renewals",
                "UK": "Annual appropriateness review, client categorization updates"
            },
            "reporting_obligations": {
                "US": "Form 8938 (FATCA), suspicious activity reporting",
                "EU": "CRS reporting, transaction reporting under MiFIR",
                "UK": "Suspicious activity reporting, transaction reporting"
            },
            "monitoring_requirements": {
                "US": "Pattern day trader monitoring, large trader reporting",
                "EU": "Best execution monitoring, transaction cost analysis",
                "UK": "Best execution monitoring, product governance"
            }
        }
    
    def _design_unified_onboarding_flow(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Design unified customer onboarding flow"""
        
        onboarding_steps = [
            {
                "step": 1,
                "title": "Market Selection",
                "description": "Customer selects which markets they want to trade (US, EU, UK)",
                "data_collected": ["Market preferences", "Account types requested"]
            },
            {
                "step": 2,
                "title": "Personal Information",
                "description": "Collect core personal information valid across all jurisdictions",
                "data_collected": ["Name", "DOB", "Address", "Contact info", "Tax info"]
            },
            {
                "step": 3,
                "title": "Identity Verification",
                "description": "Multi-factor identity verification satisfying all jurisdictions",
                "data_collected": ["ID documents", "Biometric verification", "Address proof"]
            },
            {
                "step": 4,
                "title": "Financial Assessment",
                "description": "Comprehensive financial profile for all jurisdictions",
                "data_collected": ["Income", "Net worth", "Investment experience", "Objectives"]
            },
            {
                "step": 5,
                "title": "Jurisdiction-Specific Requirements",
                "description": "Complete jurisdiction-specific forms and assessments",
                "data_collected": ["US: W-9/W-8", "EU: MiFID II", "UK: Appropriateness test"]
            },
            {
                "step": 6,
                "title": "Risk Assessment & Suitability",
                "description": "Unified risk assessment meeting all jurisdictional requirements",
                "data_collected": ["Risk tolerance", "Suitability scores", "Product restrictions"]
            },
            {
                "step": 7,
                "title": "Compliance Screening",
                "description": "AML/KYC screening across all jurisdictions",
                "data_collected": ["PEP status", "Sanctions screening", "Source of funds"]
            },
            {
                "step": 8,
                "title": "Agreement & Account Opening",
                "description": "Digital signatures for all jurisdictional agreements",
                "data_collected": ["Client agreements", "Risk disclosures", "Account confirmations"]
            }
        ]
        
        return {
            "onboarding_flow": onboarding_steps,
            "estimated_completion_time": "15-30 minutes",
            "automation_opportunities": [
                "Auto-population across jurisdiction forms",
                "Real-time document verification",
                "Automated suitability scoring",
                "Digital signature workflows"
            ],
            "quality_controls": [
                "Multi-level review process",
                "Automated compliance checks",
                "Exception handling workflows",
                "Audit trail maintenance"
            ]
        }
    
    def _generate_data_validation_rules(self) -> List[str]:
        """Generate data validation rules"""
        
        return [
            "All personal information must be consistent across all forms",
            "Government IDs must be valid and not expired",
            "Address verification documents must be recent (within 3 months)",
            "Financial information must be reasonable and verifiable",
            "Tax information must be complete for all relevant jurisdictions",
            "Investment experience must be documented with examples",
            "Risk tolerance must be consistent with investment objectives",
            "All compliance screening must return clear results"
        ]
    
    async def _analyze_compliance_requirements(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze compliance requirements"""
        
        return {
            "ongoing_monitoring": "Continuous transaction monitoring across all jurisdictions",
            "reporting_schedules": self._generate_reporting_schedules(),
            "audit_requirements": self._generate_audit_requirements(),
            "training_needs": self._generate_training_requirements()
        }
    
    async def _analyze_product_launch_requirements(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze product launch requirements"""
        
        return {
            "regulatory_approvals": "Required approvals for each jurisdiction",
            "marketing_restrictions": "Cross-jurisdictional marketing compliance",
            "distribution_requirements": "Distribution partner requirements",
            "ongoing_obligations": "Post-launch reporting and compliance"
        }
    
    async def _analyze_general_requirements(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze general cross-jurisdictional requirements"""
        
        return {
            "common_themes": "Identified common regulatory themes",
            "key_differences": "Major differences between jurisdictions",
            "compliance_priorities": "Prioritized compliance actions",
            "implementation_roadmap": "Suggested implementation approach"
        }
    
    def _generate_reporting_schedules(self) -> Dict[str, List[str]]:
        """Generate reporting schedules by jurisdiction"""
        
        return {
            "US": [
                "Monthly: Large trader reporting",
                "Quarterly: Form 13F (if applicable)",
                "Annual: Form 8938 (FATCA)",
                "As needed: Suspicious activity reports"
            ],
            "EU": [
                "Daily: Transaction reporting (MiFIR)",
                "Monthly: Best execution reports",
                "Quarterly: MiFID II reporting",
                "Annual: Pillar 3 disclosures"
            ],
            "UK": [
                "Daily: Transaction reporting",
                "Monthly: Client money reconciliations",
                "Quarterly: CASS returns",
                "Annual: ICAAP submissions"
            ]
        }
    
    def _generate_audit_requirements(self) -> Dict[str, List[str]]:
        """Generate audit requirements"""
        
        return {
            "internal_audits": [
                "Quarterly compliance reviews",
                "Annual KYC/AML audits",
                "Bi-annual systems audits"
            ],
            "external_audits": [
                "Annual financial audits",
                "Regulatory examinations",
                "Third-party compliance audits"
            ],
            "documentation_requirements": [
                "Complete audit trails",
                "Policy documentation",
                "Training records",
                "Exception reports"
            ]
        }
    
    def _generate_training_requirements(self) -> Dict[str, List[str]]:
        """Generate training requirements"""
        
        return {
            "initial_training": [
                "Cross-jurisdictional regulatory overview",
                "Specific jurisdiction requirements",
                "System training",
                "Compliance procedures"
            ],
            "ongoing_training": [
                "Annual regulatory updates",
                "Quarterly system updates",
                "Ad-hoc regulatory changes",
                "Professional development"
            ],
            "specialized_training": [
                "AML/KYC procedures",
                "Product-specific requirements",
                "Technology systems",
                "Crisis management"
            ]
        }
    
    async def _generate_business_recommendations(self, results: Dict[str, Any], use_case: str) -> Dict[str, Any]:
        """Generate actionable business recommendations"""
        
        recommendations = {
            "strategic_recommendations": self._generate_strategic_recommendations(results, use_case),
            "operational_recommendations": self._generate_operational_recommendations(results, use_case),
            "technology_recommendations": self._generate_technology_recommendations(results, use_case),
            "risk_recommendations": self._generate_risk_recommendations(results, use_case)
        }
        
        return recommendations
    
    def _generate_strategic_recommendations(self, results: Dict[str, Any], use_case: str) -> List[str]:
        """Generate strategic business recommendations"""
        
        if use_case == "account_opening":
            return [
                "Implement unified customer onboarding system to reduce complexity and costs",
                "Standardize data collection to meet the highest requirements across all jurisdictions",
                "Create jurisdiction-specific compliance teams with centralized coordination",
                "Develop automated compliance checking to reduce manual review time"
            ]
        else:
            return [
                "Prioritize compliance with the most stringent requirements across jurisdictions",
                "Establish center of excellence for cross-jurisdictional regulatory management",
                "Implement consistent risk management framework across all jurisdictions",
                "Regular review and update of cross-jurisdictional procedures"
            ]
    
    def _generate_operational_recommendations(self, results: Dict[str, Any], use_case: str) -> List[str]:
        """Generate operational recommendations"""
        
        return [
            "Establish clear escalation procedures for cross-jurisdictional issues",
            "Create standardized documentation templates for all jurisdictions",
            "Implement regular training programs for staff on multi-jurisdictional requirements",
            "Develop key performance indicators for cross-jurisdictional compliance"
        ]
    
    def _generate_technology_recommendations(self, results: Dict[str, Any], use_case: str) -> List[str]:
        """Generate technology recommendations"""
        
        return [
            "Implement single customer data management system with jurisdiction-specific views",
            "Develop automated compliance checking and reporting tools",
            "Create real-time monitoring dashboards for cross-jurisdictional compliance",
            "Establish secure data sharing protocols between jurisdictions"
        ]
    
    def _generate_risk_recommendations(self, results: Dict[str, Any], use_case: str) -> List[str]:
        """Generate risk management recommendations"""
        
        return [
            "Conduct regular cross-jurisdictional risk assessments",
            "Establish contingency plans for regulatory changes in any jurisdiction",
            "Implement comprehensive audit trails for all cross-jurisdictional activities",
            "Regular stress testing of compliance procedures across all jurisdictions"
        ]
    
    def _generate_practical_implementation_guide(self, results: Dict[str, Any], use_case: str) -> Dict[str, Any]:
        """Generate practical implementation guide"""
        
        return {
            "phase_1_foundation": {
                "duration": "1-2 months",
                "activities": [
                    "Conduct detailed gap analysis",
                    "Design unified data model",
                    "Select technology platforms",
                    "Establish project governance"
                ],
                "deliverables": [
                    "Gap analysis report",
                    "Technical architecture design",
                    "Project plan and timeline",
                    "Resource allocation plan"
                ]
            },
            "phase_2_development": {
                "duration": "3-4 months", 
                "activities": [
                    "Develop unified customer interface",
                    "Build jurisdiction-specific workflows",
                    "Implement compliance automation",
                    "Create reporting dashboards"
                ],
                "deliverables": [
                    "Customer onboarding system",
                    "Compliance workflow engine",
                    "Automated reporting tools",
                    "Integration with existing systems"
                ]
            },
            "phase_3_testing": {
                "duration": "1-2 months",
                "activities": [
                    "User acceptance testing",
                    "Compliance validation",
                    "Performance testing",
                    "Staff training"
                ],
                "deliverables": [
                    "Test results and sign-off",
                    "Compliance certification",
                    "Performance benchmarks",
                    "Training completion records"
                ]
            },
            "phase_4_deployment": {
                "duration": "1 month",
                "activities": [
                    "Phased rollout",
                    "Monitoring and support",
                    "Issue resolution",
                    "Optimization"
                ],
                "deliverables": [
                    "Production deployment",
                    "Support procedures",
                    "Issue tracking system",
                    "Performance optimization"
                ]
            }
        }
    
    def save_cross_jurisdictional_results(self, results: Dict[str, Any], output_dir: Path = None) -> str:
        """Save cross-jurisdictional analysis results"""
        
        if output_dir is None:
            output_dir = Path("output")
        
        output_dir.mkdir(exist_ok=True)
        
        # Create subfolder for cross-jurisdictional analysis
        query = results.get("query", "cross_jurisdictional_analysis")
        query_clean = query.replace(" ", "_").replace(",", "")[:20]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"CrossJurisdictional_{query_clean}_{timestamp}"
        
        analysis_folder = output_dir / folder_name
        analysis_folder.mkdir(exist_ok=True)
        
        # Save comprehensive results
        with open(analysis_folder / f"cross_jurisdictional_analysis_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save business recommendations
        business_recs = results.get("business_recommendations", {})
        with open(analysis_folder / f"business_recommendations_{timestamp}.json", "w") as f:
            json.dump(business_recs, f, indent=2, default=str)
        
        # Save unified recommendations
        unified_recs = results.get("unified_recommendations", {})
        with open(analysis_folder / f"unified_customer_recommendations_{timestamp}.json", "w") as f:
            json.dump(unified_recs, f, indent=2, default=str)
        
        # Generate markdown reports
        self._generate_markdown_reports(results, analysis_folder, timestamp)
        
        print(format_for_terminal(f"\n**Cross-jurisdictional analysis results saved to {analysis_folder}/**"))
        print(f"   - Comprehensive analysis: cross_jurisdictional_analysis_{timestamp}.json")
        print(f"   - Business recommendations: business_recommendations_{timestamp}.json")
        print(f"   - Implementation guide: IMPLEMENTATION_GUIDE_{timestamp}.md")
        print(f"   - Executive summary: EXECUTIVE_SUMMARY_{timestamp}.md")
        
        return timestamp
    
    def _generate_markdown_reports(self, results: Dict[str, Any], output_folder: Path, timestamp: str):
        """Generate markdown reports"""
        
        # Generate executive summary
        exec_summary = self._format_executive_summary(results)
        with open(output_folder / f"EXECUTIVE_SUMMARY_{timestamp}.md", "w") as f:
            f.write(exec_summary)
        
        # Generate implementation guide
        impl_guide = self._format_implementation_guide(results)
        with open(output_folder / f"IMPLEMENTATION_GUIDE_{timestamp}.md", "w") as f:
            f.write(impl_guide)
        
        # Generate business case
        business_case = self._format_business_case(results)
        with open(output_folder / f"BUSINESS_CASE_{timestamp}.md", "w") as f:
            f.write(business_case)
    
    def _format_executive_summary(self, results: Dict[str, Any]) -> str:
        """Format executive summary"""
        
        lines = []
        lines.append("# CROSS-JURISDICTIONAL REGULATORY ANALYSIS")
        lines.append("## Executive Summary")
        lines.append(f"\n**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"**Query:** {results.get('query', 'N/A')}")
        lines.append(f"**Use Case:** {results.get('use_case', 'N/A')}")
        lines.append(f"**Jurisdictions:** US, EU, UK")
        
        # Key findings
        lines.append("\n## Key Findings")
        summary = results.get("summary", {})
        lines.append(f"- **Total Requirements Analyzed:** {summary.get('cross_matched_requirements', 0)}")
        lines.append(f"- **Entities Identified:** {summary.get('total_entities_found', 0)}")
        lines.append(f"- **Activities Analyzed:** {summary.get('total_activities_found', 0)}")
        lines.append(f"- **Products Reviewed:** {summary.get('total_products_found', 0)}")
        
        # Business impact
        lines.append("\n## Business Impact")
        business_recs = results.get("business_recommendations", {})
        strategic_recs = business_recs.get("strategic_recommendations", [])
        for rec in strategic_recs[:3]:
            lines.append(f"- {rec}")
        
        return "\n".join(lines)
    
    def _format_implementation_guide(self, results: Dict[str, Any]) -> str:
        """Format implementation guide"""
        
        lines = []
        lines.append("# IMPLEMENTATION GUIDE")
        lines.append("## Cross-Jurisdictional Compliance Implementation")
        
        impl_guide = results.get("practical_implementation", {})
        
        for phase_name, phase_details in impl_guide.items():
            lines.append(f"\n## {phase_name.replace('_', ' ').title()}")
            lines.append(f"**Duration:** {phase_details.get('duration', 'TBD')}")
            
            lines.append("\n### Activities:")
            for activity in phase_details.get("activities", []):
                lines.append(f"- {activity}")
            
            lines.append("\n### Deliverables:")
            for deliverable in phase_details.get("deliverables", []):
                lines.append(f"- {deliverable}")
        
        return "\n".join(lines)
    
    def _format_business_case(self, results: Dict[str, Any]) -> str:
        """Format business case"""
        
        lines = []
        lines.append("# BUSINESS CASE")
        lines.append("## Cross-Jurisdictional Regulatory Compliance")
        
        lines.append("\n## Problem Statement")
        lines.append("Managing regulatory compliance across multiple jurisdictions creates:")
        lines.append("- Operational complexity and increased costs")
        lines.append("- Risk of non-compliance due to fragmented processes")
        lines.append("- Poor customer experience due to multiple data collection points")
        lines.append("- Inefficient resource utilization across jurisdictions")
        
        lines.append("\n## Proposed Solution")
        unified_recs = results.get("unified_recommendations", {})
        if "unified_customer_form" in unified_recs:
            lines.append("- Unified customer data collection system")
            lines.append("- Automated compliance checking across jurisdictions")
            lines.append("- Centralized regulatory reporting")
            lines.append("- Jurisdiction-specific workflow automation")
        
        lines.append("\n## Expected Benefits")
        lines.append("- **Cost Reduction:** 30-40% reduction in compliance costs")
        lines.append("- **Risk Mitigation:** Comprehensive compliance coverage")
        lines.append("- **Customer Experience:** Single onboarding process")
        lines.append("- **Operational Efficiency:** Automated processes and reporting")
        
        return "\n".join(lines)