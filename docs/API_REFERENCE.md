# API Reference

**Author:** Fanxing Bu  
**Last Updated:** 2025-01-27  
**Status:** Active

---

## Overview

This document provides comprehensive API reference for the RegHealth Navigator backend. All endpoints return JSON responses and use standard HTTP status codes.

---

## Base URL

- **Development:** `http://localhost:8080`
- **Production:** `https://your-domain.com`

---

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

---

## Rate Limiting

- **Default:** No rate limiting implemented
- **Recommendation:** Implement rate limiting for production use

---

## Error Response Format

All error responses follow this standard format:

```json
{
  "error": "Error message description",
  "status": "error",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

---

## Endpoints

### 1. List Available Documents

**GET** `/api/documents`

Returns a list of all available regulatory documents in the system.

**Response:**
```json
{
  "documents": [
    {
      "id": "2024_MPFS_final_2023-24184",
      "name": "2024_MPFS_final_2023-24184.xml",
      "program": "MPFS",
      "year": "2024",
      "type": "final",
      "size": "2.3MB",
      "date": "2023-11-01"
    }
  ],
  "status": "success"
}
```

**Status Codes:**
- `200` - Success
- `500` - Internal server error

---

### 2. Chat/QA Endpoint

**POST** `/api/chat`

Submit a question and receive an AI-generated answer with citations.

**Request Body:**
```json
{
  "message": "What are the key changes in the 2024 MPFS final rule?",
  "filters": {
    "source_file": ["2024_MPFS_final_2023-24184.xml"]
  }
}
```

**Response:**
```json
{
  "answer": "The 2024 MPFS final rule includes several key changes...",
  "citations": [
    {
      "text": "relevant text excerpt",
      "source_file": "2024_MPFS_final_2023-24184.xml",
      "chunk_id": 123
    }
  ],
  "confidence": 0.85,
  "status": "success"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request
- `500` - Internal server error

---

### 3. Document Comparison

**POST** `/api/compare`

Compare two or more regulatory documents and receive a detailed analysis.

**Request Body:**
```json
{
  "query": "Compare payment rates between 2023 and 2024 MPFS final rules"
}
```

**Response:**
```json
{
  "topic": "payment rates comparison",
  "rule1": {
    "program": "MPFS",
    "year": "2023",
    "rule_type": "final"
  },
  "rule2": {
    "program": "MPFS", 
    "year": "2024",
    "rule_type": "final"
  },
  "section_comparisons": [
    {
      "section_name": "Payment Rates",
      "rule1_content": "summary of 2023 rates",
      "rule2_content": "summary of 2024 rates",
      "changes": "detailed analysis of changes"
    }
  ],
  "unique_sections": {
    "rule1_only": ["section names only in 2023"],
    "rule2_only": ["section names only in 2024"]
  },
  "status": "success"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request or no matching documents
- `500` - Internal server error

---

### 4. Generate Summary

**POST** `/api/summarize`

Generate a comprehensive summary for a specific document.

**Request Body:**
```json
{
  "doc_name": "2024_MPFS_final_2023-24184"
}
```

**Response:**
```json
{
  "summary": "Generated summary content in markdown format...",
  "file_path": "summary_outputs/2024_MPFS_final_2023-24184.md",
  "status": "success"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid document name
- `404` - Document not found
- `500` - Internal server error

---

### 5. Get Available Summaries

**GET** `/api/available-summaries`

Returns a list of all available summaries in the system.

**Response:**
```json
{
  "summaries": [
    {
      "doc_name": "2024_MPFS_final_2023-24184",
      "file_path": "summary_outputs/2024_MPFS_final_2023-24184.md",
      "program": "MPFS",
      "year": "2024",
      "type": "final",
      "generated_date": "2025-01-27T10:30:00Z"
    }
  ],
  "status": "success"
}
```

**Status Codes:**
- `200` - Success
- `500` - Internal server error

---

### 6. Get Specific Summary

**POST** `/api/get-summary`

Retrieve the content of a specific summary.

**Request Body:**
```json
{
  "doc_name": "2024_MPFS_final_2023-24184"
}
```

**Response:**
```json
{
  "summary": "Full summary content in markdown format...",
  "metadata": {
    "doc_name": "2024_MPFS_final_2023-24184",
    "program": "MPFS",
    "year": "2024",
    "type": "final"
  },
  "status": "success"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid document name
- `404` - Summary not found
- `500` - Internal server error

---

### 7. Federal Register Information

**GET** `/api/federal-register/{doc_number}`

Retrieve metadata about a specific Federal Register document.

**Parameters:**
- `doc_number` - Federal Register document number (e.g., "2023-24184")

**Response:**
```json
{
  "document_number": "2023-24184",
  "title": "Medicare Program; CY 2024 Physician Fee Schedule",
  "agency": "Centers for Medicare & Medicaid Services",
  "publication_date": "2023-11-01",
  "effective_date": "2024-01-01",
  "status": "success"
}
```

**Status Codes:**
- `200` - Success
- `404` - Document not found
- `500` - Internal server error

---

## Common Error Scenarios

### 1. No Matching Documents Found

**Error:** `400 Bad Request`
```json
{
  "error": "No matching documents found for comparison",
  "status": "error"
}
```

**Solution:** Ensure the query specifies the correct program type (MPFS, SNF, HOSPICE) and year.

### 2. Document Not Found

**Error:** `404 Not Found`
```json
{
  "error": "Document '2024_MPFS_final_2023-24184' not found",
  "status": "error"
}
```

**Solution:** Check the document name and ensure it exists in the system.

### 3. API Key Not Set

**Error:** `500 Internal Server Error`
```json
{
  "error": "OPENAI_API_KEY environment variable is not set",
  "status": "error"
}
```

**Solution:** Ensure the OpenAI API key is properly configured in the environment.

### 4. Rate Limit Exceeded

**Error:** `429 Too Many Requests`
```json
{
  "error": "OpenAI API rate limit exceeded. Please try again later.",
  "status": "error"
}
```

**Solution:** Wait before making additional requests or implement exponential backoff.

---

## Usage Examples

### Example 1: Ask a Question About MPFS

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key changes in the 2024 MPFS final rule?",
    "filters": {
      "source_file": ["2024_MPFS_final_2023-24184.xml"]
    }
  }'
```

### Example 2: Compare Two Years of MPFS Rules

```bash
curl -X POST http://localhost:8080/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare payment rates between 2023 and 2024 MPFS final rules"
  }'
```

### Example 3: Get Available Documents

```bash
curl -X GET http://localhost:8080/api/documents
```

---

## Development Notes

- All endpoints are implemented in `app/main.py`
- Error handling is centralized in the Flask error handlers
- CORS is configured to allow frontend access
- All responses include a `status` field for consistency

---

## Future Enhancements

1. **Authentication:** Implement JWT-based authentication
2. **Rate Limiting:** Add proper rate limiting for production
3. **Caching:** Implement response caching for frequently requested data
4. **Webhooks:** Add webhook support for real-time updates
5. **API Versioning:** Implement API versioning for backward compatibility