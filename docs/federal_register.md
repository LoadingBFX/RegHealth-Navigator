# Federal Register Data Fetcher

## Overview

This tool fetches Medicare-related regulations from the Federal Register. It automatically identifies program types, standardizes file naming, and organizes documents in a structured directory.

## Program Type Detection

The tool identifies the following Medicare program types:

1. **MPFS (Medicare Physician Fee Schedule)**
   - Keywords: physician fee schedule, mpfs, pfs
   - Example: Medicare Physician Fee Schedule Update

2. **HOSPICE (Hospice Payment)**
   - Keywords: hospice wage, hospice payment, hospice quality
   - Example: Hospice Wage Index Update

3. **SNF (Skilled Nursing Facility)**
   - Keywords: skilled nursing facility, snf, nursing facility, consolidated billing
   - Example: Prospective Payment System and Consolidated Billing for Skilled Nursing Facilities

## Document Types

The tool processes the following document types:

1. **Rule (Final Rule)**
   - Type identifier: Rule
   - Filename suffix: final

2. **Proposed Rule**
   - Type identifier: Proposed Rule
   - Filename suffix: proposed

## File Naming Convention

Documents are named using the following format:
```
YYYY_PROGRAM_TYPE_DOC_TYPE_DOC_NUMBER.xml
```

Examples:
- `2024_MPFS_final_2024-06431.xml`
- `2024_HOSPICE_proposed_2024-06432.xml`

## Directory Structure

Documents are organized by program type:
```
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
```

## API Response Format

### Single Document Response
```json
{
    "document_number": "2024-06431",
    "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
    "type": "Rule",
    "publication_date": "2024-03-28",
    "html_url": "https://www.federalregister.gov/documents/2024/03/28/2024-06431/...",
    "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2024-03-28/pdf/2024-06431.pdf"
}
```

### Latest Documents Response
```json
{
    "results": [
        {
            "document_number": "2024-06431",
            "title": "Medicare Program; Calendar Year (CY) 2025 Home Health Prospective Payment System Rate Update",
            "type": "Rule",
            "publication_date": "2024-03-28",
            "html_url": "https://www.federalregister.gov/documents/2024/03/28/2024-06431/...",
            "pdf_url": "https://www.govinfo.gov/content/pkg/FR-2024-03-28/pdf/2024-06431.pdf"
        }
    ],
    "count": 1,
    "description": "Documents matching your search",
    "next_page_url": null
}
```

## XML URL Construction

The XML URL is constructed using the following format:
```
https://www.federalregister.gov/documents/full_text/xml/{year}/{document_number}.xml
```

Example:
- Document number: 2024-06431
- Year: 2024
- XML URL: https://www.federalregister.gov/documents/full_text/xml/2024/2024-06431.xml

## XML File Structure

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

## Usage

### Command Line Arguments

```bash
python -m core.data_fetcher.fetch_regulations [options]
```

Options:
- `--mode`: Operation mode
  - `single`: Download a single document
  - `latest`: Fetch latest documents (default)
- `--doc-number`: Document number (required for single mode)
- `--days`: Number of days to look back (default: 365)
- `--output-dir`: Output directory (default: data)
- `--verbose`: Enable verbose logging

### Examples

1. Fetch latest documents:
```bash
python -m core.data_fetcher.fetch_regulations --mode latest --days 30
```

2. Download a single document:
```bash
python -m core.data_fetcher.fetch_regulations --mode single --doc-number 2024-06431
```

3. Enable verbose logging:
```bash
python -m core.data_fetcher.fetch_regulations --mode latest --verbose
```

## Processing Flow

1. **Document Fetching**
   - Fetch document list from Federal Register API
   - Filter by start date (days ago from now)
   - Filter Medicare-related documents
   - Note: No end date needed as API returns latest documents by default

2. **Date Filtering**
   - Start date: Current date minus specified days
   - Example: If days=30, fetches documents from 30 days ago to now
   - No end date needed as we always want the latest documents
   - Future-dated documents are automatically excluded by the API

3. **Program Type Detection**
   - Identify program type from document title
   - Support multiple Medicare program types
   - Mark as UNCLASSIFIED if not recognized

4. **File Storage**
   - Store by program type
   - Use standardized filenames
   - Create necessary directory structure
   - Check file existence and validity

## Performance Optimization

1. **Pagination**
   - Fetch 100 documents per page
   - Handle multiple pages automatically
   - Ensure complete document list

2. **Rate Limiting**
   - Add delay only when downloading files
   - Delay: 2-5 seconds
   - Prevent rate limiting

3. **File Validation**
   - Check file existence
   - Verify file validity
   - Auto-redownload invalid files

## Logging

- Log file: `log/regulation_fetch.log`
- Log levels:
  - Default: INFO
  - Verbose: DEBUG
- Format: `%(asctime)s %(levelname)s %(message)s`

## Error Handling

1. **Network Errors**
   - Automatic retry
   - Error logging
   - Continue processing

2. **Document Processing Errors**
   - Skip invalid documents
   - Log error reasons
   - Generate error report

## Notes

1. Requires stable internet connection
2. Consider using a proxy server
3. Respect API rate limits
4. Monitor log files regularly
5. Clean up temporary files 