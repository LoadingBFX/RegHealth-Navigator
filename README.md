# 🏥 RegHealth Navigator

**A collaboration between Carnegie Mellon University (CMU) and [Simply Compliance Consulting](https://www.simplycomplianceconsulting.com/)**

**Authors:**  
Seon Young Jhang, Daisy Yan, Fanxing Bu, Dhruv Tangri, Sarvesh Siras, Saicharan Emmadi

**Last Updated:** Jul 2025

**Status:** 🚀 Pre-release v0.8

[![Capstone Project](https://img.shields.io/badge/CMU-Capstone%20Project-red)](https://www.cmu.edu/)
[![Version](https://img.shields.io/badge/version-v0.8-blue)](#)
[![License: Apache](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Last Updated](https://img.shields.io/badge/last%20updated-Jul%202025-lightgrey)](#)

[![Backend](https://img.shields.io/badge/backend-Flask-blue)](https://flask.palletsprojects.com/)
[![Frontend](https://img.shields.io/badge/frontend-React-blue)](https://reactjs.org/)
[![LLM](https://img.shields.io/badge/LLM-OpenAI-orange)](https://platform.openai.com/)
[![Vector Search](https://img.shields.io/badge/Vector%20Search-FAISS-darkgreen)](https://github.com/facebookresearch/faiss)
[![Language](https://img.shields.io/badge/language-Python%203.8%2B-yellow)](https://www.python.org/)
[![RAG](https://img.shields.io/badge/Architecture-RAG-blueviolet)](#)

---

## 📖 Project Introduction

RegHealth Navigator is an intelligent regulatory document analysis platform designed to help healthcare professionals, compliance officers, and policy analysts efficiently understand and analyze complex Medicare regulations. The system provides powerful tools for document comparison, semantic search, and AI-powered analysis with comprehensive documentation and maintainable code structure.


https://github.com/user-attachments/assets/c9ce0294-80d4-4cd8-b4fd-f27fd39d5b41


### 🎯 Key Features
- **Intelligent Document Processing**: Automated fetching and processing of Federal Register regulations
- **Semantic Search**: Advanced RAG-based search with FAISS indexing
- **Document Comparison**: AI-powered comparison of regulatory documents across different years
- **Incremental Updates**: Cost-efficient processing that only handles new or modified files
- **Comprehensive Logging**: Detailed tracking of all operations and costs
- **Modern UI**: React-based frontend with intuitive user interface

---

## 📁 Project Structure
```
RegHealth-Navigator/
├── app/         # Backend (core logic, API, config)
├── front/       # Frontend (React app)
├── data/        # Regulation data storage
├── rag_data/    # FAISS index and metadata (not in git)
├── docs/        # Documentation
├── scripts/     # Utility scripts
├── summary_outputs/ # Generated summaries
├── log/         # Application logs
├── assets/      # Project assets and images
├── .env         # Backend sensitive config (not committed)
├── requirements.txt  # Backend dependencies
└── README.md    # Project overview
```

> Example data for `data`, `rag_data`, and `summary_outputs` can be found at:
> - `data`: [Google Drive Link](https://drive.google.com/file/d/1P_LLnsZ0bnetWVOSbLYWdUwfwbI6Mt4F/view?usp=drive_link)
> - `rag_data`: [Google Drive Link](https://drive.google.com/file/d/1i5ArE-khILLxQLsNdDmbjyVcRNWco5jU/view?usp=drive_link)
> - `summary_outputs`: [Google Drive Link](https://drive.google.com/file/d/1vnTfsYEzZkmEcz_Tm8MSCnySmOCl0XZr/view?usp=drive_link)

---

## 🏗️ Architecture Overview

### Project Management & Summary Development (Seon)
**Responsibilities:**
- Project management: progress tracking, requirements clarification, meeting organization
- Summary development and optimization: leading the design and improvement of the summary module

### System Architecture & Data Pipeline (Fanxing Bu)
**Responsibilities:**
- System architecture design and implementation
- Data preprocessing pipeline (download, chunk, embedding, summary)
- UI design and implementation
- Backend framework design
- Summary performance optimization
- API development and integration
- Code integration

### Document Processing, Q&A & Documentation Management (Dhruv)
**Responsibilities:**
- Data preprocessing and optimization
- Q&A functionality development
- Document comparison feature development
- Documentation management: maintaining and updating technical documentation

### Document Q&A & Risk Management (Daisy)
**Responsibilities:**
- Document Q&A functionality development and optimization
- Demo video production
- Risk management
- Customer requirement communication

### Quality Management & Testing (Sai)
**Responsibilities:**
- Quality management
- Testing and validation
- System evaluation

### Backend Integration & API Development (Sarvesh)
**Responsibilities:**
- Backend integration
- API development and maintenance

---

## ⚙️ Configuration & Environment Variables

### Backend Configuration
- **`.env`**: Stores sensitive information (e.g., `OPENAI_API_KEY`). Create this file from the template below. Not committed.
- **`app/config/*.yml`**: Stores resource paths, CORS, and other environment-specific settings. See example files.
- **`rag_data/`**: Stores FAISS index and metadata files. Not committed.

**Required Environment Variables (.env file):**
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true

# Server Configuration
HOST=0.0.0.0
PORT=8080

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=log/app.log

# Data Paths (relative to project root)
DATA_DIR=data/
RAG_DATA_DIR=rag_data/
SUMMARY_OUTPUT_DIR=summary_outputs/

# API Configuration
MAX_TOKENS_PER_REQUEST=4000
MAX_CHUNKS_PER_QUERY=20
```

**Example: Loading API key from .env in Python**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
```

### Frontend Configuration
- **`front/.env.development`**, **`front/.env.production`**: Store API base URL and feature flags. See `front/.env.development.example` and `front/.env.production.example` for required variables.

**Example: Accessing API URL in React/Vite**
```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

---

## 🚀 Backend Setup (Flask)

### Prerequisites
- Python 3.8+
- OpenAI API key
- Sufficient disk space for regulation data

### Installation Steps
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd RegHealth-Navigator
   ```

2. **Set up environment:**
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   nano .env
   ```

3. **Configure paths:**
   ```bash
   # Copy configuration template
   cp app/config/development.yml.example app/config/development.yml
   # Edit paths if needed
   nano app/config/development.yml
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the Flask server:**
   ```bash
   export FLASK_ENV=development
   python -m app.main
   ```

---

## 📊 Data Management & Updates

### 🚀 Quick Start Guide

#### 1. Initial Setup (First Time)
```bash
# Navigate to core directory
cd app/core

# Set up environment variables
cp ../../.env.example ../../.env
# Edit .env file and add your OpenAI API key
nano ../../.env

# Configure paths
cp config/development.yml.example config/development.yml
# Edit config file if needed
nano config/development.yml

# Run initial setup
python auto_update_pipeline.py --full-auto
```

#### 2. Daily Operations
```bash
# Check system status
python incremental_pipeline.py --status

# Process new regulations (if any)
python incremental_pipeline.py --incremental

# Generate summaries for new documents
python incremental_summary.py --incremental
```

### Automated Regulation Fetching

The system includes a comprehensive automated pipeline for fetching and processing Federal Register regulations:

#### Initial Setup & Latest Updates
```bash
cd app/core
python auto_update_pipeline.py --full-auto
```

This command provides:
- **Intelligent Document Discovery**: Searches Federal Register for new regulations (1460 days lookback)
- **Automatic Classification**: Detects MPFS, HOSPICE, and SNF regulations
- **Incremental Processing**: Only processes new or modified files for cost efficiency
- **FAISS Index Updates**: Updates search indexes with new embeddings
- **Cost Tracking**: Detailed statistics on API usage and processing time
- **Comprehensive Logging**: Full audit trail of all operations

#### Manual Processing Options
```bash
cd app/core

# Process a single file
python incremental_pipeline.py --file "MPFS/new_file.xml"

# Check system status
python incremental_pipeline.py --status

# Validate system state
python incremental_pipeline.py --validate

# Clean up deleted files
python incremental_pipeline.py --cleanup
```

#### Summary Generation
Generate executive summaries for regulatory documents:

```bash
cd app/core

# Generate summary for a single file
python incremental_summary.py --files "2024_MPFS_final_2023-24184.xml"

# Generate summaries for multiple files
python incremental_summary.py --files "2024_MPFS_final_2023-24184.xml" "2023_HOSPICE_final_2022-16457.xml"

# Force regenerate existing summaries (clears cache and regenerates)
python incremental_summary.py --files "2024_MPFS_final_2023-24184.xml" --force

# Process all files without summaries (incremental)
python incremental_summary.py --incremental
```
