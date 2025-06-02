"""
main.py

FastAPI app entry point for RegHealth Navigator backend.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from core.xml_partition import XMLPartitioner
from core.xml_chunker import XMLChunker
from core.embedding import EmbeddingManager
from core.llm import LLMManager
from core.mindmap_builder import MindMapBuilder
from core.chat_engine import ChatEngine
from pydantic import BaseModel
import json

app = FastAPI(title="RegHealth Navigator API")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
partitioner = XMLPartitioner()
chunker = XMLChunker()
embedding_manager = EmbeddingManager()
llm_manager = LLMManager()
mindmap_builder = MindMapBuilder()
chat_engine = ChatEngine()

class SectionRequest(BaseModel):
    section_id: str
    query: Optional[str] = None

class ComparisonRequest(BaseModel):
    doc1_id: str
    doc2_id: str
    section_ids: Optional[List[str]] = None

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a new XML document"""
    try:
        content = await file.read()
        sections = partitioner.partition(content)
        return {"message": "Document uploaded and partitioned", "sections": sections}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sections/{section_id}/process")
async def process_section(section_id: str):
    """Process a specific section (chunk, embed, index)"""
    try:
        chunks = chunker.chunk_section(section_id)
        embeddings = embedding_manager.embed_chunks(chunks)
        return {"message": "Section processed", "chunks": len(chunks)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sections/{section_id}/summarize")
async def summarize_section(section_id: str):
    """Generate summary for a section"""
    try:
        summary = llm_manager.summarize_section(section_id)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sections/{section_id}/mindmap")
async def generate_mindmap(section_id: str):
    """Generate mindmap for a section"""
    try:
        mindmap = mindmap_builder.build(section_id)
        return {"mindmap": mindmap}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat(request: SectionRequest):
    """Chat with a specific section"""
    try:
        response = chat_engine.chat(request.section_id, request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/compare")
async def compare_documents(request: ComparisonRequest):
    """Compare two documents or specific sections"""
    try:
        comparison = llm_manager.compare_documents(
            request.doc1_id, 
            request.doc2_id,
            request.section_ids
        )
        return {"comparison": comparison}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 