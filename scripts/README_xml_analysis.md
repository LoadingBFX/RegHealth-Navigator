# XML Label Analysis Scripts

This directory contains scripts for analyzing XML files in the data directory and comparing XML label types across different folders (HOSPICE, MPFS, SNF).

## Scripts Overview

### 1. `analyze_xml_labels.py` - Comprehensive Analysis Script

**Purpose**: Performs a detailed analysis of XML labels across all folders in the data directory.

**Features**:
- Analyzes all XML files in HOSPICE, MPFS, and SNF folders
- Extracts all unique XML labels (tag names) from each file
- Compares labels across folders to check for consistency
- Generates detailed reports and saves results to JSON
- Provides comprehensive statistics and analysis

**Usage**:
```bash
python scripts/analyze_xml_labels.py
```

**Output**:
- Console report with detailed analysis
- JSON file: `xml_label_analysis_results.json`
- Summary indicating whether folders use consistent XML labels

### 2. `quick_xml_label_check.py` - Quick Check Script

**Purpose**: Provides a concise summary of XML label consistency across folders.

**Features**:
- Fast analysis of XML label consistency
- Simple console output with key findings
- No file output, just immediate results

**Usage**:
```bash
python scripts/quick_xml_label_check.py
```

**Output**:
- Quick summary of label counts per folder
- Whether all folders use the same label set
- List of unique labels per folder (if any differences found)
- List of common labels across all folders

### 3. `test_xml_label_analyzer.py` - Unit Tests

**Purpose**: Unit tests to verify the functionality of the XML label analyzer.

**Features**:
- Tests all major functions of the analyzer
- Uses temporary test files
- Verifies edge cases (empty folders, nonexistent folders)
- Ensures correct label extraction and comparison

**Usage**:
```bash
python scripts/test_xml_label_analyzer.py
```

## Analysis Results Summary

Based on the analysis of the current data directory:

### Label Counts by Folder Type:
- **HOSPICE**: 52 unique XML labels
- **MPFS**: 56 unique XML labels  
- **SNF**: 51 unique XML labels

### Consistency Check:
❌ **INCONSISTENT** - Folders have different XML label sets

### Differences Found:
- **MPFS** has 4 unique labels not found in other folders:
  - `APPENDIX`
  - `CONTENTS` 
  - `NOTE`
  - `SECHD`

### Common Labels:
All three folder types share 49 common XML labels, including:
- `RULE`, `PREAMB`, `AGENCY`, `SUBJECT`
- `P`, `HD`, `SECTION`, `SECTNO`
- `FTNT`, `FTREF`, `SU`, `E`
- And 39 other common labels

## Key Findings

1. **High Consistency**: 49 out of 52-56 labels are shared across all folder types
2. **Minor Differences**: Only MPFS has additional labels, likely for specific document features
3. **Core Structure**: All folders use the same core XML structure for regulatory documents
4. **Processing Compatibility**: The differences are minor enough that the same XML processing logic can handle all folder types

## Technical Details

### XML Label Categories:
- **Document Structure**: `RULE`, `PREAMB`, `SUPLINF`
- **Metadata**: `AGENCY`, `SUBJECT`, `CFR`, `DEPDOC`, `RIN`
- **Content**: `P`, `HD`, `SECTION`, `SECTNO`
- **Formatting**: `E`, `SU`, `FTNT`, `FTREF`
- **Tables**: `GPOTABLE`, `ROW`, `CHED`
- **MPFS-specific**: `APPENDIX`, `CONTENTS`, `NOTE`, `SECHD`

### Error Handling:
- Scripts handle malformed XML files gracefully
- Empty or nonexistent folders are handled appropriately
- Detailed logging for debugging

## Usage Recommendations

1. **For Quick Checks**: Use `quick_xml_label_check.py`
2. **For Detailed Analysis**: Use `analyze_xml_labels.py`
3. **For Development**: Run `test_xml_label_analyzer.py` to verify functionality
4. **For Integration**: Import `XMLLabelAnalyzer` class from `analyze_xml_labels.py`

## Dependencies

- Python 3.6+
- Standard library modules: `xml.etree.ElementTree`, `pathlib`, `json`, `logging`
- No external dependencies required

## Author

Fanxing Bu  
Date: 2024-12-19 