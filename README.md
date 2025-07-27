# 🏥 RegHealth Navigator

**A collaboration between Carnegie Mellon University (CMU) and [Simply Compliance Consulting](https://www.simplycomplianceconsulting.com/)**

**Authors:**  
Seon Young Jhang, Daisy Yan, Fanxing Bu, Dhruv Tangri, Sarvesh Siras, Saicharan Emmadi

**Last Updated:** Jul 2025
**Status:** 🚀 Pre-release v0.7

[![Capstone Project](https://img.shields.io/badge/CMU-Capstone%20Project-red)](https://www.cmu.edu/)

---

## 📖 Project Introduction

RegHealth Navigator is an intelligent regulatory document analysis platform designed to help healthcare professionals, compliance officers, and policy analysts efficiently understand and analyze complex Medicare regulations. The system provides powerful tools for document comparison, semantic search, and AI-powered analysis with comprehensive documentation and maintainable code structure.

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
- **`.env`**: Stores sensitive information (e.g., `OPENAI_API_KEY`). Not committed. See `.env.example` for template.
- **`app/config/*.yml`**: Stores resource paths, CORS, and other environment-specific settings. See example files.
- **`rag_data/`**: Stores FAISS index and metadata files. Not committed.

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

#### 🔧 Advanced Summary Operations
```bash
# Check summary status for all files
python incremental_summary.py --status

# Generate summaries for specific program types
python incremental_summary.py --files "2024_MPFS_*.xml"  # All MPFS 2024 files
python incremental_summary.py --files "*_HOSPICE_*.xml"   # All Hospice files

# Force regenerate all summaries (use with caution - expensive)
python incremental_summary.py --incremental --force

# Check batch cache status
ls -la ../../summary_outputs/batch_cache/
```

#### MPFS-Specific Summary Generation
Generate summaries for MPFS documents only:

```bash
cd app/core

# Check MPFS summary status
python mpfs_summary_generator.py --status

# Generate summaries for all MPFS files (incremental)
python mpfs_summary_generator.py --incremental

# Generate summaries for specific MPFS files
python mpfs_summary_generator.py --files "2024_MPFS_final_2023-24184.xml" "2023_MPFS_final_2022-23873.xml"

# Force regenerate all MPFS summaries
python mpfs_summary_generator.py --incremental --force
```

**API Usage:**
```bash
# Get available summaries
curl -X GET http://localhost:8080/api/available-summaries

# Get specific summary
curl -X POST http://localhost:8080/api/get-summary \
  -H 'Content-Type: application/json' \
  -d '{"doc_name": "2024_MPFS_final_2023-24184"}'
```

**Frontend Usage:**
- Navigate to the **Summary** tab in the web interface
- Browse available summaries by program type and year
- Click on any document to view its detailed summary
- Download or copy summary content as needed

#### Scheduled Updates
For production environments, automated scheduled updates:
```bash
cd app/core
python scheduled_updater.py
```

### Data Organization
Regulations are automatically organized by program type:
- **MPFS/**: Medicare Physician Fee Schedule documents
- **HOSPICE/**: Hospice payment regulations  
- **SNF/**: Skilled Nursing Facility regulations

Each file follows the naming convention: `YYYY_PROGRAM_TYPE_DOC_TYPE_DOC_NUMBER.xml`

### Summary Files Organization
Generated summaries are stored in the `summary_outputs/` directory:
- **Markdown files**: `YYYY_PROGRAM_TYPE_DOC_TYPE_DOC_NUMBER.md` - Human-readable summaries
- **JSON files**: `YYYY_PROGRAM_TYPE_DOC_TYPE_DOC_NUMBER.json` - Structured data for processing
- **Batch cache**: `batch_cache/YYYY_PROGRAM_TYPE_DOC_TYPE_DOC_NUMBER/` - Cached batch results for cost optimization

---

## 🚀 Frontend Setup

### Prerequisites
- Node.js 18.x (recommended for best compatibility)

### Installation Steps
1. **Switch to Node.js 18 (if using nvm):**
   ```bash
   nvm use 18
   ```

2. **Configure environment:**
   ```bash
   cd front
   cp .env.development.example .env.development
   # Edit .env.development and set backend API URL
   nano .env.development
   ```

3. **Install dependencies and start:**
   ```bash
   npm install
   npm run dev
   ```

---

## 📋 Quick Reference

### 🚀 Essential Commands
```bash
# Start backend
cd app && python -m app.main

# Start frontend  
cd front && npm run dev

# Check system status
cd app/core && python incremental_pipeline.py --status

# Generate summaries
cd app/core && python incremental_summary.py --incremental

# Force regenerate summary
cd app/core && python incremental_summary.py --files "FILENAME.xml" --force
```

### 📁 Key Directories
- `data/` - Raw regulation XML files
- `rag_data/` - FAISS index and embeddings
- `summary_outputs/` - Generated summaries and cache
- `log/` - Application logs
- `app/config/` - Configuration files

### 🔧 Configuration Files
- `.env` - API keys and sensitive data
- `app/config/development.yml` - Backend configuration
- `front/.env.development` - Frontend configuration

---

## 📚 Documentation
- **[System Architecture Design](docs/System%20architecture%20design.md)**: High-level system design, data flow, backend/frontend architecture, and technical components.
- **[Product Requirements Document (PRD)](docs/PRD.md)**: Product vision, user personas, technical workflow, MVP scope, and milestones.
- **[Incremental Processing Guide](docs/incremental_processing_guide.md)**: How to use the incremental processing system for efficient document updates and FAISS index management.
- **[Search and QA Logic](docs/search_and_qa_logic.md)**: Backend search and Q&A engine, retrieval logic, and API flow.

### Implementation Guides
- **[Chat Filter Implementation](docs/CHAT_FILTER_IMPLEMENTATION.md)**: Implementation of document filtering in chat, including backend, search, and frontend integration.
- **[Summary Implementation](docs/summary_implement.md)**: Summary generation pipeline, incremental summary processing, and frontend-backend coordination.
- **[Federal Register Integration](docs/federal_register.md)**: Details on fetching, classifying, and organizing regulations from the Federal Register API.
- **[Processing Flow Diagram](docs/processing_flow_diagram.md)**: Complete visual flow of download, chunking, embedding, and summary generation processes.

### Deployment & Operations
- **[Local Backend + GitHub Pages Setup](docs/local_backend_github_pages_setup.md)**: Step-by-step deployment guide using ngrok and GitHub Pages.
- **[GitHub Workflow Instructions](docs/github_workflow_instruction.md)**: Collaborative development workflow, branching, PRs, and CI/CD best practices.
- **[GitHub Actions Instructions](docs/github_action_instruction.md)**: How to use GitHub Actions for automated deployment and CI/CD.
- **[GITHUB_WORKFLOW](docs/GITHUB_WORKFLOW.md)**: (Duplicate of workflow guide for reference.)

### Development Guides
- **[Comparison UI Optimization](docs/comparison-ui-optimization.md)**: Frontend UI/UX optimization for document comparison, user feedback, and technical rationale.
- **[Incremental Processing Guide](docs/incremental_processing_guide.md)**: Development guide for incremental processing

---

## 🌐 Deployment Guide

For detailed deployment instructions, see:
- **[Local Backend + GitHub Pages Setup](docs/local_backend_github_pages_setup.md)** - Complete step-by-step guide using ngrok
- **[GitHub Workflow Instructions](docs/github_workflow_instruction.md)** - CI/CD pipeline setup
- **[GitHub Actions Instructions](docs/github_action_instruction.md)** - Automated deployment configuration

---

## 🤝 Team Collaboration & Best Practices

### Code Quality Standards
- **Comprehensive Documentation**: All core files include detailed header comments with functionality, process flow, and author attribution
- **Unit Testing**: Every function includes unit tests for reliability
- **Error Handling**: Comprehensive error handling with detailed logging
- **Type Hints**: Full type annotation for better code maintainability

### Security & Configuration
- **Environment Variables**: Sensitive data managed via `.env` files (never committed)
- **Configuration Files**: Resource paths and settings in YAML config files
- **Git Ignore**: Proper `.gitignore` to exclude sensitive and generated files

### Development Workflow
- **Incremental Development**: Break down large tasks into manageable steps
- **Version Control**: Frequent commits with clear messages
- **Code Review**: Review significant changes before merging
- **Documentation Updates**: Update documentation when modifying functionality

---

## ❓ FAQ / Troubleshooting

### Common Issues
- **Q: API key not set error?**
  - A: Check your `.env` file and ensure `OPENAI_API_KEY` is set without extra spaces.
  ```bash
  # Verify API key is loaded
  cd app/core
  python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
  ```

- **Q: rag_data path error?**
  - A: Verify `app/config/development.yml` has correct paths and `rag_data/` directory exists.
  ```bash
  # Check config and paths
  cat app/config/development.yml
  ls -la rag_data/
  ```

- **Q: Frontend cannot connect to backend?**
  - A: Check `VITE_API_BASE_URL` in frontend env file and CORS settings in backend config.
  ```bash
  # Check frontend config
  cat front/.env.development
  # Check backend CORS settings
  cat app/config/development.yml | grep -i cors
  ```

- **Q: Regulation fetching fails?**
  - A: Check internet connection and Federal Register API availability. Verify API rate limits.
  ```bash
  # Test Federal Register API
  curl -s "https://www.federalregister.gov/api/v1/documents.json?per_page=1" | head -20
  ```

- **Q: FAISS index corruption?**
  - A: Run `python incremental_pipeline.py --validate` to check system state and rebuild if needed.
  ```bash
  # Validate system state
  cd app/core
  python incremental_pipeline.py --validate
  
  # If validation fails, rebuild FAISS index
  python incremental_pipeline.py --rebuild-index
  ```

- **Q: Summary generation fails or uses old cache?**
  - A: Use `--force` flag to clear cache and regenerate summaries.
  ```bash
  # Force regenerate specific summary
  python incremental_summary.py --files "2024_MPFS_final_2023-24184.xml" --force
  
  # Clear all batch cache manually
  rm -rf ../../summary_outputs/batch_cache/
  ```

- **Q: High API costs during summary generation?**
  - A: Use incremental processing and monitor batch cache usage.
  ```bash
  # Check batch cache size
  du -sh ../../summary_outputs/batch_cache/
  
  # Use incremental processing only
  python incremental_summary.py --incremental
  ```

### Performance Optimization
- **Cost Efficiency**: Use incremental processing to minimize API costs
- **Processing Speed**: Monitor logs for performance bottlenecks
- **Storage Management**: Regularly clean up old logs and temporary files

### 🔍 System Monitoring & Maintenance

#### Daily Health Checks
```bash
# Check system status
cd app/core
python incremental_pipeline.py --status

# Check summary status
python incremental_summary.py --status

# Monitor disk usage
du -sh rag_data/ summary_outputs/ data/

# Check log files
tail -f ../../log/app.log
```

#### Weekly Maintenance
```bash
# Clean up old logs
find ../../log/ -name "*.log" -mtime +7 -delete

# Check for orphaned files
python incremental_pipeline.py --cleanup

# Validate system integrity
python incremental_pipeline.py --validate

# Monitor API usage costs
grep "API cost" ../../log/app.log | tail -20
```

#### Monthly Tasks
```bash
# Backup important data
tar -czf backup_$(date +%Y%m%d).tar.gz rag_data/ summary_outputs/

# Update system dependencies
pip install -r requirements.txt --upgrade

# Review and clean old summary outputs
ls -la ../../summary_outputs/ | grep -E "202[0-2]"
```

---

## 📝 License
- This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
- **Copyright © Carnegie Mellon University (CMU) and Simply Compliance Consulting ([https://www.simplycomplianceconsulting.com/](https://www.simplycomplianceconsulting.com/)), 2024. All rights reserved.**

---

## 🚧 Next Steps

The following features and improvements are planned for upcoming releases. These are informed by the product requirements, architecture docs, and user feedback:

### 1. User Authentication & Login Interface
- Implement a secure login page for user authentication.
- Support for role-based access control (future: admin, analyst, guest).

### 2. History & Session Management
- Add a persistent history panel to let users review past queries, summaries, and comparisons.
- Enable search/filtering of previous sessions and document interactions.

### 3. LLM API Configuration Switching
- UI and backend support for switching between different LLM providers (e.g., OpenAI, local models).
- Allow users/admins to select or configure the embedding and completion model in the dashboard.

### 4. Dashboard & Analytics
- Develop a dashboard for:
  - System status and update history (e.g., last regulation fetch, processing stats).
  - Usage analytics (e.g., most queried documents, API usage, cost tracking).
  - Quality and latency benchmarking (especially for Hospice/SNF pipeline stabilization).

### 5. Feedback Mechanism
- Add a user feedback widget for reporting issues, rating answers, and suggesting improvements.
- Integrate feedback into the admin dashboard for review and triage.

### 6. Comparison UI & Direct Linking
- Enhance the document comparison interface:
  - Direct links to source documents and sections.
  - Improved section matching and visualization.
  - Export comparison results as PDF.

### 7. Advanced Document Navigation
- Interactive mind-map view for visual navigation across regulations and cross-references.
- Document preview before selection.
- Smart document suggestions based on user queries.

### 8. Automated & Incremental Updates
- Fully automate regulation fetching and processing via scheduled jobs.
- Improve monitoring, logging, and error notifications for update pipelines.

### 9. Accessibility & Internationalization
- Ensure full WCAG 2.1 AA compliance.
- Add ARIA labels and support for non-English characters.

### 10. Other Planned Enhancements
- Batch operations for document selection.
- Grouping and categorization of documents.
- Corpus-wide Q&A (cross-document search when no file is selected).
- Product management assistant tools (risk flagging, milestone reminders).

---

**For more details, see:**
- [Product Requirements Document (PRD)](docs/PRD.md)
- [System Architecture Design](docs/System%20architecture%20design.md)
- [Comparison UI Optimization](docs/comparison-ui-optimization.md)
- [Chat Filter Implementation](docs/CHAT_FILTER_IMPLEMENTATION.md)
- [Incremental Processing Guide](docs/incremental_processing_guide.md)
- [Summary Implementation](docs/summary_implement.md)

---

**Contributions and feedback are welcome!**  
If you have suggestions or want to help with any of these next steps, please open an issue or pull request.
