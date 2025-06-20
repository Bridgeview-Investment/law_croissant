# RegGenome Deep Research Multi-agent System

A comprehensive AI-powered system for analyzing regulatory documents and extracting regulated activities, entities, and products. Built using the [LangChain open_deep_research](https://github.com/langchain-ai/open_deep_research) architecture and specifically designed for the RegGenome challenge.

## 🎯 Objectives

This system addresses the **RegGenome Challenge** by accomplishing three key tasks:

1. **📋 Task 1**: Create a table of regulated activities, entities, and products discussed in regulatory documents (free of redundancy and repetition)
2. **🎯 Task 2**: Predict document relevance to regulated activities, entities, and products at both document and sub-document level
3. **🔗 Task 3**: Link each regulated item to documents where they are formally defined with full definition text

## 🏗️ Architecture

The system uses a **multi-agent architecture** with specialized agents for different extraction tasks:

```
┌─────────────────────────────────────────────────────────────────┐
│                Deep Research Orchestrator                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Entity        │  │   Activity      │  │   Product       │  │
│  │ Extraction      │  │ Extraction      │  │ Extraction      │  │
│  │   Agent         │  │   Agent         │  │   Agent         │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                     │                     │         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Entity        │  │   Activity      │  │   Product       │  │
│  │   Merger        │  │   Merger        │  │   Merger        │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                RegGenome API Client                             │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key or Anthropic API key
- RegGenome API key (optional - can run with mock data)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd law_croissant
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
# Copy the template
cp config.env.template .env

# Edit the configuration file
nano .env
```

Required environment variables:
```env
# AI Model Configuration (at least one required)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# RegGenome API Configuration (optional for demo)
REGGENOME_API_KEY=your_reggenome_api_key_here
```

### Running the System

#### 🧪 Demo Mode (No API Keys Required)
```bash
python main.py --mock
```

#### 🔑 With Real RegGenome API
```bash
python main.py
```

#### 📁 Custom Output Files
```bash
python main.py --output my_results.json --table-output task1_deliverable.json
```

#### 🔍 Custom Research Query
```bash
python main.py --query "UCITS directive regulations and compliance requirements"
```

#### 🛠️ Debug Mode
```bash
python main.py --log-level DEBUG --log-file debug.log
```

## 📊 Output Files

The system generates multiple output files:

### 1. Hierarchical Table (`regulatory_hierarchy_table.json`) - **Task 1 Deliverable**
```json
{
  "regulated_entities": {
    "investment_adviser": [
      {
        "id": "entity_abc123",
        "name": "Investment Adviser",
        "description": "Person who provides investment advice for compensation",
        "jurisdictions": ["US"],
        "regulatory_framework": ["Investment Advisers Act of 1940"],
        "source_documents": ["doc_123"],
        "confidence_score": 0.95
      }
    ]
  },
  "regulated_activities": {
    "investment_advisory": [...]
  },
  "regulated_products": {
    "mutual_fund": [...]
  }
}
```

### 2. Complete Taxonomy (`regulatory_taxonomy_YYYYMMDD_HHMMSS.json`)
Contains the full research results including document relevance mappings and metadata.

## 🧠 AI Models Supported

The system supports multiple AI providers:

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo
- **Anthropic**: Claude-3.5-Sonnet, Claude-3-Haiku

Configure different models for different tasks:
```env
RESEARCH_MODEL=gpt-4o          # For complex analysis
EXTRACTION_MODEL=gpt-4o-mini   # For structured extraction
CLASSIFICATION_MODEL=gpt-4o-mini # For relevance classification
```

## 📚 Regulatory Document Coverage

The system processes documents from these **Legislative Initiatives**:

- **US - Investment Advisers Act (1940)**
- **US - Investment Company Act (1940)**
- **EU - UCITS Directives**
- **UK - The Undertakings for Collective Investment in Transferable Securities (UCITS) Regulations, 2011-2016**

## 🎛️ Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REGGENOME_API_KEY` | RegGenome API access key | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `ANTHROPIC_API_KEY` | Anthropic API key | None |
| `DEFAULT_LLM_MODEL` | Default model to use | `gpt-4o-mini` |
| `MAX_DOCUMENTS_PER_BATCH` | Documents per API batch | `50` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Command Line Options

```bash
python main.py --help
```

## 🏗️ System Components

### Core Modules

- **`config.py`**: Configuration management
- **`models.py`**: Data models for entities, activities, products
- **`api_client.py`**: RegGenome API integration
- **`llm_utils.py`**: AI model utilities and prompts
- **`deep_research_orchestrator.py`**: Main workflow orchestrator

### Extraction Agents

- **`entity_extraction_agent.py`**: Identifies regulated entities (investment advisers, banks, etc.)
- **`activity_extraction_agent.py`**: Extracts regulated activities (advisory services, trading, etc.)
- **`product_extraction_agent.py`**: Finds regulated products (mutual funds, ETFs, etc.)

## 📈 Performance Features

- **Parallel Processing**: Extraction agents run concurrently for speed
- **Intelligent Deduplication**: AI-powered merging of similar items
- **Confidence Scoring**: Each extraction includes confidence assessment
- **Error Handling**: Robust error recovery and logging
- **Rate Limiting**: Respectful API usage with automatic retries

## 🔧 Advanced Usage

### Custom Configuration File
```bash
python main.py --config my_custom.env
```

### Programmatic Usage
```python
import asyncio
from src.deep_research_orchestrator import run_deep_research

async def main():
    taxonomy = await run_deep_research(
        query="Extract UCITS-related regulations",
        use_mock_api=False,
        save_results=True
    )
    print(f"Found {len(taxonomy.entities)} entities")

asyncio.run(main())
```

### Extending the System

Add new entity types in `src/models.py`:
```python
class EntityType(str, Enum):
    # Existing types...
    CRYPTOCURRENCY_EXCHANGE = "cryptocurrency_exchange"
    ROBO_ADVISOR = "robo_advisor"
```

## 🧪 Testing

Run with mock data for testing:
```bash
python main.py --mock --log-level DEBUG
```

The mock client provides sample regulatory documents to demonstrate the system's capabilities without requiring API access.

## 🐛 Troubleshooting

### Common Issues

1. **"No API key provided"**: Set up your `.env` file with API keys
2. **Rate limiting errors**: The system handles this automatically with exponential backoff
3. **Memory issues**: Reduce `MAX_DOCUMENTS_PER_BATCH` in configuration
4. **Model errors**: Try switching to a different AI model in configuration

### Debug Mode
```bash
python main.py --log-level DEBUG --log-file debug.log --mock
```

## 📄 License

This project is built for the RegGenome Challenge and uses the MIT license framework from the [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) project.

## 🤝 Contributing

This system is designed for the RegGenome challenge. For improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For questions about the RegGenome Challenge or this implementation:

- Check the debug logs with `--log-level DEBUG`
- Review the task description in `task_description.md`
- Examine the configuration in `config.env.template`

---

**Built with ❤️ for regulatory compliance automation using AI-powered deep research agents.** 