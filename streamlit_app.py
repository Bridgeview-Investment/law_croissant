"""
RegGenome Entity Mapper - Interactive Dashboard
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from pathlib import Path
import json
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="RegGenome Entity Mapper",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #c9d3e0;
        padding: 10px;
        border-radius: 5px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🏛️ RegGenome Entity Mapper Dashboard")
st.markdown("### AI-Powered Regulatory Entity Extraction and Mapping")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    # Select output directory
    output_dir = Path("./outputs")
    if output_dir.exists():
        timestamps = [d.name for d in output_dir.iterdir() if d.is_dir()]
        timestamps.sort(reverse=True)
        
        if timestamps:
            selected_timestamp = st.selectbox(
                "Select Analysis Run",
                timestamps,
                format_func=lambda x: datetime.strptime(x, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            )
            
            results_dir = output_dir / selected_timestamp
        else:
            st.error("No analysis results found. Please run the main script first.")
            st.stop()
    else:
        st.error("Output directory not found. Please run the main script first.")
        st.stop()
    
    st.markdown("---")
    
    # Filters
    st.header("Filters")
    
    # Load entity data
    entity_df = pd.read_csv(results_dir / "entities.csv")
    
    # Entity type filter
    entity_types = entity_df['entity_type'].unique()
    selected_types = st.multiselect(
        "Entity Types",
        entity_types,
        default=entity_types
    )
    
    # Confidence threshold
    confidence_threshold = st.slider(
        "Minimum Confidence",
        0.0, 1.0, 0.7,
        step=0.05
    )

# Main content
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🔍 Entities",
    "📖 Definitions",
    "🎯 Relevance",
    "🌳 Hierarchy"
])

# Tab 1: Overview
with tab1:
    # Load summary report
    with open(results_dir / "summary_report.json", 'r') as f:
        summary = json.load(f)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Documents Processed",
            summary['summary']['documents_processed']
        )
    
    with col2:
        st.metric(
            "Entities Extracted",
            summary['summary']['entities_extracted']
        )
    
    with col3:
        st.metric(
            "Definitions Found",
            summary['summary']['definitions_found']
        )
    
    with col4:
        st.metric(
            "Entity Coverage",
            f"{summary['coverage']['entity_coverage']:.1%}"
        )
    
    st.markdown("---")
    
    # Entity breakdown chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Entity Type Distribution")
        
        breakdown_df = pd.DataFrame(
            list(summary['entity_breakdown'].items()),
            columns=['Entity Type', 'Count']
        )
        
        fig = px.pie(
            breakdown_df,
            values='Count',
            names='Entity Type',
            title="Distribution of Entity Types"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top Entities")
        
        top_entities_df = pd.DataFrame(summary['top_entities'])
        
        fig = px.bar(
            top_entities_df.head(10),
            x='occurrences',
            y='name',
            orientation='h',
            title="Most Frequently Occurring Entities",
            labels={'occurrences': 'Occurrences', 'name': 'Entity'}
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

# Tab 2: Entities
with tab2:
    st.header("Extracted Entities")
    
    # Filter entities
    filtered_df = entity_df[
        (entity_df['entity_type'].isin(selected_types)) &
        (entity_df['confidence'] >= confidence_threshold)
    ]
    
    # Search box
    search_term = st.text_input("Search entities", "")
    if search_term:
        filtered_df = filtered_df[
            filtered_df['entity_name'].str.contains(search_term, case=False, na=False)
        ]
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entities", len(filtered_df))
    with col2:
        st.metric("Unique Types", filtered_df['entity_type'].nunique())
    with col3:
        st.metric("Avg Confidence", f"{filtered_df['confidence'].mean():.3f}")
    
    # Entity table
    st.dataframe(
        filtered_df[['entity_name', 'entity_type', 'category', 'parent_entity', 'confidence']],
        use_container_width=True,
        height=500
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download Entities CSV",
        data=csv,
        file_name=f"entities_{selected_timestamp}.csv",
        mime="text/csv"
    )

# Tab 3: Definitions
with tab3:
    st.header("Extracted Definitions")
    
    # Load definitions
    with open(results_dir / "definitions.json", 'r') as f:
        definitions = json.load(f)
    
    # Convert to DataFrame
    def_df = pd.DataFrame(definitions)
    
    # Search box
    def_search = st.text_input("Search definitions", "", key="def_search")
    if def_search:
        mask = (
            def_df['term'].str.contains(def_search, case=False, na=False) |
            def_df['definition'].str.contains(def_search, case=False, na=False)
        )
        def_df = def_df[mask]
    
    # Display count
    st.metric("Total Definitions", len(def_df))
    
    # Display definitions
    for idx, row in def_df.iterrows():
        with st.expander(f"**{row['term']}** (Confidence: {row['confidence']:.2f})"):
            st.write(f"**Definition:** {row['definition']}")
            st.write(f"**Document:** {row['document_id']}")
            st.write(f"**Section:** {row['section_id']}")
            st.write(f"**Type:** {row['type']}")

# Tab 4: Relevance
with tab4:
    st.header("Entity-Document Relevance")
    
    # Load relevance predictions
    with open(results_dir / "relevance.json", 'r') as f:
        relevance_data = json.load(f)
    
    # Convert to DataFrame
    rel_df = pd.DataFrame(relevance_data)
    
    # Filter by confidence
    rel_df = rel_df[rel_df['confidence'] >= confidence_threshold]
    
    # Group by document
    doc_summary = rel_df[rel_df['level'] == 'document'].groupby('document_id').agg({
        'entity': 'count',
        'confidence': 'mean'
    }).reset_index()
    doc_summary.columns = ['Document ID', 'Entity Count', 'Avg Confidence']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Document-Level Relevance")
        
        fig = px.scatter(
            doc_summary,
            x='Entity Count',
            y='Avg Confidence',
            hover_data=['Document ID'],
            title="Documents by Entity Count and Confidence"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Entity Distribution")
        
        entity_counts = rel_df['entity'].value_counts().head(20)
        
        fig = px.bar(
            x=entity_counts.values,
            y=entity_counts.index,
            orientation='h',
            title="Most Relevant Entities Across Documents",
            labels={'x': 'Document Count', 'y': 'Entity'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed view
    st.subheader("Detailed Relevance Predictions")
    
    selected_doc = st.selectbox(
        "Select Document",
        rel_df['document_id'].unique()
    )
    
    if selected_doc:
        doc_rel = rel_df[rel_df['document_id'] == selected_doc]
        
        # Document level entities
        doc_level = doc_rel[doc_rel['level'] == 'document']
        if not doc_level.empty:
            st.write("**Document Level Entities:**")
            for _, row in doc_level.iterrows():
                st.write(f"- {row['entity']} (confidence: {row['confidence']:.2f})")
        
        # Section level entities
        section_level = doc_rel[doc_rel['level'] == 'section']
        if not section_level.empty:
            st.write("**Section Level Entities:**")
            sections = section_level['section_id'].unique()
            for section in sections:
                st.write(f"\n*Section {section}:*")
                section_ents = section_level[section_level['section_id'] == section]
                for _, row in section_ents.iterrows():
                    st.write(f"- {row['entity']} (confidence: {row['confidence']:.2f})")

# Tab 5: Hierarchy
with tab5:
    st.header("Entity Hierarchy Visualization")
    
    # Display hierarchy image if exists
    hierarchy_img = results_dir / "hierarchy.png"
    if hierarchy_img.exists():
        st.image(str(hierarchy_img), caption="Entity Hierarchy Graph")
    
    # Hierarchical view
    st.subheader("Hierarchical Structure")
    
    # Filter for hierarchical entities
    hier_df = entity_df[entity_df['parent_entity'].notna()]
    
    # Create tree view
    def create_tree(df, parent=None, level=0):
        if parent is None:
            # Root level - entities without parents in filtered set
            roots = df[~df['entity_id'].isin(df['parent_entity'].dropna())]
            for _, row in roots.iterrows():
                st.write("  " * level + f"📁 **{row['entity_name']}** ({row['entity_type']})")
                create_tree(df, row['entity_id'], level + 1)
        else:
            children = df[df['parent_entity'] == parent]
            for _, row in children.iterrows():
                st.write("  " * level + f"📄 {row['entity_name']} ({row['entity_type']})")
                create_tree(df, row['entity_id'], level + 1)
    
    # Display tree
    with st.container():
        create_tree(filtered_df)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>RegGenome Entity Mapper | Hack the Law Cambridge 2024</p>
    </div>
    """,
    unsafe_allow_html=True
)