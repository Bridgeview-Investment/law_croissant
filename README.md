# Deep Research Multi-Agent System for RegGenome

A sophisticated multi-agent system designed to extract regulated activities, entities, and products from regulatory documents using the RegGenome API.

## Overview

This system implements a hierarchical multi-agent architecture inspired by leading open-source deep research implementations. It's specifically designed for Task 1 of the RegGenome challenge: creating a deduplicated table of regulated activities, entities, and products from regulatory documents.

## Architecture

The system uses a supervisor-researcher pattern with specialized agents:

```
DeepResearchOrchestrator (Supervisor)
    ├── EntityExtractionAgent
    ├── ActivityExtractionAgent  
    ├── ProductExtractionAgent
    └── DeduplicationAgent
```

### Key Components

1. **DeepResearchOrchestrator**: Coordinates the research process, manages document fetching, and orchestrates parallel agent execution.

2. **EntityExtractionAgent**: Specializes in identifying regulated entities such as:
   - Investment advisers
   - Investment companies
   - UCITS funds
   - Management companies
   - Depositaries

3. **ActivityExtractionAgent**: Extracts regulated activities including:
   - Asset management
   - Investment advice
   - Portfolio management
   - Custody services
   - Distribution and marketing

4. **ProductExtractionAgent**: Identifies financial products like:
   - Mutual funds
   - ETFs
   - UCITS funds
   - Hedge funds
   - Money market funds

5. **DeduplicationAgent**: Consolidates results by:
   - Merging duplicate entries
   - Normalizing names
   - Combining metadata from multiple sources
   - Calculating confidence scores

## Features

- **Parallel Processing**: Agents work concurrently for faster extraction
- **Smart Deduplication**: Advanced similarity matching to eliminate redundancy
- **Confidence Scoring**: Each extracted item includes a confidence score
- **Hierarchical Output**: Results organized by type with detailed metadata
- **Flexible Configuration**: Easily adjust API parameters and extraction settings

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Place your RegGenome JWT token in `key.txt`

## Usage

### Interactive Mode (Default)

```bash
python main.py
```

This launches an interactive terminal interface where you can:
- Enter research queries directly
- View example queries and help
- Check configuration and available initiatives
- Review history of previous research
- Get instant results with summaries

### Batch Mode

```bash
# Run with default query
python main.py --batch

# Run with custom query
python main.py --batch "What are the compliance requirements for UCITS funds?"

# Or simply pass the query as arguments
python main.py What are the main regulated entities in UCITS directives?
```

### Interactive CLI Features

The interactive interface provides several commands:

- `help` - Show available commands and usage
- `examples` - Display example research queries
- `config` - View current configuration settings
- `initiatives` - List regulatory initiatives in scope
- `history` - Show recent research queries and results
- `clear` - Clear the terminal screen
- `exit/quit` - Exit the program

Simply type your research query to start the analysis!

### Example Queries

```
What are the main regulated entities in UCITS directives?
How does a UK fund conduct CDD & KYC with EU and UK regulators?
Fund distribution and marketing activities
Investment adviser compliance requirements
Depositary requirements for UCITS funds
Cross-border fund distribution requirements post-Brexit
```

### Output Format

Results are saved in two formats:

1. **JSON** (`task1_hierarchical_table_[timestamp].json`) - Structured data with full details
2. **Text Summary** (`task1_summary_[timestamp].txt`) - Human-readable report

The interactive mode also displays:
- Real-time progress updates
- Summary statistics
- Top findings from each category
- Confidence scores for extracted items

## Configuration

Edit `src/config.py` to customize:

- API endpoints
- Page size and limits
- Concurrent agent count
- Initiative filters

## Extending the System

The modular architecture makes it easy to:

1. Add new agent types
2. Implement additional extraction patterns
3. Integrate with LLMs for enhanced extraction
4. Add new output formats

## Performance Considerations

- Documents are processed in batches to manage memory
- Agents run in parallel using asyncio and thread pools
- Deduplication uses efficient similarity algorithms
- API calls include retry logic for reliability

## Next Steps

This system provides the foundation for Tasks 2 and 3:
- Task 2: Predict document relevance using extracted data
- Task 3: Link to formal definitions in source documents

The extracted entities, activities, and products serve as the knowledge base for these advanced tasks.