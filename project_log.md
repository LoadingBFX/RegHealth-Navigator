# Project Changelog & Discussion Summary

---

## 2025-07-07 — v0.6

### Summary of Changes
- **Enhanced year extraction in fetch_regulations.py**
  - Modified year extraction logic to use regex patterns from document titles instead of publication dates
  - Added `extract_year_from_title()` function with program-specific regex patterns
  - Updated file naming convention to reflect program years (CY/FY) rather than publication years
  - Improved program type detection to include "home health" documents
  - Added logic to skip correction documents based on title content (not just document number)

### Technical Decisions
- **Year Extraction Strategy**: Use regex patterns from titles instead of publication dates for more accurate file naming
- **Program-Specific Patterns**: 
  - MPFS: Extract "CY XXXX" (Calendar Year) with multiple pattern variations
  - HOSPICE: Extract "FY XXXX" (Fiscal Year) with multiple pattern variations  
  - SNF: Extract "Federal Fiscal Year XXXX"
- **Robust Pattern Matching**: Implemented multiple regex patterns per program type to handle different title formats
- **Error Handling**: Added graceful handling when year extraction fails

### Key Code Changes
```python
def extract_year_from_title(doc: Dict, program_type: str) -> Optional[str]:
    """Extract year from document title using regex patterns for different program types."""
    title = doc.get("title", "")
    
    if program_type == "MPFS":
        # Extract CY XXXX (Calendar Year) - multiple patterns
        patterns = [
            r'cy\s*(\d{4})',  # CY 2025
            r'calendar\s+year\s*\(cy\)\s*(\d{4})',  # Calendar Year (CY) 2025
            r'calendar\s+year\s+(\d{4})'  # Calendar Year 2025
        ]
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)
    
    elif program_type == "HOSPICE":
        # Extract FY XXXX (Fiscal Year) - multiple patterns
        patterns = [
            r'fy\s*(\d{4})',  # FY 2025
            r'fiscal\s+year\s*\(fy\)\s*(\d{4})',  # Fiscal Year (FY) 2025
            r'fiscal\s+year\s+(\d{4})'  # Fiscal Year 2025
        ]
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)
    
    elif program_type == "SNF":
        # Extract Federal Fiscal Year XXXX
        pattern = r'federal\s+fiscal\s+year\s+(\d{4})'
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None
```

```python
def detect_program_type(doc: Dict) -> Tuple[bool, str]:
    """Detect program type from document title."""
    title = doc.get("title", "").lower()
    
    # Skip correction documents based on title
    if "correction" in title:
        return False, ""
    
    # MPFS (Medicare Physician Fee Schedule)
    if any(keyword in title for keyword in ["medicare physician fee schedule","physician fee schedule", "mpfs", "pfs", "physician fee", "home health"]):
        return True, "MPFS"
    
    # HOSPICE (Hospice Payment)
    if any(keyword in title for keyword in ["hospice wage", "hospice payment", "hospice quality"]):
        return True, "HOSPICE"
    
    # SNF (Skilled Nursing Facility)
    if any(keyword in title for keyword in ["skilled nursing facility", "snf", "nursing facility", "consolidated billing"]):
        return True, "SNF"
    
    return False, ""
```

```python
# Updated file naming logic
# Extract year from title using regex patterns
year = extract_year_from_title(doc, program_type)
if not year:
    logger.error(f"Could not extract year from title for document {doc_number}")
    return False

# Get month and date from publication date for XML URL
month = publication_date.split("-")[1]
date = publication_date.split("-")[2]
doc_type_suffix = "final" if doc_type == "Rule" else "proposed"
filename = f"{year}_{program_type}_{doc_type_suffix}_{doc_number}.xml"
```

### User–Assistant Discussion Highlights
- **User requested year extraction from titles**: Specifically asked to extract program years (CY/FY) from document titles instead of using publication dates
- **Assistant implemented comprehensive solution**: Created regex-based extraction function with multiple patterns per program type
- **Collaborative testing**: Created and ran test suite to verify all patterns work correctly with various title formats
- **Systematic approach**: Updated both download logic and file existence checking to use new year extraction
- **Fixed duplicate download issue**: Resolved bug where files were being downloaded twice due to incorrect directory path construction and redundant existence checking
- **User requested additional filtering**: Asked to skip correction documents based on title content (not just document number)
- **Assistant implemented title-based filtering**: Added logic to detect_program_type to skip documents with "correction" in title

### Impact and Results
- **More Accurate File Naming**: Files now reflect the actual program year (CY/FY) rather than publication year
- **Better Organization**: Documents are grouped by the year they refer to, not when they were published
- **Enhanced Pattern Recognition**: Robust regex patterns handle multiple title formats for each program type
- **Improved Data Consistency**: All file operations now use the same year extraction logic
- **Comprehensive Testing**: All test cases pass, ensuring reliability across different document formats
- **Enhanced Document Filtering**: Improved correction document detection by checking both document number and title content
- **Eliminated Duplicate Downloads**: Fixed bug that caused files to be downloaded twice, improving efficiency and preventing wasted bandwidth

### Example Output Changes
- **Before**: `2024_MPFS_final_2024-06431.xml` (publication year)
- **After**: `2025_MPFS_final_2024-06431.xml` (program year from title)

---

## 2025-06-30 — v0.5

## 2025-06-30 — v0.5

### Summary of Changes
- **Fixed critical KeyError in auto_update_pipeline.py**
  - Resolved `KeyError: 'regulations'` by adding missing keys to stats dictionary
  - Added `"regulations"` and `"downloaded_files"` to returned stats
  - Fixed print statements to use correct key names
- **Enhanced OpenAI API rate limit handling**
  - Implemented exponential backoff with random jitter
  - Added automatic batch splitting for oversized requests
  - Enhanced error handling for `BadRequestError` and token limit issues
  - Improved logging with detailed retry attempts and wait times
- **Fixed data consistency issues between chunks and metadata**
  - Identified discrepancy: 1775 chunks vs 3015 metadata entries
  - Added `remove_metadata_for_file()` method to clean old entries
  - Modified `process_single_file()` to remove old metadata before processing
  - Ensured atomic operations: only write to processed_files.json if all steps succeed
- **Improved system robustness and error handling**
  - Added comprehensive validation and testing framework
  - Enhanced logging throughout the pipeline
  - Implemented graceful error recovery mechanisms

### Technical Decisions
- **Rate Limit Strategy**: Adopted exponential backoff (2^attempt + random jitter) instead of fixed delays
- **Data Consistency**: Implemented file-level metadata cleanup before reprocessing to prevent accumulation
- **Atomic Operations**: Ensured all processing steps succeed before marking files as processed
- **Error Handling**: Added specific handling for different OpenAI API error types (RateLimitError, BadRequestError)
- **Testing Approach**: Created comprehensive test suite to verify fixes without affecting production data

### Key Code Changes
```python
# Rate limit handling enhancement
def embed_batch(batch, model):
    for attempt in range(max_retries):
        try:
            # Validate batch size before sending
            total_tokens = sum(self.count_tokens(text) for text in batch)
            if total_tokens > self.max_tokens_per_batch:
                # Auto-split oversized batches
                mid = len(batch) // 2
                return embed_batch(batch[:mid], model) + embed_batch(batch[mid:], model)
            
            response = self.client.embeddings.create(input=batch, model=model)
            return [r.embedding for r in response.data]
            
        except openai.RateLimitError as e:
            # Exponential backoff with jitter
            wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"⚠️ Rate limit hit. Waiting {wait_time:.2f}s...")
            time.sleep(wait_time)
```

```python
# Data consistency fix
def process_single_file(self, file_path: str) -> Dict:
    # Step 0: Remove old metadata for this file to ensure consistency
    removed_metadata = self.faiss_updater.remove_metadata_for_file(file_path)
    if removed_metadata > 0:
        logger.info(f"🧹 Removed {removed_metadata} old metadata entries")
    
    # Step 1: Process file into chunks
    # Step 2: Update FAISS index with new chunks
    # Only write to processed_files.json if all steps succeed
```

### User–Assistant Discussion Highlights
- **User identified critical issues**: KeyError in auto_update_pipeline and data inconsistency between chunks/metadata
- **Assistant conducted thorough analysis**: Used codebase search and data analysis to identify root causes
- **Collaborative problem-solving**: User provided detailed analysis of rate limiting issues, Assistant implemented comprehensive fixes
- **Systematic approach**: Broke down complex issues into manageable components (rate limiting, data consistency, error handling)
- **Quality assurance**: Created and ran comprehensive test suite to verify all fixes work correctly

### Impact and Results
- **System Reliability**: Eliminated KeyError crashes and improved rate limit resilience
- **Data Integrity**: Ensured chunks, metadata, and FAISS index remain synchronized
- **Operational Efficiency**: Reduced processing failures and improved error recovery
- **Maintainability**: Enhanced logging and error handling for better debugging and monitoring

---

## 2025-06-02 — v0.4

### Summary of Changes
- Completed frontend infrastructure setup
  - Implemented document upload component
  - Added layout and navigation components
  - Configured React Router routing system
  - Integrated React Query for state management
- Configured GitHub Pages deployment
  - Added GitHub Actions workflow
  - Configured Vite build settings
  - Set up automated deployment pipeline
- Updated project documentation
  - Enhanced README.md
  - Added deployment guide
  - Updated project structure documentation

### Technical Decisions
- Selected Vite as build tool for improved development experience
- Implemented React Query for server state management and caching
- Adopted Tailwind CSS for responsive design
- Established GitHub Actions-based automated deployment pipeline

### User–Assistant Discussion Highlights
- User confirmed frontend architecture and component design
- Discussed and implemented GitHub Pages deployment strategy
- Enhanced project documentation and development guidelines

---

## 2024-06-10 — v0.3

### Summary of Changes
- Implemented section-based processing architecture
- Added caching for processed sections and artifacts
- Updated API endpoints to support section-level operations
- Added document comparison functionality
- Improved error handling and logging
- Added placeholder implementations for LLM integration

### Technical Decisions
- Adopted section-based processing to handle large documents efficiently
- Implemented caching to improve performance and reduce processing time
- Added proper error handling and logging throughout the codebase
- Used placeholder implementations for LLM features to enable frontend development
- Structured API endpoints to support section-level operations

### User–Assistant Discussion Highlights
- User requested section-based processing for better scalability
- Assistant implemented caching and proper error handling
- Both agreed on API structure and placeholder implementations

---

## 2024-06-09 — v0.2

### Summary of Changes
- Refactored backend and workflow to support section-based processing
- Updated PRD and team instructions to reflect new architecture
- Added/updated modules:
  - `core/xml_partition.py`: Partition XML into logical sections
  - `core/xml_chunker.py`: Chunk each section
  - `core/embedding.py`: Embedding and storage for section chunks
  - `core/llm.py`: Section-level LLM summarization, Q&A, comparison
- Improved API and frontend design for section selection and section-level operations

### Technical Decisions
- All LLM-based features now operate at the section level
- Rationale: Handles very large documents efficiently, avoids LLM context window limitations

### User–Assistant Discussion Highlights
- User clarified need for section-based processing
- Assistant proposed and implemented partition–chunk–embed–section-level LLM workflow
- Both agreed on API and frontend supporting section selection

---

## 2024-06-07 — v0.1

### Summary of Changes
- Initial project scaffold: frontend (React), backend (FastAPI), scripts
- Basic XML chunking and whole-document embedding/LLM workflow
- Initial PRD and team instructions

### Technical Decisions
- Started with whole-document chunking and LLM operations
- No section-based processing; scalability not yet addressed

### User–Assistant Discussion Highlights
- User requested fullstack scaffold and best practices
- Assistant provided initial codebase and documentation 