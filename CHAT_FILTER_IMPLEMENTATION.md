# Chat Filter Functionality Implementation

## Overview

This document describes the implementation of the chat document filtering functionality for the RegHealth Navigator application. The feature allows users to select specific documents before asking questions, ensuring that the AI responses are based only on the selected documents.

## Features Implemented

### 1. Backend API Enhancements

#### New Endpoint: `/api/documents`
- **Purpose**: Lists all available documents from the data directory
- **Method**: GET
- **Response**: JSON array of document objects with metadata
- **Location**: `app/main.py` - `list_documents()` function

#### Enhanced Chat Endpoint: `/api/chat`
- **Purpose**: Handles chat queries with optional document filtering
- **Method**: POST
- **Request Body**:
  ```json
  {
    "query": "string",
    "doc_names": ["optional", "list", "of", "document", "names"]
  }
  ```
- **Location**: `app/main.py` - `chat()` function

### 2. Search Service Updates

#### Document Filtering in Search
- **File**: `app/core/search.py`
- **Function**: `search()` method
- **Features**:
  - Filters chunks by `source_file` metadata
  - Only searches within selected documents
  - Maintains cosine similarity scoring
  - Returns top-k results from filtered set

#### Filter Implementation
```python
if filters and "source_file" in filters:
    filtered_chunks = []
    for i, chunk in enumerate(self.all_chunks):
        chunk_source_file = chunk.get("metadata", {}).get("source_file", "")
        if chunk_source_file in filters["source_file"]:
            # Include chunk in filtered results
```

### 3. Frontend Updates

#### Store Enhancements
- **File**: `front/src/store/store.ts`
- **New Functions**:
  - `fetchFiles()`: Loads documents from API
  - `setFiles()`: Updates file list
- **Enhanced FileType**: Added `program`, `year`, `type` fields

#### API Configuration
- **File**: `front/src/config/index.ts`
- **New Endpoint**: Added `documents: '/api/documents'`

#### ChatPanel Component
- **File**: `front/src/components/chat/ChatPanel.tsx`
- **Features**:
  - Fetches documents on component mount
  - Passes selected documents to chat API
  - Maintains existing UI for document selection

#### TypeScript Fixes
- **File**: `front/src/components/chat/ChatMessage.tsx`
- **Fix**: Properly typed `parts` array to handle string and JSX.Element

### 4. Configuration Integration

#### Document Path Configuration
- **File**: `app/config/development.yml`
- **Setting**: `docs_data.path: data/`
- **Usage**: Backend reads from configured data directory

#### Config Loader
- **File**: `app/config/__init__.py`
- **Property**: `docs_data_path` - resolves to absolute path

## Usage Flow

### 1. Document Discovery
1. User clicks the "+" button in chat interface
2. Frontend calls `/api/documents` endpoint
3. Backend scans `data/` directory for XML files
4. Returns structured document list with metadata

### 2. Document Selection
1. User can search and filter documents by:
   - Year (2022-2026)
   - Program (MPFS, HOSPICE, SNF)
   - Type (final, proposed)
2. User selects one or more documents
3. Selected documents appear as tags in chat header

### 3. Filtered Chat
1. User types question in chat input
2. Frontend sends request with:
   ```json
   {
     "query": "user question",
     "doc_names": ["selected_doc1.xml", "selected_doc2.xml"]
   }
   ```
3. Backend filters search to only selected documents
4. AI generates response based on filtered content
5. Response includes citations from selected documents only

## Testing

### Test Script
- **File**: `test_chat_filter.py`
- **Tests**:
  - Documents endpoint functionality
  - Chat without document filter
  - Chat with single document filter
  - Chat with multiple document filters

### Manual Testing
```bash
# Test documents endpoint
curl -X GET http://127.0.0.1:8080/api/documents

# Test chat with filter
curl -X POST http://127.0.0.1:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the conversion factor?", "doc_names": ["2024_MPFS_final_2023-24184.xml"]}'
```

## File Structure

```
app/
├── main.py                    # Enhanced with new endpoints
├── config/
│   ├── __init__.py           # Added docs_data_path property
│   └── development.yml       # Document path configuration
└── core/
    ├── search.py             # Enhanced with filtering
    └── summarizer.py         # Fixed import issue

front/src/
├── components/chat/
│   ├── ChatPanel.tsx         # Enhanced with document fetching
│   └── ChatMessage.tsx       # Fixed TypeScript error
├── store/
│   └── store.ts              # Added document fetching
└── config/
    └── index.ts              # Added documents endpoint
```

## Benefits

1. **Precision**: Users get answers based only on selected documents
2. **Relevance**: Reduces noise from unrelated regulations
3. **Control**: Users can focus on specific years, programs, or rule types
4. **Efficiency**: Faster responses when searching smaller document sets
5. **Transparency**: Clear indication of which documents are being analyzed

## Future Enhancements

1. **Document Preview**: Show document content before selection
2. **Smart Suggestions**: Recommend relevant documents based on question
3. **Document Categories**: Group documents by topic or impact
4. **Search History**: Remember user's document preferences
5. **Batch Operations**: Select/deselect multiple documents at once

## Technical Notes

- Document filtering happens at the chunk level, not document level
- FAISS index reconstruction is used for filtered searches
- Cosine similarity is maintained for ranking
- Error handling includes fallback to sample data if API fails
- TypeScript types are properly maintained throughout 