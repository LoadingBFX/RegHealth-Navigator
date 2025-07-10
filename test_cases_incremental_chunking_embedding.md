# Test Cases for Incremental Chunking and Embedding Functions

**Author:** Fanxing Bu  
**Module:** `app/core/incremental_chunker.py`, `app/core/incremental_faiss.py`, `app/core/xml_chunker.py`, `app/core/build_faiss.py`

## Overview

This document provides comprehensive test cases for the incremental processing system, including:
- Incremental chunking functions
- Incremental embedding functions  
- Base chunking and embedding functions
- Integration between components

---

## Module: `app/core/xml_chunker.py` (Base Chunking)

### 1. `XMLChunker.__init__(input_dir, chunk_words, overlap_sentences, output_chunks)`

**Function Description:** Initializes the XML chunker with configuration parameters.

**Test Cases:**

#### TC-001: Default Initialization
- **Description:** Test initialization with default parameters
- **Input:** No parameters
- **Expected Output:** XMLChunker instance with default values
- **Expected Values:**
  - input_dir=config.docs_data_path
  - chunk_words=500
  - overlap_sentences=1
  - output_chunks=config.build_faiss_output_folder/chunks.json

#### TC-002: Custom Parameters
- **Description:** Test initialization with custom parameters
- **Input:** `input_dir="/custom/path", chunk_words=300, overlap_sentences=2, output_chunks="/custom/chunks.json"`
- **Expected Output:** XMLChunker instance with custom values
- **Expected Values:**
  - input_dir=Path("/custom/path")
  - chunk_words=300
  - overlap_sentences=2
  - output_chunks="/custom/chunks.json"

---

### 2. `clean_text(text: str) -> str`

**Function Description:** Cleans text by removing extra whitespace.

**Test Cases:**

#### TC-003: Normal Text Cleaning
- **Description:** Test cleaning of normal text with extra whitespace
- **Input:** `"  This   is   a   test   text  "`
- **Expected Output:** `"This is a test text"`

#### TC-004: None Input
- **Description:** Test handling of None input
- **Input:** `None`
- **Expected Output:** `""`

#### TC-005: Empty String
- **Description:** Test handling of empty string
- **Input:** `""`
- **Expected Output:** `""`

#### TC-006: Multiple Whitespace Characters
- **Description:** Test cleaning of various whitespace characters
- **Input:** `"Text\twith\nmultiple\r\nspaces"`
- **Expected Output:** `"Text with multiple spaces"`

---

### 3. `infer_metadata_from_filename(filename: str) -> Dict`

**Function Description:** Extracts metadata from filename using regex patterns.

**Test Cases:**

#### TC-007: MPFS Final Rule
- **Description:** Test MPFS final rule filename parsing
- **Input:** `"2025_MPFS_final_2024-06431.xml"`
- **Expected Output:**
```json
{
    "source_file": "2025_MPFS_final_2024-06431.xml",
    "program": "MPFS",
    "rule_type": "Final",
    "year": 2025
}
```

#### TC-008: HOSPICE Proposed Rule
- **Description:** Test HOSPICE proposed rule filename parsing
- **Input:** `"2025_HOSPICE_proposed_2024-06432.xml"`
- **Expected Output:**
```json
{
    "source_file": "2025_HOSPICE_proposed_2024-06432.xml",
    "program": "Hospice",
    "rule_type": "Proposed",
    "year": 2025
}
```

#### TC-009: SNF Final Rule
- **Description:** Test SNF final rule filename parsing
- **Input:** `"2025_SNF_final_2024-06433.xml"`
- **Expected Output:**
```json
{
    "source_file": "2025_SNF_final_2024-06433.xml",
    "program": "SNF",
    "rule_type": "Final",
    "year": 2025
}
```

#### TC-010: Unknown Program Type
- **Description:** Test filename with unknown program type
- **Input:** `"2025_UNKNOWN_final_2024-06434.xml"`
- **Expected Output:**
```json
{
    "source_file": "2025_UNKNOWN_final_2024-06434.xml",
    "program": "Unknown",
    "rule_type": "Final",
    "year": 2025
}
```

#### TC-011: No Year in Filename
- **Description:** Test filename without year
- **Input:** `"MPFS_final_2024-06431.xml"`
- **Expected Output:**
```json
{
    "source_file": "MPFS_final_2024-06431.xml",
    "program": "MPFS",
    "rule_type": "Final",
    "year": null
}
```

---

### 4. `extract_preamb_metadata(root: ET.Element) -> Dict`

**Function Description:** Extracts metadata from XML document preamble.

**Test Cases:**

#### TC-012: Complete Metadata Extraction
- **Description:** Test extraction of complete metadata from XML
- **Input:** XML element with all metadata fields
- **Expected Output:**
```json
{
    "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
    "document_id": "2024-06431",
    "cfr": "42 CFR 484",
    "effective_date": "January 1, 2025"
}
```

#### TC-013: Missing Metadata Fields
- **Description:** Test extraction when some fields are missing
- **Input:** XML element with missing fields
- **Expected Output:**
```json
{
    "title": "Medicare Program Update",
    "document_id": "",
    "cfr": "",
    "effective_date": ""
}
```

#### TC-014: Empty XML Element
- **Description:** Test extraction from empty XML element
- **Input:** Empty XML element
- **Expected Output:**
```json
{
    "title": "",
    "document_id": "",
    "cfr": "",
    "effective_date": ""
}
```

---

### 5. `chunk_document(root: ET.Element, metadata: Dict) -> List[Dict]`

**Function Description:** Chunks XML document into smaller pieces based on word count and section headers.

**Test Cases:**

#### TC-015: Single Section Document
- **Description:** Test chunking of document with single section
- **Input:** XML with single section and multiple paragraphs
- **Expected Output:** List of chunks with proper metadata
- **Test Steps:**
  1. Create XML with single section
  2. Add multiple paragraphs exceeding chunk_words
  3. Verify chunks are created with correct word count
  4. Verify section headers are preserved

#### TC-016: Multi-Section Document
- **Description:** Test chunking of document with multiple sections
- **Input:** XML with multiple sections (HD1, HD2, HD3)
- **Expected Output:** List of chunks with hierarchical section headers
- **Test Steps:**
  1. Create XML with multiple section levels
  2. Verify section hierarchy is maintained
  3. Verify chunks span across sections correctly

#### TC-017: Overlap Between Chunks
- **Description:** Test sentence overlap between consecutive chunks
- **Input:** XML with paragraphs that create chunks with overlap
- **Expected Output:** Chunks with specified sentence overlap
- **Test Steps:**
  1. Create XML that triggers chunk creation
  2. Verify last sentences of chunk appear in next chunk
  3. Verify overlap_sentences parameter is respected

#### TC-018: Empty Document
- **Description:** Test chunking of empty document
- **Input:** XML with no content
- **Expected Output:** Empty list `[]`

#### TC-019: Document Below Chunk Threshold
- **Description:** Test document that doesn't reach chunk threshold
- **Input:** XML with content below chunk_words limit
- **Expected Output:** Single chunk with all content

---

### 6. `process_files() -> List[Dict]`

**Function Description:** Processes all XML files in input directory.

**Test Cases:**

#### TC-020: Multiple Files Processing
- **Description:** Test processing of multiple XML files
- **Input:** Directory with multiple XML files
- **Expected Output:** Combined list of chunks from all files
- **Test Steps:**
  1. Create multiple XML files in input directory
  2. Call process_files
  3. Verify all files are processed
  4. Verify chunks from all files are included

#### TC-021: Skip Root Files
- **Description:** Test that root-level XML files are skipped
- **Input:** Directory with XML files at root level
- **Expected Output:** Empty list (no chunks from root files)
- **Test Steps:**
  1. Create XML files at root level
  2. Call process_files
  3. Verify root files are skipped
  4. Verify appropriate log messages

#### TC-022: Error Handling
- **Description:** Test handling of malformed XML files
- **Input:** Directory with valid and invalid XML files
- **Expected Output:** Chunks from valid files only
- **Test Steps:**
  1. Create mix of valid and invalid XML files
  2. Call process_files
  3. Verify valid files are processed
  4. Verify errors are logged for invalid files

---

### 7. `save_chunks(chunks: List[Dict]) -> None`

**Function Description:** Saves chunks to output file.

**Test Cases:**

#### TC-023: Save Valid Chunks
- **Description:** Test saving valid chunks to file
- **Input:** List of valid chunk dictionaries
- **Expected Output:** Chunks saved to output file
- **Test Steps:**
  1. Create valid chunks list
  2. Call save_chunks
  3. Verify file is created
  4. Verify content matches input

#### TC-024: Create Output Directory
- **Description:** Test automatic creation of output directory
- **Input:** Chunks with non-existent output directory
- **Expected Output:** Directory created and chunks saved
- **Test Steps:**
  1. Set output_chunks to non-existent directory
  2. Call save_chunks
  3. Verify directory is created
  4. Verify file is saved

---

## Module: `app/core/incremental_chunker.py` (Incremental Chunking)

### 8. `IncrementalChunker.__init__(input_dir, chunk_words, overlap_sentences, output_chunks)`

**Function Description:** Initializes incremental chunker with configuration.

**Test Cases:**

#### TC-025: Default Initialization
- **Description:** Test initialization with default parameters
- **Input:** No parameters
- **Expected Output:** IncrementalChunker instance with defaults
- **Expected Values:**
  - input_dir=config.docs_data_path
  - chunk_words=500
  - overlap_sentences=1
  - output_chunks=config.build_faiss_output_folder/chunks.json
  - processed_files_tracker=config.build_faiss_output_folder/processed_files.json

---

### 9. `get_file_hash(file_path: Path) -> str`

**Function Description:** Generates SHA256 hash of file content.

**Test Cases:**

#### TC-026: File Hash Generation
- **Description:** Test hash generation for valid file
- **Input:** Path to valid file
- **Expected Output:** SHA256 hash string
- **Test Steps:**
  1. Create test file with known content
  2. Call get_file_hash
  3. Verify hash matches expected value

#### TC-027: Non-existent File
- **Description:** Test hash generation for non-existent file
- **Input:** Path to non-existent file
- **Expected Output:** FileNotFoundError

---

### 10. `load_processed_files() -> Dict`

**Function Description:** Loads processed files tracking information.

**Test Cases:**

#### TC-028: Load Existing File
- **Description:** Test loading existing processed files
- **Input:** Existing processed_files.json
- **Expected Output:** Dictionary with file tracking data
- **Sample Data:**
```json
{
    "MPFS/2025_MPFS_final_2024-06431.xml": {
        "hash": "abc123...",
        "processed_at": "1703123456.789",
        "chunks_count": 150
    }
}
```

#### TC-029: Non-existent File
- **Description:** Test loading when file doesn't exist
- **Input:** Non-existent processed_files.json
- **Expected Output:** Empty dictionary `{}`

---

### 11. `save_processed_files(processed_files: Dict) -> None`

**Function Description:** Saves processed files tracking information.

**Test Cases:**

#### TC-030: Save Valid Data
- **Description:** Test saving valid processed files data
- **Input:** Valid dictionary with file tracking data
- **Expected Output:** Data saved to file
- **Test Steps:**
  1. Create valid tracking data
  2. Call save_processed_files
  3. Verify file is created/updated
  4. Verify content matches input

---

### 12. `is_file_processed(file_path: Path) -> bool`

**Function Description:** Checks if file has been processed and is unchanged.

**Test Cases:**

#### TC-031: File Not Processed
- **Description:** Test unprocessed file
- **Input:** Path to unprocessed file
- **Expected Output:** `False`

#### TC-032: File Processed and Unchanged
- **Description:** Test processed file with same hash
- **Input:** Path to processed file with matching hash
- **Expected Output:** `True`

#### TC-033: File Processed but Modified
- **Description:** Test processed file with different hash
- **Input:** Path to processed file with different hash
- **Expected Output:** `False`

---

### 13. `find_new_files() -> List[Path]`

**Function Description:** Finds new or modified files that need processing.

**Test Cases:**

#### TC-034: New Files Found
- **Description:** Test finding new files
- **Input:** Directory with new XML files
- **Expected Output:** List of paths to new files
- **Test Steps:**
  1. Add new XML files to directory
  2. Call find_new_files
  3. Verify new files are returned

#### TC-035: Modified Files Found
- **Description:** Test finding modified files
- **Input:** Directory with modified XML files
- **Expected Output:** List of paths to modified files
- **Test Steps:**
  1. Modify existing XML files
  2. Call find_new_files
  3. Verify modified files are returned

#### TC-036: No New Files
- **Description:** Test when no new files exist
- **Input:** Directory with all files processed
- **Expected Output:** Empty list `[]`

---

### 14. `find_deleted_files() -> List[str]`

**Function Description:** Finds files that have been deleted.

**Test Cases:**

#### TC-037: Deleted Files Found
- **Description:** Test finding deleted files
- **Input:** processed_files.json with entries for deleted files
- **Expected Output:** List of deleted file paths
- **Test Steps:**
  1. Create processed_files.json with file entries
  2. Delete corresponding files
  3. Call find_deleted_files
  4. Verify deleted files are returned

#### TC-038: No Deleted Files
- **Description:** Test when no files are deleted
- **Input:** All processed files still exist
- **Expected Output:** Empty list `[]`

---

### 15. `cleanup_deleted_files(deleted_files: List[str]) -> None`

**Function Description:** Removes metadata for deleted files.

**Test Cases:**

#### TC-039: Cleanup Deleted Files
- **Description:** Test cleanup of deleted files metadata
- **Input:** List of deleted file paths
- **Expected Output:** Metadata removed from chunks.json
- **Test Steps:**
  1. Create chunks.json with file metadata
  2. Call cleanup_deleted_files
  3. Verify metadata is removed
  4. Verify processed_files.json is updated

---

### 16. `process_single_file(file_path: Path) -> List[Dict]`

**Function Description:** Processes a single XML file and returns chunks.

**Test Cases:**

#### TC-040: Valid File Processing
- **Description:** Test processing of valid XML file
- **Input:** Path to valid XML file
- **Expected Output:** List of chunks with metadata
- **Test Steps:**
  1. Create valid XML file
  2. Call process_single_file
  3. Verify chunks are created
  4. Verify metadata is correct

#### TC-041: Root File Processing
- **Description:** Test processing of root-level file
- **Input:** Path to root-level XML file
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Create XML file at root level
  2. Call process_single_file
  3. Verify empty list is returned
  4. Verify appropriate log message

#### TC-042: File Processing Error
- **Description:** Test handling of file processing errors
- **Input:** Path to malformed XML file
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Create malformed XML file
  2. Call process_single_file
  3. Verify empty list is returned
  4. Verify error is logged

---

### 17. `update_chunks_database(new_chunks: List[Dict], file_path: Path) -> None`

**Function Description:** Updates chunks database with new chunks.

**Test Cases:**

#### TC-043: Add New Chunks
- **Description:** Test adding new chunks to database
- **Input:** New chunks and file path
- **Expected Output:** Database updated with new chunks
- **Test Steps:**
  1. Create new chunks
  2. Call update_chunks_database
  3. Verify chunks are added
  4. Verify processed_files.json is updated

#### TC-044: Replace Existing Chunks
- **Description:** Test replacing existing chunks for same file
- **Input:** New chunks for already processed file
- **Expected Output:** Old chunks replaced with new ones
- **Test Steps:**
  1. Add chunks for existing file
  2. Call update_chunks_database with new chunks
  3. Verify old chunks are removed
  4. Verify new chunks are added

---

### 18. `process_file_incrementally(file_path: str) -> List[Dict]`

**Function Description:** Processes a single file incrementally.

**Test Cases:**

#### TC-045: New File Processing
- **Description:** Test processing of new file
- **Input:** Path to new XML file
- **Expected Output:** List of chunks and database updated
- **Test Steps:**
  1. Create new XML file
  2. Call process_file_incrementally
  3. Verify chunks are created
  4. Verify database is updated

#### TC-046: Already Processed File
- **Description:** Test processing of already processed file
- **Input:** Path to already processed file
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Process file once
  2. Call process_file_incrementally again
  3. Verify empty list is returned
  4. Verify appropriate log message

#### TC-047: Modified File Processing
- **Description:** Test processing of modified file
- **Input:** Path to modified XML file
- **Expected Output:** New chunks and database updated
- **Test Steps:**
  1. Process file once
  2. Modify file content
  3. Call process_file_incrementally
  4. Verify new chunks are created
  5. Verify database is updated

---

## Module: `app/core/build_faiss.py` (Base Embedding)

### 19. `setup_model(model_name) -> Tuple`

**Function Description:** Sets up model configuration and tokenizer.

**Test Cases:

#### TC-048: Default Model Setup
- **Description:** Test setup with default model
- **Input:** `model_name=None`
- **Expected Output:** Tuple of (encoding, model_config)
- **Test Steps:**
  1. Call setup_model with None
  2. Verify encoding is created
  3. Verify model_config is loaded

#### TC-049: Custom Model Setup
- **Description:** Test setup with custom model
- **Input:** `model_name="text-embedding-3-small"`
- **Expected Output:** Tuple of (encoding, model_config)
- **Test Steps:**
  1. Call setup_model with custom model
  2. Verify encoding matches model
  3. Verify model_config is correct

#### TC-050: Invalid Model
- **Description:** Test setup with invalid model
- **Input:** `model_name="invalid-model"`
- **Expected Output:** ValueError
- **Test Steps:**
  1. Call setup_model with invalid model
  2. Verify ValueError is raised

---

### 20. `count_tokens(text, encoding) -> int`

**Function Description:** Counts tokens in text using specified encoding.

**Test Cases:**

#### TC-051: Normal Text Token Count
- **Description:** Test token counting for normal text
- **Input:** `text="Hello world", encoding=cl100k_base`
- **Expected Output:** Integer token count
- **Test Steps:**
  1. Create test text
  2. Call count_tokens
  3. Verify token count is reasonable

#### TC-052: Empty Text
- **Description:** Test token counting for empty text
- **Input:** `text="", encoding=cl100k_base`
- **Expected Output:** `0`

#### TC-053: Long Text
- **Description:** Test token counting for long text
- **Input:** Long text string
- **Expected Output:** Large integer token count

---

### 21. `split_into_chunks(text, max_tokens, encoding) -> List[str]`

**Function Description:** Splits long text into smaller chunks by sentence.

**Test Cases:**

#### TC-054: Text Below Limit
- **Description:** Test text below token limit
- **Input:** Short text below max_tokens
- **Expected Output:** List with single chunk
- **Test Steps:**
  1. Create short text
  2. Call split_into_chunks
  3. Verify single chunk is returned

#### TC-055: Text Above Limit
- **Description:** Test text above token limit
- **Input:** Long text above max_tokens
- **Expected Output:** List with multiple chunks
- **Test Steps:**
  1. Create long text
  2. Call split_into_chunks
  3. Verify multiple chunks are returned
  4. Verify each chunk is within limit

#### TC-056: Sentence Boundary Splitting
- **Description:** Test splitting at sentence boundaries
- **Input:** Text with multiple sentences
- **Expected Output:** Chunks split at sentence boundaries
- **Test Steps:**
  1. Create text with multiple sentences
  2. Call split_into_chunks
  3. Verify chunks end at sentence boundaries

---

### 22. `get_openai_embeddings(texts, model, encoding) -> Tuple`

**Function Description:** Generates embeddings for text chunks with batching.

**Test Cases:**

#### TC-057: Single Batch Processing
- **Description:** Test processing of small text set
- **Input:** Small list of texts
- **Expected Output:** Tuple of (embeddings, total_tokens)
- **Test Steps:**
  1. Create small text list
  2. Call get_openai_embeddings
  3. Verify embeddings are generated
  4. Verify token count is correct

#### TC-058: Multiple Batch Processing
- **Description:** Test processing of large text set requiring multiple batches
- **Input:** Large list of texts
- **Expected Output:** Tuple of (embeddings, total_tokens)
- **Test Steps:**
  1. Create large text list
  2. Call get_openai_embeddings
  3. Verify all batches are processed
  4. Verify all embeddings are generated

#### TC-059: Long Chunk Splitting
- **Description:** Test splitting of long chunks during processing
- **Input:** Texts with some exceeding token limit
- **Expected Output:** Embeddings for all chunks including split ones
- **Test Steps:**
  1. Create texts with some long chunks
  2. Call get_openai_embeddings
  3. Verify long chunks are split
  4. Verify embeddings for all chunks

#### TC-060: API Error Handling
- **Description:** Test handling of OpenAI API errors
- **Input:** Valid texts with mocked API failure
- **Expected Output:** Exception or error handling
- **Test Steps:**
  1. Mock OpenAI API to fail
  2. Call get_openai_embeddings
  3. Verify error is handled appropriately

---

## Module: `app/core/incremental_faiss.py` (Incremental Embedding)

### 23. `IncrementalFAISS.__init__(model)`

**Function Description:** Initializes incremental FAISS updater.

**Test Cases:**

#### TC-061: Default Model Initialization
- **Description:** Test initialization with default model
- **Input:** `model=None`
- **Expected Output:** IncrementalFAISS instance with default model
- **Test Steps:**
  1. Call __init__ with None
  2. Verify default model is used
  3. Verify OpenAI client is initialized
  4. Verify tokenizer is set up

#### TC-062: Custom Model Initialization
- **Description:** Test initialization with custom model
- **Input:** `model="text-embedding-3-small"`
- **Expected Output:** IncrementalFAISS instance with custom model
- **Test Steps:**
  1. Call __init__ with custom model
  2. Verify custom model is used
  3. Verify configuration is loaded

#### TC-063: Missing API Key
- **Description:** Test initialization without API key
- **Input:** No OPENAI_API_KEY environment variable
- **Expected Output:** ValueError
- **Test Steps:**
  1. Remove OPENAI_API_KEY from environment
  2. Call __init__
  3. Verify ValueError is raised

---

### 24. `count_tokens(text: str) -> int`

**Function Description:** Counts tokens in text using instance encoding.

**Test Cases:**

#### TC-064: Token Counting
- **Description:** Test token counting with instance encoding
- **Input:** `text="Test text for token counting"`
- **Expected Output:** Integer token count
- **Test Steps:**
  1. Create test text
  2. Call count_tokens
  3. Verify token count is correct

---

### 25. `split_into_chunks(text: str, max_tokens: int) -> List[str]`

**Function Description:** Splits text into chunks using instance encoding.

**Test Cases:**

#### TC-065: Text Splitting
- **Description:** Test text splitting with instance encoding
- **Input:** Long text and max_tokens limit
- **Expected Output:** List of text chunks
- **Test Steps:**
  1. Create long text
  2. Call split_into_chunks
  3. Verify chunks are within limit
  4. Verify sentence boundaries are respected

---

### 26. `get_embeddings_for_chunks(chunks: List[str], model: str) -> List[List[float]]`

**Function Description:** Generates embeddings for text chunks with robust error handling.

**Test Cases:**

#### TC-066: Successful Embedding Generation
- **Description:** Test successful embedding generation
- **Input:** List of valid text chunks
- **Expected Output:** List of embedding vectors
- **Test Steps:**
  1. Create valid text chunks
  2. Call get_embeddings_for_chunks
  3. Verify embeddings are generated
  4. Verify all chunks are processed

#### TC-067: Rate Limit Handling
- **Description:** Test handling of rate limit errors
- **Input:** Text chunks with mocked rate limit
- **Expected Output:** Embeddings after retry
- **Test Steps:**
  1. Mock rate limit error
  2. Call get_embeddings_for_chunks
  3. Verify exponential backoff is used
  4. Verify embeddings are eventually generated

#### TC-068: Large Batch Splitting
- **Description:** Test splitting of large batches
- **Input:** Large batch exceeding token limit
- **Expected Output:** Embeddings for all chunks
- **Test Steps:**
  1. Create large batch
  2. Call get_embeddings_for_chunks
  3. Verify batch is split
  4. Verify all chunks are processed

#### TC-069: Empty Chunks List
- **Description:** Test handling of empty chunks list
- **Input:** Empty list `[]`
- **Expected Output:** Empty list `[]`

#### TC-070: Failed Embedding Generation
- **Description:** Test handling of embedding generation failure
- **Input:** Text chunks with mocked API failure
- **Expected Output:** `None`
- **Test Steps:**
  1. Mock API to fail consistently
  2. Call get_embeddings_for_chunks
  3. Verify None is returned
  4. Verify error is logged

---

### 27. `load_existing_index() -> Optional[faiss.Index]`

**Function Description:** Loads existing FAISS index if it exists.

**Test Cases:**

#### TC-071: Existing Index Load
- **Description:** Test loading existing index
- **Input:** Existing FAISS index file
- **Expected Output:** FAISS index object
- **Test Steps:**
  1. Create FAISS index file
  2. Call load_existing_index
  3. Verify index is loaded

#### TC-072: No Existing Index
- **Description:** Test when no index exists
- **Input:** No FAISS index file
- **Expected Output:** `None`
- **Test Steps:**
  1. Ensure no index file exists
  2. Call load_existing_index
  3. Verify None is returned

---

### 28. `load_existing_metadata() -> List[Dict]`

**Function Description:** Loads existing metadata if it exists.

**Test Cases:**

#### TC-073: Existing Metadata Load
- **Description:** Test loading existing metadata
- **Input:** Existing metadata file
- **Expected Output:** List of metadata dictionaries
- **Test Steps:**
  1. Create metadata file
  2. Call load_existing_metadata
  3. Verify metadata is loaded

#### TC-074: No Existing Metadata
- **Description:** Test when no metadata exists
- **Input:** No metadata file
- **Expected Output:** Empty list `[]`
- **Test Steps:**
  1. Ensure no metadata file exists
  2. Call load_existing_metadata
  3. Verify empty list is returned

---

### 29. `create_new_index(dimension: int) -> faiss.Index`

**Function Description:** Creates a new FAISS index.

**Test Cases:**

#### TC-075: New Index Creation
- **Description:** Test creation of new index
- **Input:** `dimension=1536`
- **Expected Output:** FAISS index with specified dimension
- **Test Steps:**
  1. Call create_new_index
  2. Verify index is created
  3. Verify dimension is correct

---

### 30. `update_index_with_new_chunks(new_chunks: List[Dict]) -> int`

**Function Description:** Updates FAISS index with new chunks.

**Test Cases:**

#### TC-076: New Chunks Addition
- **Description:** Test adding new chunks to index
- **Input:** List of new chunk dictionaries
- **Expected Output:** Number of embeddings added
- **Test Steps:**
  1. Create new chunks
  2. Call update_index_with_new_chunks
  3. Verify embeddings are generated
  4. Verify index is updated
  5. Verify metadata is updated

#### TC-077: Empty Chunks List
- **Description:** Test with empty chunks list
- **Input:** Empty list `[]`
- **Expected Output:** `0`

#### TC-078: Long Chunk Processing
- **Description:** Test processing of chunks that need splitting
- **Input:** Chunks with long text
- **Expected Output:** Embeddings for all processed chunks
- **Test Steps:**
  1. Create chunks with long text
  2. Call update_index_with_new_chunks
  3. Verify long chunks are split
  4. Verify all chunks are processed

#### TC-079: Embedding Generation Failure
- **Description:** Test handling of embedding generation failure
- **Input:** Chunks that cause embedding failure
- **Expected Output:** `0`
- **Test Steps:**
  1. Mock embedding generation to fail
  2. Call update_index_with_new_chunks
  3. Verify 0 is returned
  4. Verify error is logged

---

### 31. `update_metadata_with_new_chunks(new_chunks: List[Dict]) -> None`

**Function Description:** Updates metadata file with new chunks.

**Test Cases:**

#### TC-080: Metadata Update
- **Description:** Test updating metadata with new chunks
- **Input:** List of new chunk dictionaries
- **Expected Output:** Metadata file updated
- **Test Steps:**
  1. Create new chunks
  2. Call update_metadata_with_new_chunks
  3. Verify metadata file is updated
  4. Verify all chunks are included

#### TC-081: Chunk Splitting Consistency
- **Description:** Test consistency between embedding and metadata chunk splitting
- **Input:** Chunks that need splitting
- **Expected Output:** Metadata matches embedding chunks
- **Test Steps:**
  1. Create chunks that need splitting
  2. Call update_metadata_with_new_chunks
  3. Verify splitting logic matches embedding logic

---

### 32. `process_incremental_update(new_chunks: List[Dict]) -> Dict`

**Function Description:** Processes incremental update with new chunks.

**Test Cases:**

#### TC-082: Successful Incremental Update
- **Description:** Test successful incremental update
- **Input:** List of new chunk dictionaries
- **Expected Output:** Dictionary with update statistics
- **Expected Statistics:**
  - new_chunks_processed
  - new_embeddings_added
  - total_tokens
  - estimated_cost
  - model_used
  - model_pricing

#### TC-083: Empty Update
- **Description:** Test update with empty chunks list
- **Input:** Empty list `[]`
- **Expected Output:** Dictionary with zero statistics
- **Test Steps:**
  1. Call process_incremental_update with empty list
  2. Verify all statistics are zero
  3. Verify cost calculation is correct

#### TC-084: Cost Calculation
- **Description:** Test accurate cost calculation
- **Input:** Chunks with known token count
- **Expected Output:** Accurate cost estimate
- **Test Steps:**
  1. Create chunks with known token count
  2. Call process_incremental_update
  3. Verify cost calculation is accurate

---

## Integration Test Cases

### TC-085: Complete Incremental Pipeline
**Description:** Test complete incremental processing pipeline
**Test Steps:**
1. Initialize IncrementalPipeline
2. Add new XML file
3. Run process_single_file
4. Verify chunks are created
5. Verify embeddings are generated
6. Verify FAISS index is updated
7. Verify metadata is updated

### TC-086: File Modification Handling
**Description:** Test handling of file modifications
**Test Steps:**
1. Process file initially
2. Modify file content
3. Run incremental processing
4. Verify old chunks are removed
5. Verify new chunks are created
6. Verify index is updated correctly

### TC-087: Error Recovery
**Description:** Test error recovery in pipeline
**Test Steps:**
1. Introduce errors at various points
2. Run incremental processing
3. Verify partial results are preserved
4. Verify errors are handled gracefully
5. Verify system remains consistent

### TC-088: Performance Testing
**Description:** Test performance with large datasets
**Test Steps:**
1. Use large number of chunks
2. Measure processing time
3. Verify memory usage is reasonable
4. Verify system remains responsive

---

## Test Data Requirements

### Sample XML Structure
```xml
<?xml version="1.0" encoding="UTF-8"?>
<FRDOC>
    <PUBLISH>
        <PRDOCNO>2024-06431</PRDOCNO>
        <PUBDATE>2024-03-28</PUBDATE>
        <DOCTYPE>Rule</DOCTYPE>
        <SUBJECT>Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update</SUBJECT>
        <TEXT>
            <PREAMB>
                <AGENCY>Centers for Medicare &amp; Medicaid Services (CMS), HHS.</AGENCY>
                <ACTION>Final rule.</ACTION>
            </PREAMB>
            <SUPLINF>
                <HED>Supplementary Information:</HED>
                <HD1 SOURCE="HD1">I. Executive Summary</HD1>
                <P>This is the first paragraph of the executive summary.</P>
                <P>This is the second paragraph with more content.</P>
                <HD2 SOURCE="HD2">A. Background</HD2>
                <P>Background information goes here.</P>
            </SUPLINF>
        </TEXT>
    </PUBLISH>
</FRDOC>
```

### Sample Chunk Structure
```json
{
    "text": "This is the first paragraph of the executive summary. This is the second paragraph with more content.",
    "section_header": "I. Executive Summary",
    "chunk_index": 0,
    "hash": "abc123...",
    "metadata": {
        "source_file": "2025_MPFS_final_2024-06431.xml",
        "program": "MPFS",
        "rule_type": "Final",
        "year": 2025,
        "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
        "subfolder": "MPFS",
        "full_path": "/path/to/file.xml"
    }
}
```

### Sample Embedding Response
```json
{
    "data": [
        {
            "embedding": [0.1, 0.2, 0.3, ...],
            "index": 0,
            "object": "embedding"
        }
    ],
    "model": "text-embedding-3-small",
    "object": "list",
    "usage": {
        "prompt_tokens": 100,
        "total_tokens": 100
    }
}
```

---

## Notes

1. **Mocking Strategy:** All external API calls should be mocked for reliable testing
2. **File System Operations:** Use temporary directories for file system tests
3. **Error Simulation:** Test various error conditions including network failures and invalid data
4. **Performance Monitoring:** Track processing time and resource usage for large datasets
5. **Consistency Verification:** Ensure chunk splitting logic is consistent between components
6. **Cost Tracking:** Verify accurate cost calculation and tracking
7. **State Management:** Test proper state management during incremental updates 