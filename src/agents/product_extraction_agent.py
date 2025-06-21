from typing import List, Dict, Any, Optional
import re
from src.models import Document, RegulatedProduct, ProductType

class ProductExtractionAgent:
    """Agent specialized in extracting regulated products from documents"""
    
    def __init__(self):
        # Product patterns and keywords
        self.product_patterns = {
            ProductType.MUTUAL_FUND: [
                r"mutual fund[s]?",
                r"open-end(?:ed)? (?:investment )?fund[s]?",
                r"open-end(?:ed)? compan(?:y|ies)"
            ],
            ProductType.ETF: [
                r"ETF[s]?",
                r"exchange[- ]traded fund[s]?",
                r"exchange[- ]traded product[s]?"
            ],
            ProductType.UCITS_FUND: [
                r"UCITS fund[s]?",
                r"UCITS scheme[s]?",
                r"UCITS product[s]?",
                r"UCITS-compliant fund[s]?"
            ],
            ProductType.HEDGE_FUND: [
                r"hedge fund[s]?",
                r"alternative investment fund[s]?",
                r"AIF[s]?",
                r"private fund[s]?"
            ],
            ProductType.MONEY_MARKET_FUND: [
                r"money market fund[s]?",
                r"MMF[s]?",
                r"money market mutual fund[s]?",
                r"cash management fund[s]?"
            ],
            ProductType.INVESTMENT_TRUST: [
                r"investment trust[s]?",
                r"closed-end(?:ed)? fund[s]?",
                r"closed-end(?:ed)? investment compan(?:y|ies)"
            ],
            ProductType.COLLECTIVE_INVESTMENT_SCHEME: [
                r"collective investment scheme[s]?",
                r"CIS",
                r"pooled investment vehicle[s]?",
                r"collective investment undertaking[s]?"
            ]
        }
        
        self.product_characteristics = {
            "transferable securities": ["equity", "bonds", "shares", "securities"],
            "money market instruments": ["treasury bills", "commercial paper", "certificates of deposit"],
            "derivatives": ["futures", "options", "swaps", "forwards"],
            "commodities": ["gold", "silver", "oil", "agricultural products"],
            "real estate": ["property", "real estate", "REIT"]
        }
    
    def extract_products(self, document: Document) -> List[RegulatedProduct]:
        """Extract regulated products from a document"""
        products = []
        processed_products = set()
        
        full_text = self._get_full_text(document)
        
        for product_type, patterns in self.product_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                
                for match in matches:
                    product_name = match.group(0)
                    context = self._extract_context(full_text, match.start(), match.end())
                    
                    # Create unique key
                    product_key = f"{product_name.lower()}_{product_type.value}"
                    
                    if product_key not in processed_products:
                        processed_products.add(product_key)
                        
                        product = RegulatedProduct(
                            name=self._normalize_product_name(product_name),
                            type="product",
                            product_type=product_type,
                            description=self._generate_description(product_name, context),
                            source_document_id=document.document_id,
                            source_text=context,
                            confidence=self._calculate_confidence(product_name, context),
                            metadata={
                                "document_title": document.title or "Unknown",
                                "publishers": [p.get("name", "") for p in document.publishers] if document.publishers else [],
                                "published_date": document.published or "Unknown",
                                "asset_classes": self._extract_asset_classes(context)
                            },
                            issuer_requirements=self._extract_issuer_requirements(context),
                            investor_restrictions=self._extract_investor_restrictions(context)
                        )
                        products.append(product)
        
        # Extract products from specific regulatory contexts
        products.extend(self._extract_from_regulatory_context(document))
        
        return products
    
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
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 400) -> str:
        """Extract context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _normalize_product_name(self, product_name: str) -> str:
        """Normalize product name for consistency"""
        # Standardize abbreviations
        replacements = {
            r"\bETF[s]?\b": "Exchange-Traded Fund",
            r"\bMMF[s]?\b": "Money Market Fund",
            r"\bAIF[s]?\b": "Alternative Investment Fund",
            r"\bCIS\b": "Collective Investment Scheme",
            r"\bREIT[s]?\b": "Real Estate Investment Trust"
        }
        
        normalized = product_name
        for pattern, replacement in replacements.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        return " ".join(normalized.split()).title()
    
    def _generate_description(self, product_name: str, context: str) -> str:
        """Generate description based on product and context"""
        product_lower = product_name.lower()
        
        descriptions = {
            "mutual fund": "Open-ended investment fund that pools money from investors to invest in securities",
            "etf": "Investment fund traded on stock exchanges that tracks an index, commodity, or basket of assets",
            "ucits": "Harmonized investment fund that can be sold across EU member states",
            "hedge fund": "Alternative investment fund using complex strategies to generate returns",
            "money market fund": "Investment fund investing in short-term, high-quality debt securities",
            "investment trust": "Closed-ended investment company with a fixed number of shares",
            "collective investment scheme": "Investment vehicle that pools money from multiple investors"
        }
        
        for key, desc in descriptions.items():
            if key in product_lower:
                return desc
        
        # Extract description from context if available
        desc_match = re.search(r"(?:is|means|refers to) ([^.]+)", context, re.IGNORECASE)
        if desc_match:
            return desc_match.group(1).strip()
        
        return f"Regulated investment product: {product_name}"
    
    def _calculate_confidence(self, product_name: str, context: str) -> float:
        """Calculate confidence score for extracted product"""
        score = 0.6  # Base score
        
        # Check for product characteristics
        for char_type, keywords in self.product_characteristics.items():
            if any(keyword in context.lower() for keyword in keywords):
                score += 0.1
                break
        
        # Check for regulatory approval language
        approval_indicators = ["authorized", "approved", "registered", "regulated", "compliant"]
        if any(indicator in context.lower() for indicator in approval_indicators):
            score += 0.15
        
        # Check for investment-related terms
        investment_terms = ["invest", "portfolio", "asset", "share", "unit", "return", "yield"]
        if any(term in context.lower() for term in investment_terms):
            score += 0.15
        
        return min(score, 1.0)
    
    def _extract_asset_classes(self, context: str) -> List[str]:
        """Extract asset classes mentioned in context"""
        asset_classes = []
        
        for asset_type, keywords in self.product_characteristics.items():
            for keyword in keywords:
                if keyword in context.lower():
                    asset_classes.append(asset_type)
                    break
        
        return list(set(asset_classes))
    
    def _extract_issuer_requirements(self, context: str) -> List[str]:
        """Extract requirements for product issuers"""
        requirements = []
        
        # Look for issuer-specific requirements
        issuer_patterns = [
            r"(?:issuer|sponsor|promoter) (?:must|shall) [\w\s]+",
            r"(?:management company|fund manager) (?:must|shall) [\w\s]+",
            r"required (?:capital|assets|experience) [\w\s]+"
        ]
        
        for pattern in issuer_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                req_text = match.group(0).strip()
                if len(req_text) < 150:  # Avoid very long matches
                    requirements.append(req_text)
        
        return requirements[:5]  # Limit to top 5
    
    def _extract_investor_restrictions(self, context: str) -> List[str]:
        """Extract investor restrictions or eligibility criteria"""
        restrictions = []
        
        # Look for investor-related restrictions
        investor_patterns = [
            r"(?:investor[s]?|subscriber[s]?) (?:must|shall|cannot) [\w\s]+",
            r"(?:minimum|maximum) (?:investment|subscription) [\w\s]+",
            r"(?:restricted to|limited to|available to) [\w\s]+",
            r"(?:qualified|accredited|institutional) investor[s]?"
        ]
        
        for pattern in investor_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                restriction_text = match.group(0).strip()
                if len(restriction_text) < 150:
                    restrictions.append(restriction_text)
        
        return restrictions[:5]  # Limit to top 5
    
    def _extract_from_regulatory_context(self, document: Document) -> List[RegulatedProduct]:
        """Extract products from regulatory-specific contexts"""
        products = []
        
        if not document.title:
            return products
            
        # Check document title and metadata for product references
        title_lower = document.title.lower()
        
        # Investment Company Act products
        if "investment company act" in title_lower:
            if "open-end" in title_lower or "mutual fund" in title_lower:
                products.append(self._create_contextual_product(
                    "Mutual Fund (1940 Act)",
                    ProductType.MUTUAL_FUND,
                    "Open-end investment company registered under the Investment Company Act of 1940",
                    document
                ))
            if "closed-end" in title_lower:
                products.append(self._create_contextual_product(
                    "Closed-End Fund (1940 Act)",
                    ProductType.INVESTMENT_TRUST,
                    "Closed-end investment company registered under the Investment Company Act of 1940",
                    document
                ))
        
        # UCITS products
        if "ucits" in title_lower:
            products.append(self._create_contextual_product(
                "UCITS Fund",
                ProductType.UCITS_FUND,
                "Undertaking for Collective Investment in Transferable Securities",
                document
            ))
        
        return products
    
    def _create_contextual_product(self, name: str, product_type: ProductType, 
                                 description: str, document: Document) -> RegulatedProduct:
        """Create a product from regulatory context"""
        return RegulatedProduct(
            name=name,
            type="product",
            product_type=product_type,
            description=description,
            source_document_id=document.document_id,
            source_text=document.title,
            confidence=0.9,  # High confidence for title-based extraction
            metadata={
                "document_title": document.title or "Unknown",
                "extraction_method": "regulatory_context"
            }
        )