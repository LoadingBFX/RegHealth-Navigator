# Source Extraction Guide

**Author:** Fanxing Bu  
**Date:** 2024

## Overview

This guide explains how to use the source extraction functionality in the RegHealth Navigator system. The system provides methods to extract detailed information about sources used in answering queries, including file names, text previews, similarity scores, and full chunk content.

## Functions Available

### 1. ChatSearchService Methods

#### `extract_source_info_and_chunks(result, chunks)`
Extracts source information from the result and finds corresponding chunks.

**Parameters:**
- `result`: Dictionary from `ask_question` method
- `chunks`: List of chunks from `ask_question` method

**Returns:**
```python
{
    "extracted_sources": [
        {
            "source_id": 1,
            "source_file": "2024_MPFS_final_2023-24184.xml",
            "text_preview": "The methodology for calculating PE RVUs...",
            "distance": 0.4891,
            "full_text": "Full chunk text...",
            "metadata": {...}
        }
    ],
    "unique_source_files": ["file1.xml", "file2.xml"],
    "total_sources": 6
}
```

#### `print_source_chunks_info(result, chunks)`
Prints detailed information about sources and their corresponding chunks in a formatted way.

### 2. Standalone Functions

#### `extract_source_info_standalone(result, chunks)`
Standalone version of the extraction function that can be used without initializing the service.

#### `print_source_chunks_info_standalone(result, chunks)`
Standalone version of the print function.

### 3. Enhanced `ask_query` Function

The `ask_query` function now returns three values:
- `answer`: The generated answer
- `chunks`: The retrieved chunks
- `source_info`: Extracted source information

## Usage Examples

### Example 1: Basic Usage with ask_query

```python
from app.core.search import ask_query

# Ask a question and get source information
query = "How are PE RVUs established for specific services?"
answer, chunks, source_info = ask_query(query)

print(f"Answer: {answer}")
print(f"Total sources: {source_info['total_sources']}")
print(f"Unique files: {source_info['unique_source_files']}")
```

### Example 2: Using ChatSearchService Methods

```python
from app.core.search import ChatSearchService
import os

# Initialize service
service = ChatSearchService(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    faiss_index_path="./rag_data/faiss.index",
    metadata_path="./rag_data/faiss_metadata.json"
)

# Ask question
query = "What are the key components of RVU calculation?"
result, chunks = service.ask_question(query, top_k=5)

# Extract source information
source_info = service.extract_source_info_and_chunks(result, chunks)

# Print detailed information
service.print_source_chunks_info(result, chunks)
```

### Example 3: Using Standalone Functions

```python
from app.core.search import extract_source_info_standalone, print_source_chunks_info_standalone

# Assuming you have result and chunks from somewhere
source_info = extract_source_info_standalone(result, chunks)
print_source_chunks_info_standalone(result, chunks)
```

## Output Format

### Source Information Structure

Each source contains:
- **source_id**: Unique identifier for the source
- **source_file**: Name of the source file (e.g., "2024_MPFS_final_2023-24184.xml")
- **text_preview**: First 100 characters of the chunk text
- **distance**: FAISS distance score (lower is better)
- **similarity**: Calculated similarity score (1 - distance)
- **full_text**: Complete chunk text
- **metadata**: Additional metadata about the chunk

### Printed Output Example

```
================================================================================
📚 SOURCE INFORMATION EXTRACTION
================================================================================
Total unique source files: 6
Total sources extracted: 6

📁 Unique Source Files:
  1. 2023_MPFS_final_2022-23873.xml
  2. 2022_MPFS_proposed_2021-14973.xml
  3. 2022_MPFS_final_2021-23972.xml
  4. 2025_MPFS_final_2024-25382.xml
  5. 2024_MPFS_final_2023-24184.xml
  6. 2023_MPFS_proposed_2022-14562.xml

🔍 Detailed Source Information:

--- Source 1 ---
📄 File: 2024_MPFS_final_2023-24184.xml
📊 Distance: 0.4891
📈 Similarity: 0.5109
📝 Preview: The methodology for calculating PE RVUs is the same for both the facility and nonfacility RVUs but i...
📖 Full Text Length: 2943 characters
📖 Full Text (first 300 chars): The methodology for calculating PE RVUs is the same for both the facility and nonfacility RVUs but is applied independently to yield two separate PE RVUs. In calculating the PE RVUs for services furnished in a facility, we do not include resources that would generally not be provided by physicians w...
🏷️  Metadata: {'source_file': '2024_MPFS_final_2023-24184.xml', 'file_type': 'xml', ...}
```

## Testing

Run the test script to verify functionality:

```bash
python test_source_extraction.py
```

This will test both the main functions and standalone functions with real data.

## Key Features

1. **Comprehensive Source Extraction**: Extracts all relevant information from both result and chunks
2. **Duplicate Handling**: Automatically handles duplicate sources and unique file identification
3. **Detailed Metadata**: Includes file information, similarity scores, and full text content
4. **Formatted Output**: Provides clear, readable output with emojis and structured formatting
5. **Flexible Usage**: Can be used both as service methods and standalone functions
6. **Error Handling**: Robust error handling for missing or malformed data

## Notes

- The system automatically matches sources between `result['sources_used']` and `chunks` based on file names
- Distance scores are from FAISS (lower is better), similarity is calculated as `1 - distance`
- Full text is extracted from the corresponding chunk when available
- Metadata includes processing information, file details, and embedding information 