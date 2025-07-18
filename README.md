# 🏥 RegHealth Navigator

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

## 📚 Documentation

### Core Documentation
- **[System Architecture Design](docs/System%20architecture%20design.md)**: High-level system design and architecture
- **[Product Requirements Document](docs/PRD.md)**: Detailed product requirements and specifications
- **[Incremental Processing Guide](docs/incremental_processing_guide.md)**: Guide to incremental processing system
- **[Search and QA Logic](docs/search_and_qa_logic.md)**: Search functionality and Q&A system documentation

### Implementation Guides
- **[Chat Filter Implementation](docs/CHAT_FILTER_IMPLEMENTATION.md)**: Chat filtering system implementation
- **[Summary Implementation](docs/summary_implement.md)**: Document summarization implementation
- **[Federal Register Integration](docs/federal_register.md)**: Federal Register API integration details

### Deployment & Operations
- **[Local Backend + GitHub Pages Setup](docs/local_backend_github_pages_setup.md)**: Complete deployment guide using ngrok
- **[GitHub Workflow Instructions](docs/github_workflow_instruction.md)**: CI/CD pipeline documentation
- **[GitHub Actions Instructions](docs/github_action_instruction.md)**: Automated deployment setup

### Development Guides
- **[Comparison UI Optimization](docs/comparison-ui-optimization.md)**: Frontend optimization strategies
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

- **Q: rag_data path error?**
  - A: Verify `app/config/development.yml` has correct paths and `rag_data/` directory exists.

- **Q: Frontend cannot connect to backend?**
  - A: Check `VITE_API_BASE_URL` in frontend env file and CORS settings in backend config.

- **Q: Regulation fetching fails?**
  - A: Check internet connection and Federal Register API availability. Verify API rate limits.

- **Q: FAISS index corruption?**
  - A: Run `python incremental_pipeline.py --validate` to check system state and rebuild if needed.

### Performance Optimization
- **Cost Efficiency**: Use incremental processing to minimize API costs
- **Processing Speed**: Monitor logs for performance bottlenecks
- **Storage Management**: Regularly clean up old logs and temporary files

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- **Federal Register**: For providing comprehensive regulation data
- **OpenAI**: For AI capabilities and API services
- **CMU Capstone Program**: For academic guidance and support
- **All Contributors**: For their dedication to improving healthcare regulation accessibility

---

## 📊 Project Status

**Current Development Phase:** Active Development
**Last Major Update:** March 2025
**Next Milestone:** Production deployment and user testing

**Key Metrics:**
- ✅ Comprehensive documentation completed
- ✅ Automated regulation fetching implemented
- ✅ Incremental processing system operational
- ✅ Frontend-backend integration complete
- 🚧 Production deployment in progress
- 🚧 User testing and feedback collection
