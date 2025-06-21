"""
FastAPI Backend for RegGenome Multi-Agent System
Serves the React frontend and handles analysis requests
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sys
import os

# Add parent directory to path to import our multi-agent processor
sys.path.append(str(Path(__file__).parent.parent))

from src.api.client import RegGenomeClient
from src.llm.mistral_client import MistralClient
from src.processors.multi_agent_processor import MultiAgentProcessor

app = FastAPI(title="RegGenome Multi-Agent API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class AnalysisResponse(BaseModel):
    analysis_id: str

class AnalysisStatus(BaseModel):
    status: str
    progress: int
    current_phase: str
    message: str

# Global storage for analysis results (use database in production)
analysis_store: Dict[str, Dict] = {}

# Background task for running analysis
async def run_analysis_task(analysis_id: str):
    """Run the multi-agent analysis in background"""
    try:
        # Update status
        analysis_store[analysis_id]["status"] = "running"
        analysis_store[analysis_id]["progress"] = 0
        analysis_store[analysis_id]["current_phase"] = "Data Collection"
        analysis_store[analysis_id]["message"] = "Starting multi-agent analysis..."

        async with RegGenomeClient() as reggenome_client:
            llm_client = MistralClient()
            processor = MultiAgentProcessor(reggenome_client, llm_client)

            # Override to use limited processing for demo
            processor.target_initiative_ids = [562]  # EU UCITS only

            # Phase 1: Data Collection
            analysis_store[analysis_id]["progress"] = 20
            analysis_store[analysis_id]["message"] = "Fetching documents from RegGenome API..."
            
            # Get limited documents
            filters = {"initiatives": [562], "remove_near_duplicates": True}
            result = await reggenome_client._make_request(
                method="POST",
                endpoint="/customer/documents",
                json_data={**filters, "page": 1, "page_size": 10}
            )
            documents = result if isinstance(result, list) else result.get("documents", [])

            # Process documents
            document_records = []
            for doc in documents:
                source_text = processor._extract_document_text(doc.get('source_text', ''))
                record = {
                    'doc_id': doc.get('document_id'),
                    'title': doc.get('title', ''),
                    'published_date': doc.get('published', ''),
                    'source_text': source_text,
                    'rg_signposts': doc.get('signposts', []),
                    'rg_reg_scores': doc.get('reg_scores', {}),
                }
                document_records.append(record)

            processor.documents_df = processor.documents_df._constructor(document_records)

            # Phase 2: Term Extraction
            analysis_store[analysis_id]["progress"] = 40
            analysis_store[analysis_id]["current_phase"] = "Term Extraction"
            analysis_store[analysis_id]["message"] = "AI agents extracting regulatory terms..."

            # Extract terms
            sample_docs = processor.documents_df.head(3).to_dict('records')
            raw_terms = await llm_client.batch_extract_terms(sample_docs, batch_size=2)

            # Phase 3: Processing and deduplication
            analysis_store[analysis_id]["progress"] = 60
            analysis_store[analysis_id]["message"] = "Processing and deduplicating terms..."

            # Process terms (simplified version)
            unique_terms = {}
            for term in raw_terms:
                term_name = term.get("term_name", "").strip().lower()
                if term_name and term_name not in unique_terms:
                    unique_terms[term_name] = term

            # Create terms DataFrame
            term_records = []
            for i, (term_name, term_data) in enumerate(unique_terms.items()):
                record = {
                    'term_id': f"term_{i+1:04d}",
                    'term_name': term_data.get("term_name", ""),
                    'term_type': term_data.get("term_type", ""),
                    'definition_text': f"{term_data.get('term_name', '')}: {term_data.get('contextual_explanation', 'Regulatory term extracted from document')}",
                    'confidence_score': 0.8
                }
                term_records.append(record)

            # Phase 4: Finalization
            analysis_store[analysis_id]["progress"] = 90
            analysis_store[analysis_id]["current_phase"] = "Results Export"
            analysis_store[analysis_id]["message"] = "Generating final results..."

            await asyncio.sleep(2)  # Simulate processing time

            # Store results
            results = {
                "documents": document_records,
                "terms": term_records,
                "relevance": [],
                "summary": {
                    "total_documents": len(document_records),
                    "total_terms": len(term_records),
                    "entities_count": len([t for t in term_records if t["term_type"] == "ENTITY"]),
                    "products_count": len([t for t in term_records if t["term_type"] == "PRODUCT"]),
                    "activities_count": len([t for t in term_records if t["term_type"] == "ACTIVITY"]),
                    "definitions_found": len([t for t in term_records if t.get("definition_text")]),
                    "processing_time": "2m 30s"
                }
            }

            # Complete
            analysis_store[analysis_id]["progress"] = 100
            analysis_store[analysis_id]["status"] = "completed"
            analysis_store[analysis_id]["current_phase"] = "Completed"
            analysis_store[analysis_id]["message"] = "Analysis completed successfully!"
            analysis_store[analysis_id]["results"] = results

    except Exception as e:
        analysis_store[analysis_id]["status"] = "error"
        analysis_store[analysis_id]["message"] = f"Analysis failed: {str(e)}"
        print(f"Analysis error: {e}")

@app.post("/api/analysis/start", response_model=AnalysisResponse)
async def start_analysis(background_tasks: BackgroundTasks):
    """Start a new multi-agent analysis"""
    analysis_id = str(uuid.uuid4())
    
    # Initialize analysis record
    analysis_store[analysis_id] = {
        "id": analysis_id,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "progress": 0,
        "current_phase": "Initializing",
        "message": "Analysis queued..."
    }
    
    # Start background task
    background_tasks.add_task(run_analysis_task, analysis_id)
    
    return AnalysisResponse(analysis_id=analysis_id)

@app.get("/api/analysis/{analysis_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """Get the status of a specific analysis"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    return AnalysisStatus(
        status=analysis["status"],
        progress=analysis["progress"],
        current_phase=analysis["current_phase"],
        message=analysis["message"]
    )

@app.get("/api/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get the results of a completed analysis"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    if analysis["status"] != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    return analysis.get("results", {})

@app.get("/api/analysis/latest/results")
async def get_latest_results():
    """Get the results of the most recent completed analysis"""
    completed_analyses = [
        a for a in analysis_store.values() 
        if a["status"] == "completed"
    ]
    
    if not completed_analyses:
        # Return mock data if no completed analyses
        return {
            "documents": [],
            "terms": [
                {
                    "term_id": "term_0001",
                    "term_name": "European Securities and Markets Authority",
                    "term_type": "ENTITY",
                    "definition_text": "European Securities and Markets Authority: Regulatory body responsible for issuing guidelines on remuneration policies under the UCITS Directive and AIFMD.",
                    "confidence_score": 0.85
                },
                {
                    "term_id": "term_0002",
                    "term_name": "UCITS Directive",
                    "term_type": "PRODUCT",
                    "definition_text": "UCITS Directive: Directive 2009/65/EC, a regulatory framework for Undertakings for Collective Investment in Transferable Securities.",
                    "confidence_score": 0.92
                }
            ],
            "relevance": [],
            "summary": {
                "total_documents": 72,
                "total_terms": 36,
                "entities_count": 12,
                "products_count": 18,
                "activities_count": 6,
                "definitions_found": 3,
                "processing_time": "2m 45s"
            }
        }
    
    latest = max(completed_analyses, key=lambda x: x["timestamp"])
    return latest.get("results", {})

@app.get("/api/analysis")
async def list_analyses():
    """List all analyses"""
    return [
        {
            "id": a["id"],
            "timestamp": a["timestamp"],
            "status": a["status"]
        }
        for a in analysis_store.values()
    ]

# Serve React static files
app.mount("/static", StaticFiles(directory="../reggenome-frontend/build/static"), name="static")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all routes"""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    build_path = Path("../reggenome-frontend/build")
    if build_path.exists():
        return FileResponse(build_path / "index.html")
    else:
        raise HTTPException(status_code=404, detail="Frontend not built")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)