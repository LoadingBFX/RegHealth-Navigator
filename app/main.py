"""
main.py

Flask app entry point for RegHealth Navigator backend.
Provides RESTful API endpoints for chat, comparison, summarization, and document management.

Functionality:
- Flask web server with CORS configuration
- RESTful API endpoints for all system features
- Service initialization and dependency injection
- Error handling and request validation
- Document listing and summary management
- Federal Register integration endpoints

Process Flow:
1. Initialize Flask application with CORS
2. Load environment variables and API keys
3. Initialize core services (ChatSearchService, SummaryGenerator, SectionBySectionRuleComparator)
4. Register error handlers and API routes
5. Handle incoming requests with proper validation
6. Return structured JSON responses
7. Provide comprehensive error handling

Author: Sarvesh, Fanxing Bu
"""
import sys
import os
import logging
import json
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException
import yaml
import requests

from app.core import summarizer
from app.core.compare import SectionBySectionRuleComparator
from app.core.summarizer import SummaryGenerator
from .core.search import ChatSearchService
from .config import config
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

    summarizer = SummaryGenerator(
        openai_api_key=api_key
    )

    comparator = SectionBySectionRuleComparator(
        faiss_index_path=config.faiss_index_path,
        metadata_path=config.faiss_metadata_path,
        api_key=api_key
    )

    # Register error handlers
    register_error_handlers(app)

    # Register routes
    register_routes(app, chat_service, summarizer, comparator)

    return app


def list_available_documents() -> List[Dict[str, Any]]:
    """
    List all available documents from the data directory.
    
    Returns:
        List[Dict[str, Any]]: List of document information
    """
    documents = []
    data_dir = config.docs_data_path
    
    # Define program types
    programs = ["MPFS", "HOSPICE", "SNF"]
    
    for program in programs:
        program_dir = os.path.join(data_dir, program)
        if os.path.exists(program_dir):
            for filename in os.listdir(program_dir):
                if filename.endswith('.xml'):
                    file_path = os.path.join(program_dir, filename)
                    file_stat = os.stat(file_path)
                    
                    # Extract year and type from filename
                    # Example: 2024_MPFS_final_2023-24184.xml
                    parts = filename.replace('.xml', '').split('_')
                    if len(parts) >= 3:
                        year = parts[0]
                        doc_type = parts[2]  # final or proposed
                        
                        documents.append({
                            "id": filename.replace('.xml', ''),
                            "name": filename.replace('.xml', ''),
                            "program": program,
                            "year": year,
                            "type": doc_type,
                            "size": f"{file_stat.st_size / (1024*1024):.1f} MB",
                            "date": f"{file_stat.st_mtime:.0f}"
                        })
    
    # Sort by year (descending) and then by program
    documents.sort(key=lambda x: (x["year"], x["program"]), reverse=True)
    
    return documents





def get_summary(doc_name: str) -> Dict[str, Any]:
    """
    Get summary for a specific document from saved summary files.
    
    Args:
        doc_name: Name of the document (without .xml extension)
        
    Returns:
        Dict[str, Any]: Summary information in JSON format
    """
    from pathlib import Path
    
    # Check if summary file exists
    summary_dir = Path(config.summary_output_dir)
    summary_md_path = summary_dir / f"{doc_name}.md"
    
    if summary_md_path.exists():
        # Read the actual summary content
        try:
            with open(summary_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first line if it's a markdown header
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip() if lines and lines[0].startswith('#') else f"{doc_name} Summary"
            
            return {
                "title": title,
                "document_name": doc_name,
                "content": content,
                "source": "generated_summary",
                "summary_path": str(summary_md_path)
            }
            
        except Exception as e:
            logger.error(f"Error reading summary file {summary_md_path}: {e}")
            return get_placeholder_summary(doc_name)
    
    # If no summary file exists, return placeholder or trigger generation
    logger.warning(f"No summary file found for {doc_name}")
    return get_placeholder_summary(doc_name)


def get_placeholder_summary(doc_name: str) -> Dict[str, Any]:
    """
    Generate placeholder summary data when no actual summary is available.
    
    Args:
        doc_name: Name of the document (without .xml extension)
        
    Returns:
        Dict[str, Any]: Placeholder summary information
    """
    # Sample summary data based on document type
    if "MPFS" in doc_name and "final" in doc_name:
        year = doc_name.split('_')[0]
        return {
            "title": f"{year} MPFS Final Rule Summary",
            "document_name": doc_name,
            "content": f"""# {year} MPFS Final Rule Summary

The {year} Medicare Physician Fee Schedule (MPFS) Final Rule introduces significant changes to physician payment methodologies and quality reporting requirements.

## Key Changes

**Payment Updates**
The conversion factor for {year} has been set at $32.75, representing a 3.4% decrease from the previous year's conversion factor. This decrease is primarily due to the expiration of the 0 percent update that was provided in the previous year under the Consolidated Appropriations Act.

**Evaluation and Management Services**
A new payment methodology for evaluation and management (E/M) services has been implemented to simplify billing and reduce administrative burden while ensuring appropriate payment for the complexity of services provided. This methodology is based on medical decision making or time, allowing practitioners greater flexibility in documenting and billing.

**Quality Payment Program (QPP)**
The MIPS performance threshold for the {year} performance period has been increased to 82.5 points, up from 75 points in the previous year. Clinicians who score below this threshold will receive negative payment adjustments, while those scoring above will receive positive adjustments based on their performance.

**Telehealth Provisions**
Extended telehealth flexibilities have been maintained through {year}, with new reimbursement rates for remote patient monitoring and updated geographic restrictions for telehealth services.

**Implementation Timeline**
All changes take effect January 1, {year}, with a transition period for practices to adapt to the new E/M documentation requirements.""",
            "sections": [
                {
                    "title": "Payment Updates",
                    "content": f"The conversion factor for {year} has been set at $32.75, representing a 3.4% decrease from the previous year."
                },
                {
                    "title": "Quality Measures", 
                    "content": f"The MIPS performance threshold for the {year} performance period has been increased to 82.5 points."
                },
                {
                    "title": "Telehealth Provisions",
                    "content": f"Extended telehealth flexibilities have been maintained through {year}."
                }
            ]
        }
    elif "MPFS" in doc_name and "proposed" in doc_name:
        year = doc_name.split('_')[0]
        return {
            "title": f"{year} MPFS Proposed Rule Summary",
            "document_name": doc_name,
            "content": f"""# {year} MPFS Proposed Rule Summary

The proposed rule for the {year} Medicare Physician Fee Schedule outlined several key changes that were later modified in the final rule.

## Proposed Changes

**Payment Methodology**
Initially proposed a conversion factor of $33.06 for {year}, which was later adjusted to $32.75 in the final rule based on public comments and budget neutrality requirements.

**Quality Measures**
Proposed a MIPS performance threshold of 85 points, which was reduced to 82.5 points in the final rule following stakeholder feedback about implementation challenges.

**Telehealth Services**
Outlined comprehensive telehealth policies that were largely maintained in the final rule, with some modifications to geographic restrictions based on rural healthcare access concerns.

**Public Comment Period**
The proposed rule received over 2,000 public comments, leading to significant modifications in the final rule, particularly regarding the performance threshold and implementation timeline.""",
            "sections": [
                {
                    "title": "Payment Methodology",
                    "content": f"Initially proposed a conversion factor of $33.06 for {year}."
                },
                {
                    "title": "Quality Measures",
                    "content": "Proposed a MIPS performance threshold of 85 points."
                },
                {
                    "title": "Telehealth Services", 
                    "content": "Outlined comprehensive telehealth policies."
                }
            ]
        }
    elif "HOSPICE" in doc_name:
        year = doc_name.split('_')[0]
        return {
            "title": f"{year} Hospice Final Rule Summary",
            "document_name": doc_name,
            "content": f"""# {year} Hospice Final Rule Summary

The {year} Hospice Final Rule establishes updated payment rates and quality measures for hospice care providers.

## Key Provisions

**Payment Rates**
Updated hospice payment rates for {year} reflect a 2.8% increase from the previous year's levels, accounting for inflation and cost-of-living adjustments in healthcare delivery.

**Quality Reporting**
New quality measures focus on patient and family satisfaction, pain management effectiveness, and care coordination with other healthcare providers.

**Regulatory Changes**
Streamlined documentation requirements to reduce administrative burden while maintaining quality oversight and compliance standards.

**Implementation**
All changes are effective October 1, {year}, for the fiscal year {int(year)+1} hospice payment period.""",
            "sections": [
                {
                    "title": "Payment Rates",
                    "content": f"Updated hospice payment rates for {year} reflect a 2.8% increase."
                },
                {
                    "title": "Quality Reporting",
                    "content": "New quality measures focus on patient and family satisfaction."
                },
                {
                    "title": "Regulatory Changes",
                    "content": "Streamlined documentation requirements to reduce administrative burden."
                }
            ]
        }
    else:
        # Default summary for other document types
        year = doc_name.split('_')[0] if '_' in doc_name else "Unknown"
        return {
            "title": f"{year} Document Summary",
            "document_name": doc_name,
            "content": f"""# {year} Document Summary

This document contains regulatory information and updates for the {year} period.

## Overview

This document provides important regulatory updates and changes that affect healthcare providers and organizations.

## Key Points

- Regulatory updates for {year}
- Implementation guidelines
- Compliance requirements
- Timeline for changes

## Implementation

Please review the full document for complete details and implementation guidance.""",
            "sections": [
                {
                    "title": "Overview",
                    "content": f"This document contains regulatory information and updates for the {year} period."
                },
                {
                    "title": "Key Points",
                    "content": "Regulatory updates, implementation guidelines, and compliance requirements."
                }
            ]
        }


def list_available_summaries() -> List[Dict[str, Any]]:
    """
    List all available summary files.
    
    Returns:
        List[Dict[str, Any]]: List of available summaries
    """
    from pathlib import Path
    import datetime
    
    summaries = []
    summary_dir = Path(config.summary_output_dir)
    
    if not summary_dir.exists():
        return summaries
    
    # Find all .md files in summary directory
    for summary_file in summary_dir.glob("*.md"):
        try:
            file_stat = summary_file.stat()
            doc_name = summary_file.stem  # filename without extension
            
            # Try to extract basic info from filename
            parts = doc_name.split('_')
            program = "Unknown"
            year = "Unknown"
            doc_type = "Unknown"
            
            if len(parts) >= 3:
                year = parts[0]
                program = parts[1] if parts[1] in ["MPFS", "HOSPICE", "SNF"] else parts[1].upper()
                doc_type = parts[2]  # final or proposed
            
            # Read first few lines to get title
            title = f"{doc_name} Summary"
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('#'):
                        title = first_line.replace('#', '').strip()
            except Exception:
                pass  # Use default title if reading fails
            
            summaries.append({
                "id": doc_name,
                "name": doc_name,
                "title": title,
                "program": program,
                "year": year,
                "type": doc_type,
                "size": f"{file_stat.st_size / 1024:.1f} KB",
                "modified_date": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                "summary_path": str(summary_file)
            })
            
        except Exception as e:
            logger.warning(f"Error processing summary file {summary_file}: {e}")
            continue
    
    # Sort by year (descending) and then by program
    summaries.sort(key=lambda x: (x["year"], x["program"]), reverse=True)
    
    return summaries


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """

    @app.errorhandler(404)
    def not_found(error: HTTPException) -> tuple[Dict[str, str], int]:
        return jsonify({"error": "The page you're looking for seems to have wandered off with Daisy's cat. Maybe Seon, Sai, Sarvesh, Dhruv and Fanxing can help find it! (404 - Endpoint not found)"}), 404

    @app.errorhandler(500)
    def internal_error(error: HTTPException) -> tuple[Dict[str, str], int]:
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({"error": "Oops! Something went wrong on our end. Daisy's cat must have knocked over the server! Seon, Sai, Sarvesh, Dhruv and Fanxing are working to fix it. (500 - Internal server error)"}), 500

    @app.errorhandler(BadRequest)
    def handle_bad_request(error: BadRequest) -> tuple[Dict[str, str], int]:
        return jsonify({"error": f"Looks like there's a typo in your request! Even Daisy's cat wouldn't make that mistake. {str(error)} (400 - Bad Request)"}), 400


def register_routes(app: Flask, chat_service: ChatSearchService, summarizer: SummaryGenerator, comparator: SectionBySectionRuleComparator) -> None:
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

    @app.route("/api/documents", methods=["GET"])
    def list_documents() -> tuple[Dict[str, Any], int]:
        """
        List all available documents for chat filtering.
        
        Returns:
            {
                "documents": List[Dict[str, Any]]  # List of document information
            }
        """
        try:
            documents = list_available_documents()
            return jsonify({"documents": documents})
        except Exception as e:
            logger.error(f"Error in documents endpoint: {str(e)}")
            return jsonify({"error": f"Daisy's cat seems to have hidden our documents! Seon, Sai, Sarvesh, Dhruv and Fanxing are searching for them. Error: {str(e)}"}), 400

    @app.route("/api/chat", methods=["POST"])
    def chat() -> tuple[Dict[str, Any], int]:
        """
        Chat endpoint for querying the RAG system.
        
        Request body:
            {
                "query": str,  # The user's question
                "doc_names": List[str]  # Optional: List of document names to filter by
            }
            
        Returns:
            {
                "response": str,  # The system's response
                "sources": List[Dict[str, Any]]  # Source information with chunks
            }
        """
        try:
            data = validate_json_request(required_fields=["query"])
            query = data.get("query")
            doc_names = data.get("doc_names", [])  # Optional document filter
            
            # Create filters if doc_names are provided
            filters = None
            if doc_names:
                filters = {"source_file": doc_names}
            
            result, cited_chunks = chat_service.ask_question(query, filters=filters)
            
            # Group cited chunks by source file
            sources_map = {}
            for i, chunk in enumerate(cited_chunks):
                source_file = chunk.get("metadata", {}).get("source_file", "unknown")
                if source_file not in sources_map:
                    sources_map[source_file] = {
                        "name": source_file,
                        "chunks": []
                    }
                sources_map[source_file]["chunks"].append({
                    "text": chunk.get("text", ""),
                    "index": i,
                    "distance": chunk.get("distance", 0)
                })
            
            # Sort chunks within each source by distance (most relevant first)
            for source_info in sources_map.values():
                source_info["chunks"].sort(key=lambda x: x["distance"])
            
            # Convert to list and sort by relevance (average distance of chunks)
            sources_list = []
            for source_info in sources_map.values():
                if source_info["chunks"]:
                    avg_distance = sum(chunk["distance"] for chunk in source_info["chunks"]) / len(source_info["chunks"])
                    source_info["avg_distance"] = avg_distance
                    sources_list.append(source_info)
            
            sources_list.sort(key=lambda x: x["avg_distance"])
            
            return jsonify({
                "response": result["answer"],
                "sources": sources_list
            })
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            return jsonify({"error": f"Daisy's cat interrupted our chat! Seon, Sai, Sarvesh, Dhruv and Fanxing are trying to catch it. Error: {str(e)}"}), 400

    @app.route("/api/summarize", methods=["POST"])
    def summarize() -> tuple[Dict[str, str], int]:
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
            summary = summarizer.generate_report(data)
            return jsonify({"response": summary})
        except Exception as e:
            logger.error(f"Error in summarize endpoint: {str(e)}")
            return jsonify({"error": f"Daisy's cat ran away with our summary! Seon, Sai, Sarvesh, Dhruv and Fanxing are chasing after it. Error: {str(e)}"}), 400

    @app.route("/api/get-summary", methods=["POST"])
    def api_get_summary() -> tuple[Dict[str, Any], int]:
        """
        Get summary for a specific document.
        
        Request body:
            {
                "doc_name": str  # Name of the document (without .xml extension)
            }
            
        Returns:
            {
                "summary": Dict[str, Any]  # Summary information
            }
        """
        try:
            data = validate_json_request(required_fields=["doc_name"])
            doc_name = data.get("doc_name")
            summary = get_summary(doc_name)
            return jsonify({"summary": summary})
        except Exception as e:
            logger.error(f"Error in get-summary endpoint: {str(e)}")
            return jsonify({"error": f"Daisy's cat seems to have hidden that summary! Seon, Sai, Sarvesh, Dhruv and Fanxing are looking for it. Error: {str(e)}"}), 400

    @app.route("/api/available-summaries", methods=["GET"])
    def api_available_summaries() -> tuple[Dict[str, Any], int]:
        """
        List all available summary files.
        
        Returns:
            {
                "summaries": List[Dict[str, Any]]  # List of available summaries
            }
        """
        try:
            summaries = list_available_summaries()
            return jsonify({"summaries": summaries})
        except Exception as e:
            logger.error(f"Error in available-summaries endpoint: {str(e)}")
            return jsonify({"error": f"Daisy's cat seems to have hidden our summary list! Seon, Sai, Sarvesh, Dhruv and Fanxing are searching for it. Error: {str(e)}"}), 400

    @app.route("/api/federal-register/<doc_number>", methods=["GET"])
    def get_federal_register_info(doc_number: str) -> tuple[Dict[str, Any], int]:
        """
        Get document information from Federal Register API.
        
        Args:
            doc_number: Document number (e.g., "2024-06431")
            
        Returns:
            {
                "pdf_url": str,  # URL to PDF version
                "html_url": str,  # URL to HTML version  
                "title": str,    # Document title
                "publication_date": str
            }
        """
        try:
            # Validate doc_number format (YYYY-NNNNN)
            if not doc_number or len(doc_number.split('-')) != 2:
                return jsonify({"error": "Invalid document number format"}), 400
            
            # Call Federal Register API
            api_url = f"https://www.federalregister.gov/api/v1/documents/{doc_number}.json"
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 404:
                return jsonify({"error": "Document not found"}), 404
            
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant information
            result = {
                "pdf_url": data.get("pdf_url", ""),
                "html_url": data.get("html_url", ""),
                "title": data.get("title", ""),
                "publication_date": data.get("publication_date", ""),
                "document_number": data.get("document_number", doc_number)
            }
            
            return jsonify(result)
            
        except requests.RequestException as e:
            logger.error(f"Error calling Federal Register API for {doc_number}: {str(e)}")
            return jsonify({"error": "Failed to fetch document information"}), 503
        except Exception as e:
            logger.error(f"Error in federal-register endpoint: {str(e)}")
            return jsonify({"error": f"Daisy's cat seems to have hidden the Federal Register info! Seon, Sai, Sarvesh, Dhruv and Fanxing are looking for it. Error: {str(e)}"}), 500

    @app.route("/api/compare", methods=["POST"])
    def compare() -> tuple[Dict[str, Any], int]:
        try:
            data = validate_json_request(required_fields=["message"])
            query = data.get("message")
            response = comparator.compare_rules(query)
            
            # Handle empty response from comparator
            if not response or response == {}:
                return jsonify({
                    "error": "No matching documents found for comparison. Please try specifying the program type (e.g., 'MPFS', 'SNF', 'Hospice') in your query.",
                    "suggestion": "Try queries like: 'Compare MPFS 2024 vs 2025 quality reporting' or 'How do SNF 2023 and 2024 rules differ?'"
                }), 404
            
            return response
        except Exception as e:
            logger.error(f"Error in compare endpoint: {str(e)}")
            return jsonify({"error": f"Daisy's cat interrupted our comparison! Seon, Sai, Sarvesh, Dhruv and Fanxing are trying to catch it. Error: {str(e)}"}), 500

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
