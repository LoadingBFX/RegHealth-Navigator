# Error Handling Strategy

**Author:** Fanxing Bu  
**Last Updated:** 2025-01-27  
**Status:** Active

---

## Overview

This document outlines the comprehensive error handling strategy for the RegHealth Navigator system. The strategy focuses on user-friendly error messages, graceful degradation, and detailed logging for debugging.

---

## Error Categories

### 1. User Input Errors (400 Bad Request)

**Common Scenarios:**
- Invalid document names
- Malformed API requests
- Missing required fields
- Invalid query parameters

**Handling Strategy:**
```python
# Example from app/main.py
@app.errorhandler(BadRequest)
def handle_bad_request(error: BadRequest) -> tuple[Dict[str, str], int]:
    return {"error": str(error), "status": "error"}, 400
```

**User-Friendly Messages:**
- "Document '2024_MPFS_final_2023-24184' not found. Please check the document name."
- "Invalid request format. Please ensure all required fields are provided."
- "No matching documents found for comparison. Please specify the program type (MPFS, SNF, HOSPICE)."

### 2. Resource Not Found (404 Not Found)

**Common Scenarios:**
- Document not found in system
- Summary file not generated
- API endpoint not found

**Handling Strategy:**
```python
@app.errorhandler(404)
def not_found(error: HTTPException) -> tuple[Dict[str, str], int]:
    return {"error": "Resource not found", "status": "error"}, 404
```

**User-Friendly Messages:**
- "The requested document is not available in our system."
- "Summary not found. Please generate the summary first."
- "The requested API endpoint does not exist."

### 3. Server Errors (500 Internal Server Error)

**Common Scenarios:**
- OpenAI API key not configured
- FAISS index corruption
- Memory or disk space issues
- Network connectivity problems

**Handling Strategy:**
```python
@app.errorhandler(500)
def internal_error(error: HTTPException) -> tuple[Dict[str, str], int]:
    return {"error": "Internal server error", "status": "error"}, 500
```

**User-Friendly Messages:**
- "Service temporarily unavailable. Please try again later."
- "Configuration error. Please contact system administrator."
- "Processing failed. Please check your request and try again."

---

## Error Response Format

All error responses follow a standardized format:

```json
{
  "error": "Human-readable error message",
  "status": "error",
  "timestamp": "2025-01-27T10:30:00Z",
  "details": {
    "error_code": "E001",
    "suggestion": "Helpful suggestion for resolution"
  }
}
```

---

## Specific Error Scenarios

### 1. OpenAI API Errors

**Rate Limit Exceeded:**
```json
{
  "error": "OpenAI API rate limit exceeded. Please try again in a few minutes.",
  "status": "error",
  "retry_after": 60
}
```

**API Key Issues:**
```json
{
  "error": "OpenAI API key not configured. Please contact administrator.",
  "status": "error"
}
```

**Token Limit Exceeded:**
```json
{
  "error": "Request too large. Please try a more specific query.",
  "status": "error"
}
```

### 2. Document Processing Errors

**File Not Found:**
```json
{
  "error": "Document '2024_MPFS_final_2023-24184.xml' not found in data directory.",
  "status": "error",
  "suggestion": "Check if the document exists in the data/MPFS/ directory."
}
```

**Invalid XML Format:**
```json
{
  "error": "Invalid XML format in document. Please check file integrity.",
  "status": "error"
}
```

### 3. Comparison Errors

**No Matching Documents:**
```json
{
  "error": "No matching documents found for comparison. Please specify the program type (MPFS, SNF, HOSPICE) in your query.",
  "status": "error",
  "examples": [
    "Compare MPFS 2024 vs 2025 quality reporting",
    "How do SNF 2023 and 2024 rules differ?",
    "Compare Hospice 2024 final vs proposed rules"
  ]
}
```

**Insufficient Data:**
```json
{
  "error": "Insufficient data for comparison. Please ensure both documents are available.",
  "status": "error"
}
```

---

## Frontend Error Handling

### 1. Chat Interface Errors

**No Documents Selected:**
```typescript
const errorMessage = {
  id: Date.now().toString(),
  role: 'assistant' as const,
  content: `Please select one or more documents before asking questions. You can choose documents from the available list.`
};
```

**Comparison Failures:**
```typescript
if (error instanceof Error && error.message.includes('No matching documents found')) {
  errorContent = `I couldn't find the specific documents you're asking about. Please try specifying the program type (e.g., 'MPFS', 'SNF', 'Hospice') in your query.

Some Examples:

**MPFS**
"Compare MPFS 2024 vs 2025 quality reporting"

**SNF**
"How do SNF 2023 and 2024 rules differ?"

**Hospice**
"Compare Hospice 2024 final vs proposed rules"

This will help me find the right documents to compare for you.`;
}
```

### 2. Loading States

**Processing Indicator:**
```typescript
{isProcessing && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-teal-50 p-6 rounded-lg shadow-lg max-w-md w-full border-2 border-teal-200">
      <h3 className="text-xl font-semibold mb-4 text-teal-700">Processing Document</h3>
      <div className="w-full bg-teal-100 rounded-full h-2.5 mb-4">
        <div 
          className="bg-teal-400 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
          style={{ width: `${processingProgress}%` }}
        ></div>
      </div>
      <p className="text-sm text-teal-700">
        {processingProgress < 100 
          ? `Processing document (${processingProgress}%)...` 
          : 'Finalizing and caching results...'}
      </p>
    </div>
  </div>
)}
```

---

## Logging Strategy

### 1. Error Logging

**Backend Logging:**
```python
import logging

logger = logging.getLogger(__name__)

try:
    # Operation that might fail
    result = process_document(file_path)
except Exception as e:
    logger.error(f"Failed to process document {file_path}: {str(e)}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    return {"error": "Document processing failed", "status": "error"}, 500
```

**Frontend Logging:**
```typescript
const handleError = (error: Error) => {
  console.error('API Error:', error);
  // Send to error tracking service (e.g., Sentry)
  if (process.env.NODE_ENV === 'production') {
    // Report to error tracking service
  }
};
```

### 2. Performance Monitoring

**API Response Times:**
```python
import time

start_time = time.time()
# API operation
response_time = time.time() - start_time
logger.info(f"API call completed in {response_time:.2f} seconds")
```

**Cost Tracking:**
```python
logger.info(f"OpenAI API cost: ${cost:.4f} for {tokens} tokens")
```

---

## Recovery Procedures

### 1. Automatic Recovery

**Retry Logic:**
```python
def api_call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except openai.RateLimitError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt + random.uniform(0, 1)
                logger.warning(f"Rate limit hit. Waiting {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                raise e
```

**Graceful Degradation:**
```python
def get_summary_with_fallback(doc_name):
    try:
        return get_generated_summary(doc_name)
    except FileNotFoundError:
        return get_placeholder_summary(doc_name)
```

### 2. Manual Recovery

**FAISS Index Corruption:**
```bash
# Validate system state
cd app/core
python incremental_pipeline.py --validate

# If validation fails, rebuild FAISS index
python incremental_pipeline.py --rebuild-index
```

**Summary Cache Issues:**
```bash
# Force regenerate specific summary
python incremental_summary.py --files "2024_MPFS_final_2023-24184.xml" --force

# Clear all batch cache manually
rm -rf ../../summary_outputs/batch_cache/
```

---

## User Communication

### 1. Error Messages Guidelines

**Do:**
- Use clear, non-technical language
- Provide specific suggestions for resolution
- Include examples when helpful
- Maintain consistent tone and style

**Don't:**
- Expose internal system details
- Use technical jargon
- Blame the user
- Provide generic "contact administrator" messages

### 2. Progressive Disclosure

**Level 1: Basic Error Message**
```
"Document not found. Please check the document name."
```

**Level 2: Detailed Error (for developers)**
```
"Document '2024_MPFS_final_2023-24184.xml' not found in data/MPFS/ directory. 
Available documents: ['2023_MPFS_final_2022-23873.xml', '2024_MPFS_proposed_2024-14828.xml']"
```

---

## Testing Error Scenarios

### 1. Unit Tests

```python
def test_invalid_document_name():
    response = client.post('/api/get-summary', 
                         json={'doc_name': 'invalid_doc'})
    assert response.status_code == 404
    assert 'Document not found' in response.json['error']

def test_missing_api_key():
    # Test with missing OpenAI API key
    response = client.post('/api/chat', 
                         json={'message': 'test'})
    assert response.status_code == 500
    assert 'API key' in response.json['error']
```

### 2. Integration Tests

```python
def test_comparison_with_no_matching_docs():
    response = client.post('/api/compare', 
                         json={'query': 'Compare invalid documents'})
    assert response.status_code == 400
    assert 'No matching documents' in response.json['error']
```

---

## Monitoring and Alerting

### 1. Error Rate Monitoring

**Key Metrics:**
- Error rate by endpoint
- Response time percentiles
- API cost tracking
- User session failures

### 2. Alerting Rules

**High Priority:**
- Error rate > 5% for any endpoint
- OpenAI API failures
- FAISS index corruption

**Medium Priority:**
- Response time > 10 seconds
- High API costs
- Missing documents

---

## Future Improvements

1. **Structured Error Codes:** Implement standardized error codes for better categorization
2. **Error Analytics:** Track error patterns to identify common issues
3. **Automated Recovery:** Implement more sophisticated automatic recovery mechanisms
4. **User Feedback:** Add error reporting from users to improve error messages
5. **Performance Monitoring:** Add real-time performance monitoring and alerting

---

**Note:** This error handling strategy should be reviewed and updated regularly based on user feedback and system performance metrics.