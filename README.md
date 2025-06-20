# RegGenome Entity Mapping Solution

An advanced AI-powered solution for identifying and mapping regulated entities, products, and activities from regulatory documents using the RegGenome API.

## Challenge Overview

This solution addresses the RegGenome challenge by:
1. Extracting regulated activities, entities, and products from regulatory documents
2. Predicting relevance at document and sub-document levels
3. Linking entities to their formal definitions across documents

## Key Features

- **Intelligent Entity Extraction**: Uses advanced NLP techniques to identify regulated entities
- **Hierarchical Classification**: Organizes entities into meaningful hierarchical structures
- **Multi-level Relevance Prediction**: Predicts applicability at both document and clause levels
- **Definition Linking**: Automatically finds and links formal definitions
- **Real-time API Integration**: Efficiently processes RegGenome structured data
- **Visualization Dashboard**: Interactive interface for exploring results

## Technical Approach

### 1. Entity Recognition
- Custom NER models trained on financial regulatory text
- Pattern matching for regulatory-specific terminology
- Context-aware entity disambiguation

### 2. Hierarchical Organization
- Graph-based entity relationship modeling
- Automatic taxonomy generation
- Integration with industry standards (ISO10962, CDM, ISDA)

### 3. Relevance Prediction
- Transformer-based relevance scoring
- Multi-label classification for entity-document mapping
- Confidence scoring for predictions

### 4. Definition Extraction
- Cross-document reference resolution
- Definition boundary detection
- Upstream legislation tracking

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/reggenome-entity-mapper.git
cd reggenome-entity-mapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up API credentials
export REGGENOME_API_KEY="your_api_key"
```

## Quick Start

```python
from reggenome_mapper import EntityMapper

# Initialize mapper
mapper = EntityMapper(api_key="your_api_key")

# Process documents for specified initiatives
results = mapper.process_initiatives([
    "US - Investment Advisers Act (1940)",
    "EU - UCITS Directives"
])

# Generate reports
mapper.generate_reports(results, output_dir="./outputs")
```

## Project Structure

```
reggenome-entity-mapper/
├── src/
│   ├── api/              # RegGenome API client
│   ├── extractors/       # Entity extraction modules
│   ├── classifiers/      # Relevance prediction models
│   ├── hierarchical/     # Hierarchy building logic
│   ├── definitions/      # Definition extraction
│   └── visualization/    # Dashboard and reporting
├── tests/                # Unit and integration tests
├── data/                 # Sample data and caches
├── docs/                 # Documentation
└── notebooks/            # Jupyter notebooks for analysis
```

## Results Format

The solution produces three main outputs:

### 1. Entity Table (entities.csv)
```csv
entity_id,entity_name,entity_type,parent_entity,confidence
E001,Investment Company,Organization,,0.95
E002,Registered Investment Adviser,Organization,E001,0.92
```

### 2. Relevance Predictions (relevance.json)
```json
{
  "document_id": "abc123",
  "relevant_entities": ["E001", "E002"],
  "sub_documents": [
    {
      "section": "2.1",
      "relevant_entities": ["E001"],
      "confidence": 0.87
    }
  ]
}
```

### 3. Definition Links (definitions.json)
```json
{
  "entity_id": "E001",
  "definitions": [
    {
      "document_id": "xyz789",
      "section": "1.2",
      "text": "Investment Company means...",
      "confidence": 0.94
    }
  ]
}
```

## Competition Strategy

### Performance Optimizations
- Concurrent API requests with rate limiting
- Intelligent caching for processed documents
- Batch processing for large document sets

### Accuracy Enhancements
- Ensemble of multiple extraction methods
- Active learning from RegGenome metadata
- Cross-validation with industry taxonomies

### Unique Features
- Real-time processing pipeline
- Explainable AI for transparency
- Integration with existing compliance tools

## Team

Developed for Hack the Law Cambridge 2024

## License

MIT License