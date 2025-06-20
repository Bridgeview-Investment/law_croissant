# RegGenome Entity Mapper - Architecture

## System Overview

The RegGenome Entity Mapper is a comprehensive AI-powered solution designed to extract, classify, and map regulatory entities from financial regulatory documents. The system addresses the RegGenome challenge requirements through a multi-stage pipeline that processes documents from the RegGenome API.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RegGenome     │    │   Document      │    │   Entity        │
│   API Client    │───▶│   Processing    │───▶│   Extraction    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Reporting &   │◀───│   Relevance     │◀───│   Hierarchical  │
│   Visualization │    │   Prediction    │    │   Organization  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Definition    │
                       │   Extraction    │
                       └─────────────────┘
```

## Core Components

### 1. API Client Layer (`src/api/`)

**Purpose**: Interface with RegGenome Helios API

**Key Files**:
- `client.py`: Async HTTP client with rate limiting and caching
- `exceptions.py`: Custom exception handling

**Features**:
- Async/await support for concurrent requests
- Automatic retry logic with exponential backoff
- Request rate limiting to respect API constraints
- Response caching for improved performance
- Comprehensive error handling

**Design Patterns**:
- Context manager for resource management
- Decorator pattern for retry logic
- Strategy pattern for different request types

### 2. Entity Extraction Layer (`src/extractors/`)

**Purpose**: Extract and identify regulatory entities from document text

**Key Files**:
- `entity_extractor.py`: General entity extraction using NLP
- `financial_entities.py`: Specialized financial regulatory entity extraction
- `patterns.py`: Regex pattern definitions

**Methods**:
1. **Named Entity Recognition (NER)**:
   - SpaCy models for general entity recognition
   - Transformer-based models (BERT) for advanced recognition
   - Custom regulatory entity patterns

2. **Pattern-Based Extraction**:
   - Regex patterns for financial terms
   - Context-aware entity disambiguation
   - Industry-specific terminology recognition

3. **Multi-Model Ensemble**:
   - Combines multiple extraction methods
   - Confidence scoring and merging
   - Deduplication and normalization

**Entity Types Extracted**:
- Organizations (Investment Companies, Banks, Regulators)
- Products (Securities, Derivatives, Funds)
- Activities (Investment Services, Fund Management)
- Regulations (Directives, Acts, Rules)

### 3. Hierarchical Organization (`src/hierarchical/`)

**Purpose**: Build structured hierarchies and taxonomies

**Key Files**:
- `hierarchy_builder.py`: Graph-based hierarchy construction
- `entity_classifier.py`: Entity classification and categorization

**Approach**:
1. **Graph Construction**:
   - NetworkX directed graphs for entity relationships
   - Industry taxonomy integration (ISO10962, CDM, ISDA)
   - Automatic parent-child relationship inference

2. **Taxonomy Mapping**:
   - Integration with standard financial taxonomies
   - Custom regulatory classification schemes
   - Multi-level hierarchical structures

3. **Similarity Analysis**:
   - TF-IDF vectorization for entity comparison
   - Cosine similarity for relationship inference
   - Clustering for automatic categorization

### 4. Relevance Prediction (`src/classifiers/`)

**Purpose**: Predict entity relevance to documents and sections

**Key Files**:
- `relevance_predictor.py`: Multi-level relevance prediction
- `document_classifier.py`: Document-level classification

**Machine Learning Pipeline**:
1. **Feature Engineering**:
   - Sentence embeddings using transformer models
   - TF-IDF features for traditional ML models
   - Context-aware feature extraction

2. **Multi-Label Classification**:
   - Neural network architecture for entity prediction
   - Binary relevance for each entity type
   - Confidence scoring for predictions

3. **Training Strategy**:
   - Active learning from RegGenome metadata
   - Transfer learning from pre-trained models
   - Cross-validation for model evaluation

**Prediction Levels**:
- Document-level: Overall document relevance
- Section-level: Granular section-specific relevance
- Confidence scores: Probabilistic relevance assessment

### 5. Definition Extraction (`src/definitions/`)

**Purpose**: Extract and link entity definitions

**Key Files**:
- `definition_extractor.py`: Pattern and NLP-based definition extraction
- `definition_linker.py`: Cross-document definition linking

**Extraction Methods**:
1. **Pattern-Based Extraction**:
   - Formal definition patterns ("X means Y")
   - Parenthetical definitions
   - Definition section parsing

2. **NLP-Based Extraction**:
   - Dependency parsing for definition structures
   - Question-answering models for specific terms
   - Context-aware definition boundary detection

3. **Cross-Document Linking**:
   - Reference resolution across documents
   - Upstream legislation tracking
   - Definition consistency checking

## Data Flow

### 1. Initialization Phase
```python
# API client setup
client = RegGenomeClient(api_key)

# Component initialization
extractor = EntityExtractor()
hierarchy_builder = HierarchyBuilder()
relevance_predictor = RelevancePredictor()
definition_extractor = DefinitionExtractor()
```

### 2. Document Retrieval Phase
```python
# Fetch documents for specific initiatives
documents = await client.fetch_all_documents_for_initiatives([
    "US - Investment Advisers Act (1940)",
    "EU - UCITS Directives"
])
```

### 3. Entity Extraction Phase
```python
for document in documents:
    # General entity extraction
    entities = extractor.extract_from_document(document)
    
    # Financial entity extraction
    fin_entities = financial_extractor.extract_financial_entities(
        document_text
    )
    
    # Merge and deduplicate
    all_entities.extend(merge_entities(entities, fin_entities))
```

### 4. Hierarchy Building Phase
```python
# Build entity relationships
hierarchy = hierarchy_builder.build_entity_hierarchy(entities)

# Generate hierarchy table
entity_table = hierarchy_builder.get_entity_hierarchy_table()
```

### 5. Relevance Prediction Phase
```python
# Predict entity relevance
predictions = relevance_predictor.predict_relevance(
    documents, entity_names
)
```

### 6. Definition Extraction Phase
```python
for document in documents:
    # Extract definitions
    definitions = definition_extractor.extract_definitions(
        document_text, document_id
    )
    
    # Link to entities
    entity_definitions = definition_extractor.link_definitions_to_entities(
        entities, definitions
    )
```

### 7. Output Generation Phase
```python
# Export results
export_entity_table(entities)
export_relevance_predictions(predictions)
export_definitions(definitions)
export_hierarchy_visualization(hierarchy)
```

## Design Principles

### 1. Modularity
- Each component has a single responsibility
- Clear interfaces between components
- Easy to test and maintain individual modules

### 2. Scalability
- Async processing for I/O operations
- Concurrent API requests with rate limiting
- Caching for expensive operations
- Batch processing for large datasets

### 3. Extensibility
- Plugin architecture for new extractors
- Configurable parameters via environment variables
- Support for custom taxonomies and patterns

### 4. Robustness
- Comprehensive error handling
- Graceful degradation when components fail
- Input validation and sanitization
- Logging and monitoring throughout

### 5. Performance
- Efficient algorithms for large-scale processing
- Memory-conscious data structures
- GPU acceleration where applicable
- Intelligent caching strategies

## Technology Stack

### Core Libraries
- **Python 3.8+**: Main programming language
- **AsyncIO**: Asynchronous programming
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing

### NLP and ML
- **spaCy**: Industrial-strength NLP
- **Transformers**: State-of-the-art transformer models
- **PyTorch**: Deep learning framework
- **scikit-learn**: Traditional machine learning

### Data and Networking
- **httpx**: Async HTTP client
- **NetworkX**: Graph analysis
- **SQLite**: Local caching (optional)
- **JSON/CSV**: Data interchange formats

### Visualization
- **Plotly**: Interactive visualizations
- **Matplotlib**: Static plots
- **Streamlit**: Web dashboard
- **Graphviz**: Graph visualization

## Configuration Management

### Environment-Based Configuration
```env
# API Configuration
REGGENOME_API_KEY=xxx
MAX_CONCURRENT_REQUESTS=10

# Model Configuration
USE_GPU=true
CONFIDENCE_THRESHOLD=0.7

# Output Configuration
OUTPUT_DIR=./outputs
EXPORT_FORMAT=json,csv
```

### Runtime Configuration
- Command-line arguments for execution parameters
- Dynamic configuration loading
- Override mechanisms for different environments

## Error Handling Strategy

### 1. API Errors
- Network timeouts: Automatic retry with backoff
- Authentication failures: Clear error messages
- Rate limiting: Respect API limits with queuing

### 2. Processing Errors
- Malformed documents: Skip and log
- Model loading failures: Graceful fallback
- Memory issues: Batch processing adjustment

### 3. Output Errors
- File system issues: Alternative output locations
- Serialization errors: Format fallbacks
- Visualization failures: Text-based alternatives

## Performance Considerations

### 1. Memory Management
- Streaming processing for large documents
- Generator patterns for data iteration
- Explicit garbage collection in long-running processes

### 2. Computational Efficiency
- Vectorized operations with NumPy
- Batch processing for model inference
- Parallel processing where thread-safe

### 3. I/O Optimization
- Async API requests
- Compression for large data transfers
- Local caching for repeated operations

## Security Considerations

### 1. API Security
- Secure storage of API keys
- TLS for all API communications
- Input validation and sanitization

### 2. Data Privacy
- No storage of sensitive document content
- Anonymization of personal information
- Compliance with data protection regulations

### 3. Code Security
- Input validation for all user inputs
- Safe deserialization practices
- Dependency vulnerability monitoring

## Future Enhancements

### 1. Advanced ML Models
- Fine-tuned domain-specific transformers
- Graph neural networks for entity relationships
- Active learning for continuous improvement

### 2. Real-time Processing
- Streaming data processing
- Event-driven architecture
- Real-time dashboards

### 3. Extended Integrations
- Additional regulatory databases
- Enterprise compliance tools
- Cloud deployment options

This architecture provides a solid foundation for regulatory entity extraction while maintaining flexibility for future enhancements and adaptations to different regulatory domains.