"""
main.py

FastAPI app entry point for RegHealth Navigator backend.
"""
from fastapi import FastAPI, UploadFile, File
from typing import List

app = FastAPI(title="RegHealth Navigator API")

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    """
    Upload an XML file to the server.
    """
    pass

@app.get("/files")
def list_files() -> List[str]:
    """
    List all available XML files.
    """
    pass

@app.post("/summary")
def generate_summary(file_id: str):
    """
    Generate a summary for the given XML file.
    """
    pass

@app.post("/mindmap")
def generate_mindmap(file_id: str):
    """
    Generate a mindmap for the given XML file.
    """
    pass

@app.post("/chat")
def chat_query(file_id: str, query: str):
    """
    Answer a chat query for the given XML file.
    """
    pass

@app.post("/compare")
def compare_files(file_ids: List[str], aspect: str):
    """
    Compare two or more XML files on a given aspect.
    """
    pass 