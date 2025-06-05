# Federal Register API Integration

## Overview
This document outlines the integration with the Federal Register API for downloading Medicare-related regulations and rules.

## File Structure

Downloaded documents are organized in the following structure:

```
data/
├── MPFS/          # Medicare Physician Fee Schedule documents
├── HOSPICE/       # Hospice payment and quality documents
└── SNF/           # Skilled Nursing Facility documents
```

The script `core/data_fetcher/fetch_regulations.py` handles the downloading and organization of these documents.

## Document Types

The system currently supports the following document types:

1. Final Rules
2. Proposed Rules

## File Naming Convention

Files are saved using the following naming convention:

```
{year}_{program_type}_{type}_{document_number}.xml
```

Where:
- `year`: Publication year (e.g., 2024)
- `program_type`: Program identifier (MPFS, HOSPICE, SNF)
- `type`: Document type (final, proposed)
- `document_number`: Original document number from Federal Register

Example: `2024_MPFS_final_2024-14828.xml`

## Logging

All operations are logged to `log/regulation_fetch.log` with the following information:
- Document processing status
- Download success/failure
- File organization
- Error messages and warnings

## Usage

### Single Document Download

```bash
python core/data_fetcher/fetch_regulations.py --mode single --doc-number 2024-14828 --verbose
```

### Batch Download

```bash
python core/data_fetcher/fetch_regulations.py --mode latest --days 7 --verbose
```

## Document Processing Rules

1. **Program Type Detection**
   - Documents are classified into program types based on their titles
   - Unrecognized program types are logged but not saved
   - Currently supported program types: MPFS, HOSPICE, SNF

2. **Document Type Handling**
   - Only final and proposed rules are processed
   - Other document types are logged but not saved
   - Correction documents (C1-, C2-, etc.) are skipped

3. **File Organization**
   - Files are saved in program-specific directories
   - Duplicate files are detected and skipped
   - File names follow the standardized format

## API Structure

### Base URL
```
https://www.federalregister.gov/api/v1
```