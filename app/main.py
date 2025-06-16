"""
main.py

Flask app entry point for RegHealth Navigator backend.
"""
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
import yaml
from core.search import ChatSearchService
from config import config
from dotenv import load_dotenv

# from core.xml_partition import XMLPartitioner
# from core.xml_chunker import XMLChunker
# from core.embedding import EmbeddingManager
# from core.llm import LLMManager
# from core.chat_engine import ChatEngine
# import json

# 加载 .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# 只初始化一次
chat_service = ChatSearchService(
    openai_api_key=api_key,
    faiss_index_path=config.faiss_index_path,
    metadata_path=config.faiss_metadata_path
)

app = Flask(__name__)

# CORS setup for development
CORS(app, origins=config.cors_origins)  # Update this for production

# Initialize your components (you may need to adjust based on your actual implementation)
# partitioner = XMLPartitioner()
# chunker = XMLChunker()
# embedding_manager = EmbeddingManager()
# llm_manager = LLMManager()

def validate_json_request(required_fields=None):
    """Helper function to validate JSON requests"""
    if not request.is_json:
        raise BadRequest("Request must be JSON")

    data = request.get_json()
    if not data:
        raise BadRequest("Request body cannot be empty")

    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

    return data

@app.route("/api/upload", methods=["POST"])
def upload_document():
    """Upload and process a new XML document"""
    # try:
    #     if 'file' not in request.files:
    #         raise BadRequest("No file provided")
    #
    #     file = request.files['file']
    #     if file.filename == '':
    #         raise BadRequest("No file selected")
    #
    #     content = file.read()
    #     sections = partitioner.partition(content)
    #     return jsonify({"message": "Document uploaded and partitioned", "sections": sections})
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 400

@app.route("/api/sections/<section_id>/process", methods=["POST"])
def process_section(section_id):
    """Process a specific section (chunk, embed, index)"""
    # try:
    #     chunks = chunker.chunk_section(section_id)
    #     embeddings = embedding_manager.embed_chunks(chunks)
    #     return jsonify({"message": "Section processed", "chunks": len(chunks)})
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 400

@app.route("/api/sections/<section_id>/summarize", methods=["POST"])
def summarize_section(section_id):
    """Generate summary for a section"""
    # try:
    #     summary = llm_manager.summarize_section(section_id)
    #     return jsonify({"summary": summary})
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 400

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat endpoint that demonstrates frontend-backend interaction.

    Request body should contain:
        {
            "section_id": "demo_section",
            "query": "What are the requirements?" (optional)
        }

    Returns:
        {
            "response": "Hello! You asked about section demo_section. Your query was: What are the requirements?"
        }
    """
    try:
        data = validate_json_request(required_fields=["query"])
        query = data.get("query")
        response = chat_service.ask_query(query)
        return jsonify({"response": response})
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/compare", methods=["POST"])
def compare_documents():
    """Compare two documents or specific sections"""
    # try:
    #     data = validate_json_request(required_fields=["doc1_id", "doc2_id"])
    #
    #     doc1_id = data["doc1_id"]
    #     doc2_id = data["doc2_id"]
    #     section_ids = data.get("section_ids")
    #
    #     comparison = llm_manager.compare_documents(doc1_id, doc2_id, section_ids)
    #     return jsonify({"comparison": comparison})
    # except BadRequest as e:
    #     return jsonify({"error": str(e)}), 400
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 400

@app.route("/api/simple-chat", methods=["POST"])
def simple_chat():
    """Simple chat endpoint that returns hello world"""
    try:
        data = validate_json_request(required_fields=["message"])
        return jsonify({"response": "hello world!"})
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# if __name__ == "__main__":
#     with open('../config.yml', 'r') as file:
#         config = yaml.safe_load(file)
#         API_KEY = config['OPENAI_API_KEY']  # Method 1

#     app.run(host="0.0.0.0", port=8000, debug=True)