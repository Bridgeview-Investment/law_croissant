import networkx as nx
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from loguru import logger
import json


class HierarchyBuilder:
    """Build hierarchical structures for regulatory entities"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entity_embeddings = {}
        self.vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 3))
        
        # Industry standard mappings
        self.industry_taxonomies = self._load_industry_taxonomies()
        
    def _load_industry_taxonomies(self) -> Dict[str, Dict]:
        """Load industry standard taxonomies"""
        return {
            "ISO10962": {
                "E": "Equities",
                "D": "Debt instruments",
                "C": "Collective investment vehicles",
                "R": "Referential instruments",
                "O": "Options",
                "F": "Futures",
                "S": "Swaps",
                "H": "Non-listed and complex listed options",
                "I": "Spot",
                "J": "Forwards",
                "K": "Strategies",
                "L": "Financing",
                "T": "Commodities",
                "M": "Others (miscellaneous)"
            },
            "ENTITY_HIERARCHY": {
                "FINANCIAL_INSTITUTION": {
                    "CREDIT_INSTITUTION": ["Bank", "Savings Bank", "Credit Union"],
                    "INVESTMENT_FIRM": ["Broker-Dealer", "Portfolio Manager", "Investment Adviser"],
                    "FUND_MANAGER": ["UCITS ManCo", "AIFM", "Registered Investment Company"]
                },
                "INVESTMENT_VEHICLE": {
                    "UCITS": ["Equity Fund", "Bond Fund", "Money Market Fund", "Mixed Fund"],
                    "AIF": ["Hedge Fund", "Private Equity Fund", "Real Estate Fund", "Fund of Funds"],
                    "OTHER": ["ETF", "Investment Trust", "Unit Trust"]
                },
                "MARKET_PARTICIPANT": {
                    "INFRASTRUCTURE": ["Exchange", "CCP", "CSD", "Trade Repository"],
                    "SERVICE_PROVIDER": ["Custodian", "Depositary", "Administrator", "Auditor"]
                }
            },
            "ACTIVITY_CATEGORIES": {
                "CORE_INVESTMENT_SERVICES": [
                    "Reception and transmission of orders",
                    "Execution of orders",
                    "Dealing on own account",
                    "Portfolio management",
                    "Investment advice",
                    "Underwriting",
                    "Placing"
                ],
                "ANCILLARY_SERVICES": [
                    "Safekeeping and administration",
                    "Granting credits or loans",
                    "Foreign exchange services",
                    "Investment research",
                    "Services related to underwriting"
                ],
                "FUND_ACTIVITIES": [
                    "Management of UCITS",
                    "Management of AIFs",
                    "Risk management",
                    "Administration",
                    "Marketing",
                    "Distribution"
                ]
            }
        }
    
    def build_entity_hierarchy(self, entities: List[Dict]) -> nx.DiGraph:
        """Build hierarchical graph from entities"""
        logger.info(f"Building hierarchy for {len(entities)} entities")
        
        # Clear existing graph
        self.graph.clear()
        
        # Group entities by type
        entities_by_type = defaultdict(list)
        for entity in entities:
            entities_by_type[entity.get("entity_type", "UNKNOWN")].append(entity)
        
        # Create root nodes for each type
        for entity_type in entities_by_type:
            self.graph.add_node(entity_type, node_type="root", level=0)
        
        # Add entities and build relationships
        for entity_type, entity_list in entities_by_type.items():
            self._add_entities_to_graph(entity_type, entity_list)
        
        # Infer additional relationships
        self._infer_relationships()
        
        # Calculate hierarchy metrics
        self._calculate_metrics()
        
        return self.graph
    
    def _add_entities_to_graph(self, entity_type: str, entities: List[Dict]):
        """Add entities to graph with relationships"""
        
        # Find matching categories from taxonomy
        for entity in entities:
            entity_name = entity.get("name", "")
            entity_id = f"{entity_type}:{entity_name}"
            
            # Add entity node
            self.graph.add_node(
                entity_id,
                name=entity_name,
                entity_type=entity_type,
                node_type="entity",
                level=1,
                **entity
            )
            
            # Connect to type root
            self.graph.add_edge(entity_type, entity_id)
            
            # Find parent in taxonomy
            parent = self._find_taxonomy_parent(entity_name, entity_type)
            if parent and parent != entity_type:
                parent_id = f"{entity_type}:{parent}"
                if parent_id not in self.graph:
                    self.graph.add_node(
                        parent_id,
                        name=parent,
                        entity_type=entity_type,
                        node_type="category",
                        level=1
                    )
                    self.graph.add_edge(entity_type, parent_id)
                
                # Remove direct connection to root and connect to parent
                if self.graph.has_edge(entity_type, entity_id):
                    self.graph.remove_edge(entity_type, entity_id)
                self.graph.add_edge(parent_id, entity_id)
                
                # Update level
                self.graph.nodes[entity_id]["level"] = 2
    
    def _find_taxonomy_parent(self, entity_name: str, entity_type: str) -> Optional[str]:
        """Find parent category from industry taxonomies"""
        
        entity_name_lower = entity_name.lower()
        
        # Check entity hierarchy
        if entity_type in ["ORGANIZATION", "FINANCIAL_INSTITUTION"]:
            for main_cat, subcats in self.industry_taxonomies["ENTITY_HIERARCHY"].items():
                if isinstance(subcats, dict):
                    for subcat, examples in subcats.items():
                        for example in examples:
                            if example.lower() in entity_name_lower or entity_name_lower in example.lower():
                                return subcat
                        if subcat.lower() in entity_name_lower:
                            return main_cat
        
        # Check activity categories
        elif entity_type == "ACTIVITY":
            for category, activities in self.industry_taxonomies["ACTIVITY_CATEGORIES"].items():
                for activity in activities:
                    if activity.lower() in entity_name_lower or entity_name_lower in activity.lower():
                        return category
        
        # Check product types (ISO10962 simplified)
        elif entity_type == "PRODUCT":
            product_keywords = {
                "Equities": ["equity", "share", "stock"],
                "Debt": ["bond", "note", "debt", "debenture"],
                "Funds": ["fund", "ucits", "aif", "collective investment"],
                "Derivatives": ["option", "future", "swap", "derivative", "forward"]
            }
            
            for category, keywords in product_keywords.items():
                if any(keyword in entity_name_lower for keyword in keywords):
                    return category
        
        return None
    
    def _infer_relationships(self):
        """Infer additional relationships between entities"""
        
        # Get all entity nodes
        entity_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "entity"]
        
        # Calculate similarity between entities
        if len(entity_nodes) > 1:
            entity_texts = [self.graph.nodes[n].get("name", "") for n in entity_nodes]
            
            # Create TF-IDF vectors
            try:
                tfidf_matrix = self.vectorizer.fit_transform(entity_texts)
                similarities = cosine_similarity(tfidf_matrix)
                
                # Add edges for highly similar entities
                threshold = 0.7
                for i in range(len(entity_nodes)):
                    for j in range(i + 1, len(entity_nodes)):
                        if similarities[i, j] > threshold:
                            node_i, node_j = entity_nodes[i], entity_nodes[j]
                            
                            # Only add relationship if they're not already connected
                            if not nx.has_path(self.graph, node_i, node_j):
                                self.graph.add_edge(
                                    node_i, node_j,
                                    relationship="similar",
                                    weight=similarities[i, j]
                                )
            except Exception as e:
                logger.warning(f"Could not calculate similarities: {e}")
    
    def _calculate_metrics(self):
        """Calculate hierarchy metrics"""
        
        # Calculate centrality
        try:
            centrality = nx.degree_centrality(self.graph)
            for node, cent in centrality.items():
                self.graph.nodes[node]["centrality"] = cent
        except:
            pass
        
        # Calculate depths
        for root in [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "root"]:
            depths = nx.single_source_shortest_path_length(self.graph, root)
            for node, depth in depths.items():
                if "depth" not in self.graph.nodes[node] or depth < self.graph.nodes[node]["depth"]:
                    self.graph.nodes[node]["depth"] = depth
    
    def get_entity_hierarchy_table(self) -> pd.DataFrame:
        """Generate hierarchy table for entities"""
        
        data = []
        
        for node, attrs in self.graph.nodes(data=True):
            if attrs.get("node_type") in ["entity", "category"]:
                # Find parent
                parents = list(self.graph.predecessors(node))
                parent = parents[0] if parents else None
                
                # Find root
                root = None
                if parent:
                    root_path = nx.shortest_path(self.graph, source=None, target=node)
                    root = root_path[0] if root_path else None
                
                data.append({
                    "entity_id": node,
                    "entity_name": attrs.get("name", ""),
                    "entity_type": attrs.get("entity_type", ""),
                    "category": attrs.get("node_type", ""),
                    "parent_entity": parent,
                    "root_category": root,
                    "level": attrs.get("level", 0),
                    "depth": attrs.get("depth", 0),
                    "centrality": attrs.get("centrality", 0),
                    "confidence": attrs.get("confidence", 1.0)
                })
        
        df = pd.DataFrame(data)
        
        # Sort by hierarchy
        df = df.sort_values(["entity_type", "level", "entity_name"])
        
        return df
    
    def find_related_entities(self, entity_id: str, max_distance: int = 2) -> List[str]:
        """Find entities related within max_distance"""
        
        if entity_id not in self.graph:
            return []
        
        # Find all nodes within distance
        distances = nx.single_source_shortest_path_length(self.graph.to_undirected(), entity_id, cutoff=max_distance)
        
        # Filter to only entities
        related = [
            node for node, dist in distances.items()
            if dist > 0 and self.graph.nodes[node].get("node_type") == "entity"
        ]
        
        return related
    
    def export_hierarchy(self, filepath: str):
        """Export hierarchy to file"""
        
        # Convert to serializable format
        hierarchy_data = {
            "nodes": [
                {
                    "id": node,
                    **{k: v for k, v in attrs.items() if isinstance(v, (str, int, float, bool, list, dict))}
                }
                for node, attrs in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    **{k: v for k, v in attrs.items() if isinstance(v, (str, int, float, bool))}
                }
                for u, v, attrs in self.graph.edges(data=True)
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(hierarchy_data, f, indent=2)
    
    def visualize_hierarchy(self, output_path: str = "hierarchy.png"):
        """Create visual representation of hierarchy"""
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(20, 15))
        
        # Layout
        pos = nx.spring_layout(self.graph, k=3, iterations=50)
        
        # Draw nodes by type
        node_colors = {
            "root": "red",
            "category": "orange",
            "entity": "lightblue"
        }
        
        for node_type, color in node_colors.items():
            nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == node_type]
            nx.draw_networkx_nodes(self.graph, pos, nodelist=nodes, node_color=color, node_size=500)
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, pos, alpha=0.5)
        
        # Labels
        labels = {n: d.get("name", n)[:20] for n, d in self.graph.nodes(data=True)}
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=8)
        
        plt.title("Entity Hierarchy Visualization")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        
        logger.info(f"Hierarchy visualization saved to {output_path}")