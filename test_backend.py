"""
Test backend API endpoints
"""
import os
import json
from typing import Dict, Any, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_summary() -> List[Dict[str, Any]]:
    """
    List all available documents for summary generation.
    
    Returns:
        List[Dict[str, Any]]: List of document information
    """
    documents = []
    data_dir = "data"
    
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
    Generate summary for a specific document.
    
    Args:
        doc_name: Name of the document (without .xml extension)
        
    Returns:
        Dict[str, Any]: Summary information in JSON format
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

def validate_json_request(required_fields=None):
    """
    Validate JSON request and required fields.
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

# Create Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

@app.route("/api/list-summary", methods=["GET"])
def api_list_summary():
    """
    List all available documents for summary generation.
    """
    try:
        documents = list_summary()
        return jsonify({"documents": documents})
    except Exception as e:
        logger.error(f"Error in list-summary endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route("/api/get-summary", methods=["POST"])
def api_get_summary():
    """
    Get summary for a specific document.
    """
    try:
        data = validate_json_request(required_fields=["doc_name"])
        doc_name = data.get("doc_name")
        summary = get_summary(doc_name)
        return jsonify({"summary": summary})
    except Exception as e:
        logger.error(f"Error in get-summary endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 400

@app.route("/api/test", methods=["GET"])
def test():
    """
    Test endpoint
    """
    return jsonify({"message": "Backend is running!"})

if __name__ == "__main__":
    print("Starting test backend server...")
    app.run(host="0.0.0.0", port=5000, debug=True) 