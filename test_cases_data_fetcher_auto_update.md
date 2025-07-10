# Test Cases for Data Fetcher and Auto Update Pipeline

**Author:** Fanxing Bu  
**Module:** `app/core/data_fetcher/fetch_regulations.py` and `app/core/auto_update_pipeline.py`

## Overview

This document provides comprehensive test cases for all functions in the data fetcher and auto update pipeline modules. Each test case includes:
- Function description
- Input/output specifications
- Test scenarios (normal, edge cases, error conditions)
- Sample data structures
- Expected behaviors

---

## Module: `app/core/data_fetcher/fetch_regulations.py`

### 1. `setup_logging(verbose: bool = False) -> logging.Logger`

**Function Description:** Sets up logging configuration with specified verbosity level.

**Test Cases:**

#### TC-001: Default Logging Setup
- **Description:** Test logging setup with default parameters (verbose=False)
- **Input:** `verbose=False`
- **Expected Output:** Logger instance with INFO level
- **Test Steps:**
  1. Call `setup_logging(False)`
  2. Verify logger level is INFO
  3. Verify logger format includes timestamp, level, and message

#### TC-002: Verbose Logging Setup
- **Description:** Test logging setup with verbose mode enabled
- **Input:** `verbose=True`
- **Expected Output:** Logger instance with DEBUG level
- **Test Steps:**
  1. Call `setup_logging(True)`
  2. Verify logger level is DEBUG
  3. Verify logger format is correct

#### TC-003: Logger Functionality Test
- **Description:** Test that created logger can log messages
- **Input:** `verbose=True`
- **Expected Output:** Logger that can log debug, info, warning, error messages
- **Test Steps:**
  1. Create logger with `setup_logging(True)`
  2. Log messages at different levels
  3. Verify messages are properly formatted

---

### 2. `get_single_document(doc_number: str) -> Optional[Dict]`

**Function Description:** Fetches a single document by its document number from Federal Register API.

**Test Cases:**

#### TC-004: Valid Document Fetch
- **Description:** Test fetching a valid document number
- **Input:** `doc_number="2024-06431"`
- **Expected Output:** Dictionary with document data
- **Sample Response:**
```json
{
    "document_number": "2024-06431",
    "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
    "type": "Rule",
    "publication_date": "2024-03-28",
    "html_url": "https://www.federalregister.gov/documents/2024/03/28/2024-06431/...",
    "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2024-03-28/pdf/2024-06431.pdf",
    "full_text_xml_url": "https://www.federalregister.gov/documents/full_text/xml/2024/2024-06431.xml"
}
```

#### TC-005: Invalid Document Number
- **Description:** Test fetching with invalid document number
- **Input:** `doc_number="invalid-doc-123"`
- **Expected Output:** `None`
- **Test Steps:**
  1. Call function with invalid document number
  2. Verify function returns None
  3. Verify error is logged

#### TC-006: Empty Document Number
- **Description:** Test with empty document number
- **Input:** `doc_number=""`
- **Expected Output:** `None`
- **Test Steps:**
  1. Call function with empty string
  2. Verify function returns None
  3. Verify error is logged

#### TC-007: Network Error Handling
- **Description:** Test behavior when network request fails
- **Input:** `doc_number="2024-06431"` (with mocked network failure)
- **Expected Output:** `None`
- **Test Steps:**
  1. Mock requests.get to raise RequestException
  2. Call function
  3. Verify function returns None
  4. Verify error is logged

---

### 3. `get_latest_documents(days: int = 365) -> List[Dict]`

**Function Description:** Fetches latest documents from Federal Register API with pagination support.

**Test Cases:**

#### TC-008: Default Days Parameter
- **Description:** Test with default days parameter (365)
- **Input:** `days=365`
- **Expected Output:** List of document dictionaries
- **Test Steps:**
  1. Call function with default parameter
  2. Verify returned list contains document dictionaries
  3. Verify documents have required fields (document_number, title, type, publication_date)

#### TC-009: Custom Days Parameter
- **Description:** Test with custom days parameter
- **Input:** `days=30`
- **Expected Output:** List of documents from last 30 days
- **Test Steps:**
  1. Call function with days=30
  2. Verify API call uses correct date range
  3. Verify returned documents are within date range

#### TC-010: Pagination Handling
- **Description:** Test handling of multiple pages of results
- **Input:** `days=365` (with mocked multi-page response)
- **Expected Output:** Combined list from all pages
- **Test Steps:**
  1. Mock API to return multiple pages
  2. Call function
  3. Verify all pages are processed
  4. Verify delay between requests

#### TC-011: Empty Results
- **Description:** Test when no documents are found
- **Input:** `days=1` (very recent)
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Call function with very recent date range
  2. Verify empty list is returned
  3. Verify no errors are logged

#### TC-012: API Error Handling
- **Description:** Test behavior when API request fails
- **Input:** `days=365` (with mocked API failure)
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Mock requests.get to raise RequestException
  2. Call function
  3. Verify empty list is returned
  4. Verify error is logged

---

### 4. `is_valid_xml(filepath: Path) -> bool`

**Function Description:** Validates if a file is a valid XML file using lxml parser.

**Test Cases:**

#### TC-013: Valid XML File
- **Description:** Test with valid XML file
- **Input:** Path to valid XML file
- **Expected Output:** `True`
- **Sample XML:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<FRDOC>
    <PUBLISH>
        <PRDOCNO>2024-06431</PRDOCNO>
        <PUBDATE>2024-03-28</PUBDATE>
        <DOCTYPE>Rule</DOCTYPE>
        <TITLE>Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update</TITLE>
    </PUBLISH>
</FRDOC>
```

#### TC-014: Invalid XML File
- **Description:** Test with malformed XML file
- **Input:** Path to invalid XML file
- **Expected Output:** `False`
- **Sample Invalid XML:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<FRDOC>
    <PUBLISH>
        <PRDOCNO>2024-06431</PRDOCNO>
        <PUBDATE>2024-03-28</PUBDATE>
        <DOCTYPE>Rule</DOCTYPE>
        <TITLE>Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update</TITLE>
    </PUBLISH>
<!-- Missing closing tag -->
```

#### TC-015: Non-XML File
- **Description:** Test with non-XML file (e.g., text file)
- **Input:** Path to text file
- **Expected Output:** `False`
- **Sample Content:**
```
This is a plain text file, not XML
```

#### TC-016: Non-existent File
- **Description:** Test with non-existent file path
- **Input:** Path to non-existent file
- **Expected Output:** `False`
- **Test Steps:**
  1. Call function with non-existent path
  2. Verify function returns False
  3. Verify no exception is raised

#### TC-017: Empty XML File
- **Description:** Test with empty XML file
- **Input:** Path to empty file
- **Expected Output:** `False`
- **Test Steps:**
  1. Create empty file
  2. Call function
  3. Verify function returns False

---

### 5. `extract_year_from_title(doc: Dict, program_type: str) -> Optional[str]`

**Function Description:** Extracts year from document title using regex patterns for different program types.

**Test Cases:**

#### TC-018: MPFS Calendar Year Extraction
- **Description:** Test year extraction for MPFS documents
- **Input:** 
  - `doc={"title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update"}`
  - `program_type="MPFS"`
- **Expected Output:** `"2025"`
- **Test Patterns:**
  - "CY 2025" → "2025"
  - "Calendar Year (CY) 2025" → "2025"
  - "Calendar Year 2025" → "2025"

#### TC-019: HOSPICE Fiscal Year Extraction
- **Description:** Test year extraction for HOSPICE documents
- **Input:**
  - `doc={"title": "Medicare Program; Fiscal Year (FY) 2025 Hospice Wage Index Update"}`
  - `program_type="HOSPICE"`
- **Expected Output:** `"2025"`
- **Test Patterns:**
  - "FY 2025" → "2025"
  - "Fiscal Year (FY) 2025" → "2025"
  - "Fiscal Year 2025" → "2025"

#### TC-020: SNF Federal Fiscal Year Extraction
- **Description:** Test year extraction for SNF documents
- **Input:**
  - `doc={"title": "Medicare Program; Federal Fiscal Year 2025 Prospective Payment System and Consolidated Billing for Skilled Nursing Facilities"}`
  - `program_type="SNF"`
- **Expected Output:** `"2025"`
- **Test Pattern:**
  - "Federal Fiscal Year 2025" → "2025"

#### TC-021: No Year Found
- **Description:** Test when no year pattern is found in title
- **Input:**
  - `doc={"title": "Medicare Program; General Update"}`
  - `program_type="MPFS"`
- **Expected Output:** `None`

#### TC-022: Case Insensitive Matching
- **Description:** Test case insensitive regex matching
- **Input:**
  - `doc={"title": "Medicare Program; calendar year (cy) 2025 update"}`
  - `program_type="MPFS"`
- **Expected Output:** `"2025"`

#### TC-023: Multiple Year Patterns
- **Description:** Test when multiple year patterns exist (should return first match)
- **Input:**
  - `doc={"title": "Medicare Program; Calendar Year (CY) 2025 and Fiscal Year 2026 Update"}`
  - `program_type="MPFS"`
- **Expected Output:** `"2025"`

#### TC-024: Invalid Program Type
- **Description:** Test with unsupported program type
- **Input:**
  - `doc={"title": "Medicare Program; Calendar Year (CY) 2025 Update"}`
  - `program_type="INVALID"`
- **Expected Output:** `None`

---

### 6. `detect_program_type(doc: Dict) -> Tuple[bool, str]`

**Function Description:** Detects program type from document title using keyword matching.

**Test Cases:**

#### TC-025: MPFS Detection
- **Description:** Test detection of MPFS program type
- **Input:** `doc={"title": "Medicare Physician Fee Schedule Update"}`
- **Expected Output:** `(True, "MPFS")`
- **Test Keywords:**
  - "medicare physician fee schedule"
  - "physician fee schedule"
  - "mpfs"

#### TC-026: HOSPICE Detection
- **Description:** Test detection of HOSPICE program type
- **Input:** `doc={"title": "Hospice Wage Index Update"}`
- **Expected Output:** `(True, "HOSPICE")`
- **Test Keywords:**
  - "hospice wage"
  - "hospice payment"
  - "hospice quality"

#### TC-027: SNF Detection
- **Description:** Test detection of SNF program type
- **Input:** `doc={"title": "Prospective Payment System and Consolidated Billing for Skilled Nursing Facilities"}`
- **Expected Output:** `(True, "SNF")`
- **Test Keywords:**
  - "skilled nursing facility"
  - "snf"
  - "nursing facility"
  - "consolidated billing"

#### TC-028: Correction Document Detection
- **Description:** Test detection of correction documents (should be skipped)
- **Input:** `doc={"title": "Medicare Program; Correction to Physician Fee Schedule"}`
- **Expected Output:** `(False, "")`

#### TC-029: Unrecognized Program Type
- **Description:** Test with unrecognized program type
- **Input:** `doc={"title": "Medicare Program; General Update"}`
- **Expected Output:** `(False, "")`

#### TC-030: Case Insensitive Detection
- **Description:** Test case insensitive keyword matching
- **Input:** `doc={"title": "MEDICARE PHYSICIAN FEE SCHEDULE UPDATE"}`
- **Expected Output:** `(True, "MPFS")`

#### TC-031: Empty Title
- **Description:** Test with empty title
- **Input:** `doc={"title": ""}`
- **Expected Output:** `(False, "")`

---

### 7. `download_xml(doc: Dict, save_dir: Path, logger: Optional[logging.Logger] = None) -> bool`

**Function Description:** Downloads XML file for a document and saves it with standardized naming.

**Test Cases:**

#### TC-032: Successful Download
- **Description:** Test successful XML download
- **Input:**
  - `doc={"document_number": "2024-06431", "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update", "type": "Rule", "publication_date": "2024-03-28"}`
  - `save_dir=Path("data")`
- **Expected Output:** `True`
- **Expected File:** `data/MPFS/2025_MPFS_final_2024-06431.xml`

#### TC-033: File Already Exists
- **Description:** Test when file already exists and is valid
- **Input:** Existing valid XML file
- **Expected Output:** `True`
- **Test Steps:**
  1. Create valid XML file at expected location
  2. Call download function
  3. Verify function returns True without downloading

#### TC-034: Invalid XML Download
- **Description:** Test when downloaded file is not valid XML
- **Input:** Document that returns invalid XML
- **Expected Output:** `False`
- **Test Steps:**
  1. Mock response to return invalid XML
  2. Call download function
  3. Verify function returns False
  4. Verify downloaded file is deleted

#### TC-035: Missing Document Information
- **Description:** Test with missing required document fields
- **Input:** `doc={"title": "Test Document"}` (missing document_number, publication_date, type)
- **Expected Output:** `False`

#### TC-036: Unrecognized Program Type
- **Description:** Test with document that has unrecognized program type
- **Input:** `doc={"document_number": "2024-06431", "title": "General Update", "type": "Rule", "publication_date": "2024-03-28"}`
- **Expected Output:** `False`

#### TC-037: Year Extraction Failure
- **Description:** Test when year cannot be extracted from title
- **Input:** `doc={"document_number": "2024-06431", "title": "Medicare Program Update", "type": "Rule", "publication_date": "2024-03-28"}`
- **Expected Output:** `False`

#### TC-038: Network Error During Download
- **Description:** Test behavior when network request fails
- **Input:** Valid document (with mocked network failure)
- **Expected Output:** `False`
- **Test Steps:**
  1. Mock requests.get to raise RequestException
  2. Call download function
  3. Verify function returns False
  4. Verify error is logged

#### TC-039: Directory Creation
- **Description:** Test automatic directory creation
- **Input:** Valid document with non-existent program directory
- **Expected Output:** `True`
- **Test Steps:**
  1. Ensure program directory doesn't exist
  2. Call download function
  3. Verify directory is created
  4. Verify file is saved

---

### 8. `generate_filename(doc: Dict, program_type: str) -> Optional[str]`

**Function Description:** Generates standardized filename for a document.

**Test Cases:**

#### TC-040: MPFS Final Rule Filename
- **Description:** Test filename generation for MPFS final rule
- **Input:**
  - `doc={"document_number": "2024-06431", "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update", "type": "Rule"}`
  - `program_type="MPFS"`
- **Expected Output:** `"2025_MPFS_final_2024-06431.xml"`

#### TC-041: HOSPICE Proposed Rule Filename
- **Description:** Test filename generation for HOSPICE proposed rule
- **Input:**
  - `doc={"document_number": "2024-06432", "title": "Medicare Program; Fiscal Year (FY) 2025 Hospice Wage Index Update", "type": "Proposed Rule"}`
  - `program_type="HOSPICE"`
- **Expected Output:** `"2025_HOSPICE_proposed_2024-06432.xml"`

#### TC-042: SNF Final Rule Filename
- **Description:** Test filename generation for SNF final rule
- **Input:**
  - `doc={"document_number": "2024-06433", "title": "Medicare Program; Federal Fiscal Year 2025 Prospective Payment System and Consolidated Billing for Skilled Nursing Facilities", "type": "Rule"}`
  - `program_type="SNF"`
- **Expected Output:** `"2025_SNF_final_2024-06433.xml"`

#### TC-043: Missing Document Number
- **Description:** Test with missing document number
- **Input:**
  - `doc={"title": "Test Document", "type": "Rule"}`
  - `program_type="MPFS"`
- **Expected Output:** `None`

#### TC-044: Missing Document Type
- **Description:** Test with missing document type
- **Input:**
  - `doc={"document_number": "2024-06431", "title": "Test Document"}`
  - `program_type="MPFS"`
- **Expected Output:** `None`

#### TC-045: Year Extraction Failure
- **Description:** Test when year cannot be extracted from title
- **Input:**
  - `doc={"document_number": "2024-06431", "title": "Medicare Program Update", "type": "Rule"}`
  - `program_type="MPFS"`
- **Expected Output:** `None`

---

### 9. `parse_args() -> argparse.Namespace`

**Function Description:** Parses command line arguments for the script.

**Test Cases:**

#### TC-046: Default Arguments
- **Description:** Test with no command line arguments
- **Input:** `[]` (empty argument list)
- **Expected Output:** Namespace with default values
- **Expected Values:**
  - mode='latest'
  - doc_number=None
  - date=None
  - days=365
  - output_dir='data'
  - verbose=False

#### TC-047: Single Mode with Document Number
- **Description:** Test single mode with document number
- **Input:** `["--mode", "single", "--doc-number", "2024-06431"]`
- **Expected Output:** Namespace with single mode and document number
- **Expected Values:**
  - mode='single'
  - doc_number='2024-06431'

#### TC-048: Latest Mode with Custom Days
- **Description:** Test latest mode with custom days
- **Input:** `["--mode", "latest", "--days", "30"]`
- **Expected Output:** Namespace with latest mode and 30 days
- **Expected Values:**
  - mode='latest'
  - days=30

#### TC-049: Verbose Mode
- **Description:** Test verbose flag
- **Input:** `["--verbose"]`
- **Expected Output:** Namespace with verbose=True

#### TC-050: Custom Output Directory
- **Description:** Test custom output directory
- **Input:** `["--output-dir", "/custom/path"]`
- **Expected Output:** Namespace with custom output directory
- **Expected Values:**
  - output_dir='/custom/path'

#### TC-051: Invalid Mode
- **Description:** Test with invalid mode argument
- **Input:** `["--mode", "invalid"]`
- **Expected Output:** SystemExit exception
- **Test Steps:**
  1. Call parse_args with invalid mode
  2. Verify SystemExit is raised

---

### 10. `main()`

**Function Description:** Main function that orchestrates the complete document fetching process.

**Test Cases:**

#### TC-052: Single Document Mode
- **Description:** Test main function in single document mode
- **Input:** Command line arguments for single document
- **Expected Output:** Downloaded XML file
- **Test Steps:**
  1. Mock command line arguments for single mode
  2. Call main function
  3. Verify document is fetched and downloaded
  4. Verify summary is printed

#### TC-053: Latest Documents Mode
- **Description:** Test main function in latest documents mode
- **Input:** Command line arguments for latest documents
- **Expected Output:** Multiple downloaded XML files
- **Test Steps:**
  1. Mock command line arguments for latest mode
  2. Call main function
  3. Verify documents are fetched and downloaded
  4. Verify summary statistics are printed

#### TC-054: Error Handling
- **Description:** Test main function error handling
- **Input:** Invalid command line arguments
- **Expected Output:** Error message and graceful exit
- **Test Steps:**
  1. Mock invalid arguments
  2. Call main function
  3. Verify error is handled gracefully

#### TC-055: Summary Statistics
- **Description:** Test summary statistics generation
- **Input:** Various document processing scenarios
- **Expected Output:** Accurate summary statistics
- **Test Steps:**
  1. Process documents with various outcomes
  2. Verify summary shows correct counts
  3. Verify all categories are accounted for

---

## Module: `app/core/auto_update_pipeline.py`

### 11. `AutoUpdatePipeline.__init__(days_back: int = 365, model: str = None)`

**Function Description:** Initializes the AutoUpdatePipeline with configuration parameters.

**Test Cases:**

#### TC-056: Default Initialization
- **Description:** Test initialization with default parameters
- **Input:** No parameters
- **Expected Output:** AutoUpdatePipeline instance with default values
- **Expected Values:**
  - days_back=365
  - model=config.default_embedding_model
  - data_dir=Path(config.docs_data_path)

#### TC-057: Custom Days Back
- **Description:** Test initialization with custom days_back
- **Input:** `days_back=30`
- **Expected Output:** AutoUpdatePipeline instance with custom days_back
- **Expected Values:**
  - days_back=30

#### TC-058: Custom Model
- **Description:** Test initialization with custom model
- **Input:** `model="text-embedding-ada-002"`
- **Expected Output:** AutoUpdatePipeline instance with custom model
- **Expected Values:**
  - model="text-embedding-ada-002"

#### TC-059: Both Custom Parameters
- **Description:** Test initialization with both custom parameters
- **Input:** `days_back=60, model="text-embedding-ada-002"`
- **Expected Output:** AutoUpdatePipeline instance with both custom values
- **Expected Values:**
  - days_back=60
  - model="text-embedding-ada-002"

---

### 12. `fetch_new_regulations() -> List[Dict]`

**Function Description:** Fetches new regulations from Federal Register and filters for relevant documents.

**Test Cases:**

#### TC-060: Successful Fetch with Relevant Documents
- **Description:** Test fetching regulations with relevant documents found
- **Input:** None (uses instance days_back)
- **Expected Output:** List of relevant regulation documents
- **Test Steps:**
  1. Mock get_latest_documents to return relevant documents
  2. Call fetch_new_regulations
  3. Verify relevant documents are returned
  4. Verify filtering logic works correctly

#### TC-061: No Relevant Documents
- **Description:** Test when no relevant documents are found
- **Input:** None
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Mock get_latest_documents to return irrelevant documents
  2. Call fetch_new_regulations
  3. Verify empty list is returned

#### TC-062: Correction Document Filtering
- **Description:** Test filtering of correction documents
- **Input:** Documents including correction documents
- **Expected Output:** List excluding correction documents
- **Test Steps:**
  1. Mock documents including correction documents (starting with "C")
  2. Call fetch_new_regulations
  3. Verify correction documents are filtered out

#### TC-063: Future-Dated Document Filtering
- **Description:** Test filtering of future-dated documents
- **Input:** Documents including future-dated documents
- **Expected Output:** List excluding future-dated documents
- **Test Steps:**
  1. Mock documents including future dates
  2. Call fetch_new_regulations
  3. Verify future-dated documents are filtered out

#### TC-064: Non-Rule Document Filtering
- **Description:** Test filtering of non-rule documents
- **Input:** Documents including non-rule types
- **Expected Output:** List containing only Rule and Proposed Rule documents
- **Test Steps:**
  1. Mock documents including non-rule types
  2. Call fetch_new_regulations
  3. Verify only rule documents are included

#### TC-065: Unrecognized Program Type Filtering
- **Description:** Test filtering of documents with unrecognized program types
- **Input:** Documents including unrecognized program types
- **Expected Output:** List containing only recognized program types
- **Test Steps:**
  1. Mock documents including unrecognized program types
  2. Call fetch_new_regulations
  3. Verify only recognized program types are included

#### TC-066: Error Handling
- **Description:** Test error handling during fetch process
- **Input:** None (with mocked error)
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Mock get_latest_documents to raise exception
  2. Call fetch_new_regulations
  3. Verify empty list is returned
  4. Verify error is logged

---

### 13. `download_new_files(regulations: List[Dict]) -> List[Path]`

**Function Description:** Downloads XML files for new regulations.

**Test Cases:**

#### TC-067: Successful Downloads
- **Description:** Test successful download of multiple files
- **Input:** List of valid regulation documents
- **Expected Output:** List of downloaded file paths
- **Test Steps:**
  1. Mock valid regulation documents
  2. Call download_new_files
  3. Verify files are downloaded
  4. Verify correct file paths are returned

#### TC-068: Empty Regulations List
- **Description:** Test with empty regulations list
- **Input:** `[]`
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Call download_new_files with empty list
  2. Verify empty list is returned
  3. Verify appropriate log message

#### TC-069: File Already Exists
- **Description:** Test when files already exist and are valid
- **Input:** Regulations for files that already exist
- **Expected Output:** List of existing file paths
- **Test Steps:**
  1. Create valid XML files at expected locations
  2. Call download_new_files
  3. Verify existing files are not re-downloaded
  4. Verify file paths are returned

#### TC-070: Download Failure Handling
- **Description:** Test handling of download failures
- **Input:** Regulations including some that will fail to download
- **Expected Output:** List of successfully downloaded file paths
- **Test Steps:**
  1. Mock some downloads to fail
  2. Call download_new_files
  3. Verify successful downloads are returned
  4. Verify failed downloads are logged

#### TC-071: Filename Generation Failure
- **Description:** Test when filename generation fails
- **Input:** Regulations that cannot generate valid filenames
- **Expected Output:** List excluding failed filename generations
- **Test Steps:**
  1. Mock regulations that cause filename generation to fail
  2. Call download_new_files
  3. Verify failed cases are skipped
  4. Verify errors are logged

#### TC-072: Directory Creation
- **Description:** Test automatic directory creation for new program types
- **Input:** Regulations for new program types
- **Expected Output:** List of downloaded files in new directories
- **Test Steps:**
  1. Mock regulations for new program types
  2. Ensure directories don't exist
  3. Call download_new_files
  4. Verify directories are created
  5. Verify files are saved in correct locations

---

### 14. `process_new_files(downloaded_files: List[Path]) -> List[Dict]`

**Function Description:** Processes newly downloaded files through incremental pipeline.

**Test Cases:**

#### TC-073: Successful Processing
- **Description:** Test successful processing of multiple files
- **Input:** List of valid file paths
- **Expected Output:** List of processing results
- **Test Steps:**
  1. Mock valid file paths
  2. Mock incremental pipeline to return success results
  3. Call process_new_files
  4. Verify processing results are returned

#### TC-074: Empty Files List
- **Description:** Test with empty files list
- **Input:** `[]`
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Call process_new_files with empty list
  2. Verify empty list is returned
  3. Verify appropriate log message

#### TC-075: Processing Failure Handling
- **Description:** Test handling of processing failures
- **Input:** Files including some that will fail processing
- **Expected Output:** List of processing results (successful and failed)
- **Test Steps:**
  1. Mock some files to fail processing
  2. Call process_new_files
  3. Verify successful processing results are returned
  4. Verify failed processing is logged

#### TC-076: Path Conversion
- **Description:** Test conversion of absolute paths to relative paths
- **Input:** List of absolute file paths
- **Expected Output:** Processing results for relative paths
- **Test Steps:**
  1. Provide absolute file paths
  2. Call process_new_files
  3. Verify paths are converted to relative paths
  4. Verify incremental pipeline receives relative paths

#### TC-077: Cost Tracking
- **Description:** Test cost tracking in processing results
- **Input:** Files with various processing costs
- **Expected Output:** Processing results with cost information
- **Test Steps:**
  1. Mock processing results with different costs
  2. Call process_new_files
  3. Verify cost information is preserved
  4. Verify cost display logic works correctly

---

### 15. `run_full_update() -> Dict`

**Function Description:** Runs the complete automated update process.

**Test Cases:**

#### TC-078: Complete Successful Update
- **Description:** Test complete successful update process
- **Input:** None
- **Expected Output:** Dictionary with complete update statistics
- **Test Steps:**
  1. Mock all sub-functions to return success
  2. Call run_full_update
  3. Verify all steps are executed
  4. Verify comprehensive statistics are returned
  5. Verify timing information is included

#### TC-079: No New Regulations
- **Description:** Test when no new regulations are found
- **Input:** None
- **Expected Output:** Dictionary with zero statistics
- **Test Steps:**
  1. Mock fetch_new_regulations to return empty list
  2. Call run_full_update
  3. Verify statistics show zero values
  4. Verify process completes gracefully

#### TC-080: Partial Success
- **Description:** Test when some steps succeed and others fail
- **Input:** None
- **Expected Output:** Dictionary with mixed success/failure statistics
- **Test Steps:**
  1. Mock mixed success/failure scenarios
  2. Call run_full_update
  3. Verify statistics reflect partial success
  4. Verify all steps are attempted

#### TC-081: Error Handling
- **Description:** Test error handling during update process
- **Input:** None (with mocked errors)
- **Expected Output:** Dictionary with error information
- **Test Steps:**
  1. Mock errors in various steps
  2. Call run_full_update
  3. Verify errors are handled gracefully
  4. Verify partial results are returned

#### TC-082: Statistics Calculation
- **Description:** Test accurate statistics calculation
- **Input:** Various processing scenarios
- **Expected Output:** Accurate statistics dictionary
- **Expected Statistics:**
  - regulations_found
  - files_downloaded
  - files_processed
  - files_successful
  - total_chunks_created
  - total_embeddings_added
  - total_cost
  - duration_seconds

#### TC-083: Timing Information
- **Description:** Test timing information in results
- **Input:** None
- **Expected Output:** Dictionary with accurate timing
- **Test Steps:**
  1. Call run_full_update
  2. Verify duration_seconds is included
  3. Verify timing is reasonable
  4. Verify timing is rounded to 2 decimal places

---

### 16. `check_for_updates() -> bool`

**Function Description:** Checks if there are any new regulations available.

**Test Cases:**

#### TC-084: Updates Available
- **Description:** Test when new regulations are available
- **Input:** None
- **Expected Output:** `True`
- **Test Steps:**
  1. Mock fetch_new_regulations to return new regulations
  2. Mock some files to not exist
  3. Call check_for_updates
  4. Verify True is returned

#### TC-085: No Updates Available
- **Description:** Test when no new regulations are available
- **Input:** None
- **Expected Output:** `False`
- **Test Steps:**
  1. Mock fetch_new_regulations to return empty list
  2. Call check_for_updates
  3. Verify False is returned

#### TC-086: All Files Already Exist
- **Description:** Test when regulations exist but files are already downloaded
- **Input:** None
- **Expected Output:** `False`
- **Test Steps:**
  1. Mock fetch_new_regulations to return regulations
  2. Mock all files to exist
  3. Call check_for_updates
  4. Verify False is returned

#### TC-087: Mixed Scenario
- **Description:** Test when some files exist and others don't
- **Input:** None
- **Expected Output:** `True`
- **Test Steps:**
  1. Mock fetch_new_regulations to return regulations
  2. Mock some files to exist and others to not exist
  3. Call check_for_updates
  4. Verify True is returned (if any files missing)

#### TC-088: Error Handling
- **Description:** Test error handling during update check
- **Input:** None (with mocked errors)
- **Expected Output:** `False`
- **Test Steps:**
  1. Mock fetch_new_regulations to raise exception
  2. Call check_for_updates
  3. Verify False is returned
  4. Verify error is logged

---

### 17. `get_system_status() -> Dict`

**Function Description:** Gets comprehensive system status information.

**Test Cases:**

#### TC-089: Complete Status Information
- **Description:** Test complete system status retrieval
- **Input:** None
- **Expected Output:** Dictionary with comprehensive status information
- **Expected Keys:**
  - updates_available
  - days_back
  - last_check
  - processed_files_count
  - total_chunks
  - faiss_index_size
  - new_files
  - deleted_files

#### TC-090: Status with Updates Available
- **Description:** Test status when updates are available
- **Input:** None
- **Expected Output:** Dictionary with updates_available=True
- **Test Steps:**
  1. Mock check_for_updates to return True
  2. Call get_system_status
  3. Verify updates_available=True

#### TC-091: Status with No Updates
- **Description:** Test status when no updates are available
- **Input:** None
- **Expected Output:** Dictionary with updates_available=False
- **Test Steps:**
  1. Mock check_for_updates to return False
  2. Call get_system_status
  3. Verify updates_available=False

#### TC-092: Incremental Pipeline Status Integration
- **Description:** Test integration with incremental pipeline status
- **Input:** None
- **Expected Output:** Dictionary including incremental pipeline status
- **Test Steps:**
  1. Mock incremental pipeline status
  2. Call get_system_status
  3. Verify incremental pipeline status is included
  4. Verify all status information is merged correctly

#### TC-093: Timestamp Information
- **Description:** Test timestamp information in status
- **Input:** None
- **Expected Output:** Dictionary with current timestamp
- **Test Steps:**
  1. Call get_system_status
  2. Verify last_check contains current timestamp
  3. Verify timestamp is in ISO format

---

## Integration Test Cases

### TC-094: End-to-End Pipeline Test
**Description:** Test complete end-to-end pipeline execution
**Test Steps:**
1. Initialize AutoUpdatePipeline
2. Run complete update process
3. Verify all components work together
4. Verify final results are consistent

### TC-095: Error Recovery Test
**Description:** Test system recovery after errors
**Test Steps:**
1. Introduce errors at various points
2. Verify system continues processing
3. Verify partial results are preserved
4. Verify error reporting is accurate

### TC-096: Performance Test
**Description:** Test performance with large datasets
**Test Steps:**
1. Use large number of regulations
2. Measure processing time
3. Verify memory usage is reasonable
4. Verify system remains responsive

### TC-097: Configuration Test
**Description:** Test different configuration scenarios
**Test Steps:**
1. Test with different models
2. Test with different days_back values
3. Test with different data directories
4. Verify configuration is properly applied

---

## Test Data Requirements

### Sample Document Data
```json
{
    "document_number": "2024-06431",
    "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
    "type": "Rule",
    "publication_date": "2024-03-28",
    "html_url": "https://www.federalregister.gov/documents/2024/03/28/2024-06431/...",
    "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2024-03-28/pdf/2024-06431.pdf",
    "full_text_xml_url": "https://www.federalregister.gov/documents/full_text/xml/2024/2024-06431.xml"
}
```

### Sample XML Structure
```xml
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
```

### Sample Processing Results
```json
{
    "status": "success",
    "chunks_created": 150,
    "embeddings_added": 150,
    "estimated_cost": 0.0450,
    "file_path": "MPFS/2025_MPFS_final_2024-06431.xml"
}
```

---

## Notes

1. **Mocking Strategy:** All external API calls should be mocked to ensure test reliability and speed.
2. **File System Operations:** Use temporary directories for file system tests to avoid conflicts.
3. **Error Simulation:** Test various error conditions including network failures, invalid data, and system errors.
4. **Performance Considerations:** Monitor test execution time and resource usage for large datasets.
5. **Configuration Management:** Ensure tests use appropriate configuration for different environments.
6. **Logging Verification:** Verify that appropriate log messages are generated for different scenarios.
7. **Edge Cases:** Pay special attention to edge cases such as empty inputs, malformed data, and boundary conditions. 