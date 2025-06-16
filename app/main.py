"""
main.py

Flask app entry point for RegHealth Navigator backend.
"""
import sys
import os
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException
import yaml
from core.search import ChatSearchService
from config import config
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app() -> Flask:
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Initialize Flask app
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, origins=config.cors_origins)
    
    # Initialize services
    chat_service = ChatSearchService(
        openai_api_key=api_key,
        faiss_index_path=config.faiss_index_path,
        metadata_path=config.faiss_metadata_path
    )
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app, chat_service)
    
    return app

def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error: HTTPException) -> tuple[Dict[str, str], int]:
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error: HTTPException) -> tuple[Dict[str, str], int]:
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(BadRequest)
    def handle_bad_request(error: BadRequest) -> tuple[Dict[str, str], int]:
        return jsonify({"error": str(error)}), 400

def register_routes(app: Flask, chat_service: ChatSearchService) -> None:
    """
    Register routes for the Flask application.
    
    Args:
        app: Flask application instance
        chat_service: ChatSearchService instance
    """
    def validate_json_request(required_fields: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Validate JSON request and required fields.
        
        Args:
            required_fields: List of required field names
            
        Returns:
            Dict[str, Any]: Validated request data
            
        Raises:
            BadRequest: If request is not JSON or missing required fields
        """
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

    @app.route("/api/chat", methods=["POST"])
    def chat() -> tuple[Dict[str, Any], int]:
        """
        Chat endpoint for querying the RAG system.
        
        Request body:
            {
                "query": str  # The user's question
            }
            
        Returns:
            {
                "response": str  # The system's response
            }
        """
        try:
            data = validate_json_request(required_fields=["query"])
            query = data.get("query")
            response = chat_service.ask_query(query)
            return jsonify({"response": response})
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 400

    @app.route("/api/simple-chat", methods=["POST"])
    def simple_chat() -> tuple[Dict[str, str], int]:
        """
        Simple test endpoint.
        
        Request body:
            {
                "message": str  # Any message
            }
            
        Returns:
            {
                "response": str  # Always returns "hello world!"
            }
        """
        try:
            data = validate_json_request(required_fields=["message"])
            return jsonify({"response": "hello world!"})
        except Exception as e:
            logger.error(f"Error in simple-chat endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 400

def main() -> None:
    """Main entry point for the Flask application."""
    app = create_app()
    logger.info("Starting Flask app...")
    app.run(
        host=config.api_host,
        port=config.api_port,
        debug=config.debug
    )

if __name__ == "__main__":
    main()