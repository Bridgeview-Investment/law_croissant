# RegGenome Entity Mapper - Usage Guide

## Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **RegGenome API Key** - Contact product@reg-genome.com for access
3. **Git** for cloning the repository

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/reggenome-entity-mapper.git
cd reggenome-entity-mapper

# Make run script executable
chmod +x run.sh

# Set up environment (creates venv and installs dependencies)
./run.sh
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your RegGenome API key:
```
REGGENOME_API_KEY=your_api_key_here
```

## Running the System

### 1. Full Processing Pipeline

Process all documents for the default initiatives:

```bash
./run.sh process
```

Or with custom initiatives:

```bash
python main.py --initiatives "US - Investment Advisers Act (1940)" "EU - UCITS Directives"
```

### 2. Demo Mode (Limited Documents)

For testing with a smaller dataset:

```bash
./run.sh demo
```

### 3. Interactive Dashboard

Launch the Streamlit dashboard to explore results:

```bash
./run.sh dashboard
```

## Command Line Options

### Main Script Options

```bash
python main.py [OPTIONS]

Options:
  --initiatives LIST    Initiative names to process (space-separated)
  --limit INT          Limit number of documents to process
  --api-key STR        RegGenome API key (overrides environment)
```

### Examples

```bash
# Process specific initiatives with limit
python main.py --initiatives "US - Investment Company Act, 1940" --limit 50

# Use different API key
python main.py --api-key "your_key_here"

# Process UK regulations only
python main.py --initiatives "UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations, 2011 - 2016"
```

## Understanding the Outputs

The system generates several output files in the `outputs/YYYYMMDD_HHMMSS/` directory:

### 1. `entities.csv`
Hierarchical table of extracted entities:
- `entity_id`: Unique identifier
- `entity_name`: Name of the entity
- `entity_type`: Type (ORGANIZATION, PRODUCT, ACTIVITY, etc.)
- `category`: Category within type
- `parent_entity`: Parent in hierarchy
- `confidence`: Extraction confidence (0-1)

### 2. `relevance.json` / `relevance.csv`
Entity-document relevance predictions:
- `document_id`: Document identifier
- `level`: "document" or "section"
- `entity`: Entity name
- `confidence`: Relevance confidence (0-1)

### 3. `definitions.json`
Extracted definitions:
- `term`: Defined term
- `definition`: Definition text
- `document_id`: Source document
- `section_id`: Source section
- `confidence`: Extraction confidence
- `type`: Definition type (formal, contextual, etc.)

### 4. `entity_definitions.json`
Links between entities and their definitions

### 5. `hierarchy.png`
Visual representation of entity hierarchy

### 6. `summary_report.json`
Processing summary and statistics

## Configuration Options

### Environment Variables

Set these in your `.env` file:

```env
# API Configuration
REGGENOME_API_KEY=your_api_key
REGGENOME_API_URL=https://api.reggenome.com/api/v1

# Processing Configuration
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=60
CACHE_ENABLED=true
CACHE_DIR=./data/cache

# Model Configuration
USE_GPU=true
MODEL_BATCH_SIZE=32
CONFIDENCE_THRESHOLD=0.7

# Output Configuration
OUTPUT_DIR=./outputs
GENERATE_VISUALIZATIONS=true
EXPORT_FORMAT=json,csv,html
```

### Advanced Configuration

#### Entity Extraction Tuning

Modify confidence thresholds in `src/extractors/entity_extractor.py`:

```python
# Adjust confidence thresholds for different extraction methods
entities.append(Entity(
    confidence=0.95,  # Increase for higher precision
    ...
))
```

#### Relevance Prediction Tuning

Adjust the relevance threshold in `src/classifiers/relevance_predictor.py`:

```python
self.threshold = 0.5  # Lower = more inclusive, Higher = more precise
```

## Dashboard Features

The interactive dashboard provides:

1. **Overview Tab**: Summary statistics and visualizations
2. **Entities Tab**: Searchable entity table with filters
3. **Definitions Tab**: Browse extracted definitions
4. **Relevance Tab**: Entity-document relevance analysis
5. **Hierarchy Tab**: Interactive hierarchy exploration

### Dashboard Usage

1. Start the dashboard: `./run.sh dashboard`
2. Open browser to `http://localhost:8501`
3. Use the sidebar to select analysis runs and apply filters
4. Explore different tabs for various views of the data

## Troubleshooting

### Common Issues

#### 1. API Authentication Errors
```
Error: RegGenome API key not provided
```
**Solution**: Ensure `REGGENOME_API_KEY` is set in `.env` file

#### 2. Memory Issues with Large Document Sets
```
MemoryError: Unable to allocate array
```
**Solution**: Use `--limit` parameter to process fewer documents:
```bash
python main.py --limit 100
```

#### 3. Model Download Issues
```
Error downloading spaCy model
```
**Solution**: Manually download the model:
```bash
python -m spacy download en_core_web_sm
```

#### 4. GPU Memory Issues
```
CUDA out of memory
```
**Solution**: Set `USE_GPU=false` in `.env` file

### Performance Optimization

#### For Large Document Sets

1. **Increase concurrency** (if API allows):
```env
MAX_CONCURRENT_REQUESTS=20
```

2. **Enable caching**:
```env
CACHE_ENABLED=true
```

3. **Use GPU acceleration**:
```env
USE_GPU=true
```

#### For Limited Resources

1. **Reduce batch size**:
```env
MODEL_BATCH_SIZE=16
```

2. **Increase confidence threshold**:
```env
CONFIDENCE_THRESHOLD=0.8
```

3. **Process in batches**:
```bash
python main.py --limit 50
```

## Integration with Other Tools

### Jupyter Notebooks

Example notebook usage:

```python
import sys
sys.path.append('./src')

from api.client import RegGenomeClient
from extractors.entity_extractor import EntityExtractor

# Initialize components
extractor = EntityExtractor()

# Process your own documents
entities = extractor.extract_entities("Your regulatory text here...")
```

### API Integration

Use the client independently:

```python
import asyncio
from api.client import RegGenomeClient

async def fetch_documents():
    async with RegGenomeClient("your_api_key") as client:
        documents = await client.get_documents(
            initiatives=[1, 2, 3],
            page_size=50
        )
        return documents

documents = asyncio.run(fetch_documents())
```

## Support

For technical issues:
1. Check the troubleshooting section above
2. Review log files in `logs/` directory
3. Create an issue on GitHub with error details

For RegGenome API issues:
- Contact: product@reg-genome.com