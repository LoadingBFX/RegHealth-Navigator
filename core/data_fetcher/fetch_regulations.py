#!/usr/bin/env python3
import argparse
import logging
import time
import random
import requests
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import json
from lxml import etree

# Constants
BASE_URL = "https://www.federalregister.gov/api/v1"
SEARCH_URL = f"{BASE_URL}/documents.json"
DOCUMENT_URL = f"{BASE_URL}/documents/{{}}.json"

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def get_single_document(doc_number: str) -> Optional[Dict]:
    """Fetch a single document by its document number.
    
    Args:
        doc_number (str): The document number to fetch (e.g., "2024-06431")
        
    Returns:
        Optional[Dict]: Document data if successful, None if failed
        
    Example response:
        {
            "document_number": "2024-06431",
            "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
            "type": "Rule",
            "publication_date": "2024-03-28",
            "html_url": "https://www.federalregister.gov/documents/2024/03/28/2024-06431/...",
            "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2024-03-28/pdf/2024-06431.pdf",
            "full_text_xml_url": "https://www.federalregister.gov/documents/full_text/xml/2024/2024-06431.xml"
        }
    """
    url = DOCUMENT_URL.format(doc_number)
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching document {doc_number}: {str(e)}")
        return None

def get_latest_documents(days: int = 365) -> List[Dict]:
    """Fetch latest documents from Federal Register.
    
    Args:
        days (int): Number of days to look back (default: 365)
        
    Returns:
        List[Dict]: List of document data
        
    Example response:
        {
            "results": [
                {
                    "document_number": "2024-06431",
                    "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
                    "type": "Rule",
                    "publication_date": "2024-03-28",
                    "html_url": "https://www.federalregister.gov/documents/2024/03/28/2024-06431/...",
                    "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2024-03-28/pdf/2024-06431.pdf",
                    "full_text_xml_url": "https://www.federalregister.gov/documents/full_text/xml/2024/2024-06431.xml"
                },
                {
                    "document_number": "2024-06432",
                    "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update; Proposed Rule",
                    "type": "Proposed Rule",
                    "publication_date": "2024-03-28",
                    "html_url": "https://www.federalregister.gov/documents/2024/03/28/2024-06432/...",
                    "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2024-03-28/pdf/2024-06432.pdf",
                    "full_text_xml_url": "https://www.federalregister.gov/documents/full_text/xml/2024/2024-06432.xml"
                }
            ],
            "count": 2,
            "description": "Documents matching your search",
            "next_page_url": null
        }
    """
    all_docs = []
    page = 1
    
    while True:
        params = {
            "conditions[publication_date][gte]": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "conditions[type][]": ["RULE", "PRORULE"],
            "conditions[agencies][]": "centers-for-medicare-medicaid-services",
            "per_page": 100,
            "page": page
        }
        
        try:
            response = requests.get(SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("results"):
                break
                
            all_docs.extend(data["results"])
            page += 1
            
            # Add delay between pages
            time.sleep(random.uniform(1, 2))
            
        except requests.RequestException as e:
            logging.error(f"Error fetching page {page}: {str(e)}")
            break
            
    return all_docs

def is_valid_xml(filepath: Path) -> bool:
    """Check if a file is a valid XML file.
    
    Args:
        filepath (Path): Path to the XML file to validate
        
    Returns:
        bool: True if file is valid XML, False otherwise
        
    Example XML structure:
        <?xml version="1.0" encoding="UTF-8"?>
        <FRDOC>
            <PUBLISH>
                <PRDOCNO>2024-06431</PRDOCNO>
                <PUBDATE>2024-03-28</PUBDATE>
                <DOCTYPE>Rule</DOCTYPE>
                <TITLE>Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update</TITLE>
                <TEXT>
                    <PREAMB>
                        <AGENCY>Centers for Medicare &amp; Medicaid Services (CMS), HHS.</AGENCY>
                        <ACTION>Final rule.</ACTION>
                    </PREAMB>
                    <SUPLINF>
                        <HED>Supplementary Information:</HED>
                        <HD1>I. Executive Summary</HD1>
                        <P>...</P>
                    </SUPLINF>
                </TEXT>
            </PUBLISH>
        </FRDOC>
    """
    try:
        with open(filepath, 'rb') as f:
            etree.parse(f)
        return True
    except (etree.XMLSyntaxError, IOError):
        return False

def detect_program_type(doc: Dict) -> Tuple[bool, str]:
    """Detect program type from document title.
    
    Args:
        doc (Dict): Document data containing title and other metadata
        
    Returns:
        Tuple[bool, str]: (True if program type detected, program type name)
        
    Program Types:
        1. MPFS (Medicare Physician Fee Schedule)
           - Keywords: physician fee schedule, mpfs, pfs
           - Example: Medicare Physician Fee Schedule Update
        
        2. HOSPICE (Hospice Payment)
           - Keywords: hospice wage, hospice payment, hospice quality
           - Example: Hospice Wage Index Update
        
        3. SNF (Skilled Nursing Facility)
           - Keywords: skilled nursing facility, snf, nursing facility, consolidated billing
           - Example: Prospective Payment System and Consolidated Billing for Skilled Nursing Facilities
    
    Example:
        >>> doc = {
        ...     "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
        ...     "type": "Rule",
        ...     "document_number": "2024-06431"
        ... }
        >>> detect_program_type(doc)
        (True, "MPFS")
    """
    title = doc.get("title", "").lower()
    
    # MPFS (Medicare Physician Fee Schedule)
    if any(keyword in title for keyword in ["physician fee schedule", "mpfs", "pfs"]):
        return True, "MPFS"
    
    # HOSPICE (Hospice Payment)
    if any(keyword in title for keyword in ["hospice wage", "hospice payment", "hospice quality"]):
        return True, "HOSPICE"
    
    # SNF (Skilled Nursing Facility)
    if any(keyword in title for keyword in ["skilled nursing facility", "snf", "nursing facility", "consolidated billing"]):
        return True, "SNF"
    
    return False, ""

def download_xml(doc: Dict, save_dir: Path, logger: Optional[logging.Logger] = None) -> bool:
    """Download XML file for a document.
    
    Args:
        doc (Dict): Document data containing metadata
        save_dir (Path): Directory to save the XML file
        logger (Optional[logging.Logger]): Logger instance for logging
        
    Returns:
        bool: True if download successful, False otherwise
        
    File Naming Convention:
        YYYY_PROGRAM_TYPE_DOC_TYPE_DOC_NUMBER.xml
        
    Example:
        >>> doc = {
        ...     "document_number": "2024-06431",
        ...     "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
        ...     "type": "Rule",
        ...     "publication_date": "2024-03-28"
        ... }
        >>> download_xml(doc, Path("data"))
        True  # Creates data/MPFS/2024_MPFS_final_2024-06431.xml
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        doc_number = doc.get("document_number", "")
        publication_date = doc.get("publication_date", "")
        doc_type = doc.get("type", "")
        
        if not all([doc_number, publication_date, doc_type]):
            logger.error(f"Missing required document information: {doc}")
            return False
        
        # Get program type
        has_program, program_type = detect_program_type(doc)
        if not has_program:
            logger.error(f"Could not detect program type for document {doc_number}")
            return False
        
        # Create program type directory
        program_dir = save_dir / program_type
        program_dir.mkdir(parents=True, exist_ok=True)
        
        # Construct filename
        year = publication_date.split("-")[0]
        doc_type_suffix = "final" if doc_type == "Rule" else "proposed"
        filename = f"{year}_{program_type}_{doc_type_suffix}_{doc_number}.xml"
        filepath = program_dir / filename
        
        # Check if file already exists and is valid
        if filepath.exists() and is_valid_xml(filepath):
            logger.info(f"Already exists and valid: {filepath}")
            return True
        
        # Download XML
        xml_url = f"https://www.federalregister.gov/documents/full_text/xml/{year}/{doc_number}.xml"
        response = requests.get(xml_url)
        response.raise_for_status()
        
        # Save file
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        # Verify file
        if not is_valid_xml(filepath):
            logger.error(f"Downloaded file is not valid XML: {filepath}")
            filepath.unlink()
            return False
        
        logger.info(f"✅ Successfully downloaded: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading document {doc.get('document_number', '')}: {str(e)}")
        return False

def parse_args():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
        
    Command Line Arguments:
        --mode: Operation mode (single/latest)
        --doc-number: Document number to download
        --date: Publication date in YYYY-MM-DD format
        --days: Number of days to look back
        --output-dir: Output directory for downloaded files
        --verbose: Enable verbose logging
        
    Example:
        >>> parse_args()
        Namespace(
            mode='latest',
            doc_number=None,
            date=None,
            days=365,
            output_dir='data',
            verbose=False
        )
    """
    parser = argparse.ArgumentParser(description='Federal Register document fetcher')
    parser.add_argument('--mode', choices=['single', 'latest'], default='latest',
                      help='Operation mode: single (one document) or latest (fetch latest documents)')
    parser.add_argument('--doc-number', type=str,
                      help='Document number to download (e.g., 2024-06431)')
    parser.add_argument('--date', type=str,
                      help='Publication date in YYYY-MM-DD format')
    parser.add_argument('--days', type=int, default=365,
                      help='Number of days to look back (for latest mode)')
    parser.add_argument('--output-dir', type=str, default='data',
                      help='Output directory for downloaded files')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    return parser.parse_args()

def main():
    """Main function to fetch regulations.
    
    This function:
    1. Parses command line arguments
    2. Sets up logging
    3. Creates output directory
    4. Fetches and processes documents
    5. Downloads XML files
    6. Generates summary report
    
    Command Line Usage:
        # Fetch latest documents
        python fetch_regulations.py --mode latest --days 30
        
        # Download single document
        python fetch_regulations.py --mode single --doc-number 2024-06431
        
        # Enable verbose logging
        python fetch_regulations.py --mode latest --verbose
        
    Output:
        Creates a directory structure:
        data/
        ├── MPFS/
        │   ├── 2024_MPFS_final_2024-06431.xml
        │   └── 2024_MPFS_proposed_2024-06432.xml
        ├── HOSPICE/
        │   ├── 2024_HOSPICE_final_2024-06433.xml
        │   └── 2024_HOSPICE_proposed_2024-06434.xml
        └── SNF/
            ├── 2024_SNF_final_2024-06435.xml
            └── 2024_SNF_proposed_2024-06436.xml
    """
    # Parse command line arguments
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Create output directory
    save_dir = Path(args.output_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize counters
    total_docs = 0
    downloaded = 0
    already_existed = 0
    unrecognized = 0
    unsupported = 0
    failed = 0
    
    try:
        if args.mode == "single":
            if not args.doc_number:
                logger.error("Document number is required for single mode")
                return
            
            # Fetch single document
            doc = get_single_document(args.doc_number)
            if doc:
                total_docs = 1
                has_program, program_type = detect_program_type(doc)
                if has_program:
                    program_dir = save_dir / program_type
                    program_dir.mkdir(parents=True, exist_ok=True)
                    success = download_xml(doc, program_dir, logger=logger)
                    if success:
                        downloaded += 1
                    else:
                        failed += 1
                else:
                    unrecognized += 1
            else:
                failed += 1
        else:
            # Fetch latest documents
            logger.info(f"Fetching latest documents from the past {args.days} days...")
            docs = get_latest_documents(args.days)
            total_docs = len(docs)
            logger.info(f"Found {total_docs} documents")
            
            # Process each document
            for doc in docs:
                doc_number = doc.get("document_number", "")
                doc_type = doc.get("type", "")
                title = doc.get("title", "")
                
                # Skip correction documents
                if doc_number.startswith("C"):
                    logger.info(f"Skip {doc_number}: Correction document ({doc_number})")
                    continue
                
                # Skip future-dated documents
                publication_date = doc.get("publication_date", "")
                if publication_date and datetime.strptime(publication_date, "%Y-%m-%d") > datetime.now():
                    logger.info(f"Skip {doc_number}: Future-dated document ({publication_date})")
                    continue
                
                # Skip non-rule documents
                if doc_type not in ["Rule", "Proposed Rule"]:
                    logger.info(f"Skip {doc_number}: Unsupported document type ({doc_type})")
                    unsupported += 1
                    continue
                
                # Detect program type
                has_program, program_type = detect_program_type(doc)
                if not has_program:
                    logger.info(f"Unrecognized program type: {title}")
                    logger.info(f"{doc_number}: Unrecognized program type: {title}")
                    unrecognized += 1
                    continue
                
                # Create program type directory
                program_dir = save_dir / program_type
                program_dir.mkdir(parents=True, exist_ok=True)
                
                # Check if file already exists and is valid
                year = publication_date.split("-")[0]
                doc_type_suffix = "final" if doc_type == "Rule" else "proposed"
                filename = f"{year}_{program_type}_{doc_type_suffix}_{doc_number}.xml"
                filepath = program_dir / filename
                
                if filepath.exists() and is_valid_xml(filepath):
                    logger.info(f"Already exists and valid: {filepath}")
                    logger.info(f"{doc_number}: Already exists and valid: {filepath}")
                    already_existed += 1
                    continue
                
                # Download document
                logger.info(f"{doc_number}: Need to download: {doc_number}")
                success = download_xml(doc, program_dir, logger=logger)
                if success:
                    downloaded += 1
                else:
                    failed += 1
                
                # Add delay between downloads
                time.sleep(random.uniform(2, 5))
    
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return
    
    # Print summary
    logger.info("\nDownload Summary:")
    logger.info(f"Total documents: {total_docs}")
    logger.info(f"Successfully downloaded: {downloaded}")
    logger.info(f"Already existed: {already_existed}")
    logger.info(f"Unrecognized program type: {unrecognized}")
    logger.info(f"Unsupported document type: {unsupported}")
    logger.info(f"Failed: {failed}")

if __name__ == '__main__':
    main() 