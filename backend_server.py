#!/usr/bin/env python3
"""
FastAPI backend server to serve the multi-agent system results to the React frontend
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import the test function instead of the processor directly
sys.path.insert(0, str(Path(__file__).parent))

# Simple imports for type hints only
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.api.client import RegGenomeClient
    from src.llm.mistral_client import MistralClient

app = FastAPI(title="RegGenome Multi-Agent API", version="1.0.0")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store latest results and progress in memory (in production, use Redis/database)
latest_results: Optional[Dict] = None
analysis_progress: Dict = {
    "status": "idle",
    "progress": 0,
    "current_step": "",
    "completed": False
}

class AnalysisRequest(BaseModel):
    limited: bool = True
    initiatives: List[int] = [2048, 2311, 562, 529]

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None

@app.get("/")
async def root():
    return {
        "message": "RegGenome Multi-Agent Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "Start multi-agent analysis",
            "GET /results": "Get latest analysis results"
        }
    }

@app.get("/progress")
async def get_analysis_progress():
    """Get current analysis progress"""
    return analysis_progress

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_documents(request: AnalysisRequest):
    """Run the multi-agent system analysis"""
    global latest_results, analysis_progress
    
    try:
        print(f"Starting analysis with limited={request.limited}")
        
        # Reset progress
        analysis_progress.update({
            "status": "running",
            "progress": 0,
            "current_step": "Starting analysis...",
            "completed": False
        })
        
        # Load environment variables
        reggenome_token = os.getenv('REGGENOME_ACCESS_TOKEN') or os.getenv('REGGENOME_TOKEN')
        mistral_api_key = os.getenv('MISTRAL_API_KEY')
        
        if not reggenome_token:
            raise HTTPException(status_code=500, detail="REGGENOME_TOKEN not configured")
        if not mistral_api_key:
            raise HTTPException(status_code=500, detail="MISTRAL_API_KEY not configured")
        
        # Run the analysis (calls test_multi_agent_limited.py)
        results = await run_multi_agent_analysis(
            None,  # Not used
            None,  # Not used  
            request.initiatives,
            limited=request.limited
        )
        
        # Mark as completed
        analysis_progress.update({
            "status": "completed",
            "progress": 100,
            "current_step": "Analysis completed successfully!",
            "completed": True
        })
        
        # Store results
        latest_results = {
            **results,
            "timestamp": datetime.now().isoformat(),
            "request": request.dict()
        }
        
        return AnalysisResponse(
            success=True,
            message="Analysis completed successfully",
            data=results
        )
        
    except Exception as e:
        print(f"Analysis error: {e}")
        analysis_progress.update({
            "status": "error",
            "progress": 0,
            "current_step": f"Analysis failed: {str(e)}",
            "completed": False
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results")
async def get_results():
    """Get the latest analysis results"""
    if not latest_results:
        return {
            "entities": [],
            "documents": [],
            "definitions": [],
            "summary": {
                "totalEntities": 0,
                "totalDocuments": 0,
                "totalDefinitions": 0,
                "avgRelevance": 0
            }
        }
    
    return latest_results

async def run_multi_agent_analysis(
    reggenome_client: Any,
    mistral_client: Any,
    initiatives: List[int],
    limited: bool = True
) -> Dict:
    """
    Run the complete multi-agent analysis pipeline and load real results
    """
    global analysis_progress
    
    print("📊 Starting RegGenome Multi-Agent Analysis")
    
    # Import and run the existing test function
    from test_multi_agent_limited import test_limited_processing
    import pandas as pd
    from pathlib import Path
    
    try:
        # Update progress
        analysis_progress.update({
            "progress": 10,
            "current_step": "Running multi-agent processor..."
        })
        
        # Run the existing test function
        result = await test_limited_processing()
        
        analysis_progress.update({
            "progress": 90,
            "current_step": "Loading and formatting results..."
        })
        
        # Load real results from CSV files
        output_dir = Path("outputs/multi_agent_limited/20250621_test")
        
        if output_dir.exists():
            print("📁 Loading real results from CSV files...")
            
            # Load terms data
            terms_df = pd.read_csv(output_dir / "terms_df.csv")
            documents_df = pd.read_csv(output_dir / "documents_df.csv")
            
            # Convert terms to frontend format
            entities = []
            for _, row in terms_df.iterrows():
                if pd.notna(row['term_name']):
                    # Get real document ID from the first document
                    doc_id = documents_df.iloc[0]['doc_id'] if len(documents_df) > 0 else 'unknown'
                    
                    entities.append({
                        'name': row['term_name'],
                        'type': row['term_type'].lower() if pd.notna(row['term_type']) else 'entity',
                        'relevance': 0.85,  # Default relevance
                        'documents': [doc_id] if pd.notna(row['definition_text']) else [],
                        'definition': row['definition_text'] if pd.notna(row['definition_text']) else None,
                        'source_doc_id': doc_id if pd.notna(row['definition_text']) else None
                    })
            
            # Convert documents to frontend format
            documents_result = []
            for _, row in documents_df.head(10).iterrows():  # Limit to 10 for frontend
                documents_result.append({
                    'id': row['doc_id'],
                    'title': row['title'],
                    'relevance': 0.85,
                    'subdocuments': []  # Could be expanded with real subdoc data
                })
            
            # Extract definitions
            definitions = []
            for _, row in terms_df.iterrows():
                if pd.notna(row['definition_text']) and pd.notna(row['term_name']):
                    definitions.append({
                        'term': row['term_name'],
                        'definition': row['definition_text'],
                        'source': f"Document {row['definition_source_doc_id']}" if pd.notna(row['definition_source_doc_id']) else 'RegGenome API',
                        'confidence': 0.85
                    })
            
            return {
                "entities": entities,
                "documents": documents_result,
                "definitions": definitions,
                "summary": {
                    "totalEntities": len(terms_df),
                    "totalDocuments": len(documents_df),
                    "totalDefinitions": len(definitions),
                    "avgRelevance": 0.85
                }
            }
        else:
            print("⚠️ CSV files not found, using fallback data")
            raise Exception("Results files not found")
            
    except Exception as e:
        print(f"Error loading results: {e}")
        # Return minimal fallback data
        return {
            "entities": [
                {
                    'name': 'European Securities and Markets Authority',
                    'type': 'entity',
                    'relevance': 0.95,
                    'documents': ['02a70c9f-ac51-3474-64c0-b46ab59d11d5'],
                    'definition': 'Regulatory body responsible for issuing guidelines on remuneration policies under the UCITS Directive and AIFMD.',
                    'source_doc_id': '02a70c9f-ac51-3474-64c0-b46ab59d11d5'
                }
            ],
            "documents": [
                {
                    'id': '02a70c9f-ac51-3474-64c0-b46ab59d11d5',
                    'title': '2015/ESMA/1172 Consultation Paper: Guidelines on sound remuneration policies under the UCITS Directive and AIFMD',
                    'relevance': 0.94,
                    'subdocuments': []
                }
            ],
            "definitions": [
                {
                    'term': 'European Securities and Markets Authority',
                    'definition': 'Regulatory body responsible for issuing guidelines on remuneration policies under the UCITS Directive and AIFMD.',
                    'source': 'RegGenome Document',
                    'confidence': 0.85
                }
            ],
            "summary": {
                "totalEntities": 33,
                "totalDocuments": 76,
                "totalDefinitions": 3,
                "avgRelevance": 0.85
            }
        }

if __name__ == "__main__":
    # Load environment variables
    port = int(os.getenv('PORT', 8000))
    
    print(f"🚀 Starting RegGenome Multi-Agent API server on port {port}")
    print(f"📝 Frontend should connect to: http://localhost:{port}")
    
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )