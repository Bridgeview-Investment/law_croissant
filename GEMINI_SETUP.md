# 🤖 Google Gemini 2.5 Pro Integration Setup

This guide explains how to enhance your RegGenome Deep Research System with Google Gemini 2.5 Pro for improved accuracy in entity extraction and document analysis.

## 🚀 Why Use Gemini 2.5 Pro?

Gemini 2.5 Pro provides several advantages for regulatory document analysis:

- **Enhanced Financial Context Understanding**: Better recognition of financial terms and concepts
- **Improved Entity Classification**: More accurate categorization of entities, activities, and products  
- **Advanced Semantic Analysis**: Better understanding of regulatory language and relationships
- **Definition Extraction**: Enhanced ability to identify formal definitions in legal text

## 📋 Setup Instructions

### Step 1: Install Dependencies

```bash
# Install Gemini-specific dependencies
pip install -r requirements_gemini.txt

# Or install individually
pip install google-generativeai>=0.3.0
```

### Step 2: Get Your Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key" 
4. Copy your API key

### Step 3: Configure API Key

Choose one of these options:

#### Option A: Environment Variable (Recommended)
```bash
export GEMINI_API_KEY="your_api_key_here"
```

#### Option B: Key File
```bash
echo "your_api_key_here" > gemini_key.txt
```

### Step 4: Verify Setup

```bash
# Test the Gemini integration
python reggenome_gemini.py setup
```

## 🎯 Usage

### Basic Usage
```bash
# Run with Gemini enhancement
python reggenome_gemini.py "What are UCITS fund management requirements?"
```

### Advanced Usage
```bash
# Specify output directory and format
python reggenome_gemini.py "Investment adviser compliance rules" \
    --output-dir gemini_results \
    --format both
```

### Programmatic Usage
```python
from src.config import Config
from src.gemini_orchestrator import GeminiUnifiedInterface

# Initialize with Gemini enhancement
config = Config()
interface = GeminiUnifiedInterface(config)

# Run enhanced research
results = await interface.run_all_tasks_with_gemini(query)
```

## 🔧 Configuration Options

### Gemini Model Settings

You can customize Gemini behavior by modifying `src/gemini_client.py`:

```python
@dataclass
class GeminiConfig:
    api_key: str
    model_name: str = "gemini-2.0-flash-exp"  # Model to use
    temperature: float = 0.1  # Lower = more focused, Higher = more creative
    max_output_tokens: int = 8192  # Maximum response length
```

### Rate Limiting

The system includes built-in rate limiting to respect API quotas:
- Batch processing: 5 documents at a time
- Delays between batches: 1 second
- Error handling with retries

## 📊 Enhanced Outputs

With Gemini integration, you get:

### Enhanced Entity Extraction
- Better recognition of financial entities in context
- Improved classification accuracy
- More detailed entity descriptions

### Improved Deliverables
All three RegGenome deliverables benefit from Gemini enhancement:

1. **Entity Taxonomy**: More accurate entity relationships and classifications
2. **Relevance Predictions**: Better document-entity relevance scoring
3. **Entity Definitions**: Enhanced definition extraction from legal text

### Additional Metadata
Enhanced results include Gemini-specific metadata:

```json
{
  "ai_enhancement": {
    "model": "Google Gemini 2.5 Pro",
    "enhanced_tasks": ["Task 1: Entity Extraction"],
    "enhancement_benefits": [
      "Improved financial context understanding",
      "Better entity classification accuracy", 
      "Enhanced semantic analysis"
    ]
  }
}
```

## 🔍 Comparison: Standard vs Gemini-Enhanced

| Feature | Standard System | Gemini-Enhanced |
|---------|----------------|-----------------|
| Entity Recognition | Pattern-based | AI context-aware |
| Financial Terms | Basic matching | Deep understanding |
| Definition Extraction | Regex patterns | Semantic analysis |
| Accuracy | Good | Excellent |
| Processing Speed | Fast | Moderate (API calls) |
| API Cost | Free | Pay-per-use |

## ⚡ Performance Tips

### Optimize API Usage
1. **Batch Processing**: System automatically batches documents to minimize API calls
2. **Caching**: Results are cached to avoid repeated API calls for same content
3. **Text Limiting**: Long documents are truncated to stay within API limits

### Monitor Usage
```bash
# Check API usage in Google Cloud Console
# Monitor quotas and billing

# Use environment variable to track costs
export GEMINI_DEBUG=true  # Enables detailed logging
```

## 🛠 Troubleshooting

### Common Issues

#### API Key Not Found
```
❌ ERROR: Gemini API key not found!
```
**Solution**: Verify your API key is set correctly using one of the setup methods above.

#### Rate Limit Exceeded
```
❌ Error: Rate limit exceeded
```
**Solution**: The system has built-in retry logic. If this persists, check your API quota in Google Cloud Console.

#### Import Error
```
❌ Google Generative AI library not found!
```
**Solution**: Install required dependencies:
```bash
pip install google-generativeai
```

#### Invalid API Key
```
❌ Error: Invalid API key
```
**Solution**: Verify your API key is correct and has proper permissions.

### Debug Mode

Enable detailed logging:
```bash
export GEMINI_DEBUG=true
python reggenome_gemini.py "your query"
```

## 💰 Cost Considerations

### Gemini API Pricing
- Pay-per-request model
- Costs vary by input/output token count
- Current pricing available at [Google AI Pricing](https://ai.google.dev/pricing)

### Cost Optimization
1. **Document Limiting**: System automatically limits text length per API call
2. **Batch Processing**: Reduces total API calls
3. **Caching**: Avoids duplicate processing
4. **Selective Enhancement**: Only critical extractions use Gemini

### Estimated Costs
For a typical research query processing 100 documents:
- Approximate API calls: 20-30
- Estimated cost: $0.10-$0.50 (varies by content length)

## 🔄 Fallback Behavior

If Gemini is unavailable, the system gracefully falls back to:
1. Standard pattern-based extraction
2. Regular RegGenome processing
3. All existing functionality preserved

## 🚀 Advanced Features

### Custom Prompts
Modify prompts in `src/gemini_client.py` to customize AI behavior for your specific use case.

### Model Selection
Choose different Gemini models based on your needs:
- `gemini-2.0-flash-exp`: Latest and most capable
- `gemini-1.5-pro`: Stable production version
- `gemini-1.5-flash`: Faster, lower cost option

### Integration with Other Models
The architecture supports adding other AI models alongside Gemini for hybrid processing.

## 📞 Support

For issues specific to Gemini integration:
1. Check this setup guide
2. Review error messages and logs
3. Verify API key and quotas
4. Test with simpler queries first

For general RegGenome system issues, refer to the main documentation.

---

✅ **You're now ready to use Gemini 2.5 Pro enhanced RegGenome research!**

Run: `python reggenome_gemini.py "your research query"` to get started.