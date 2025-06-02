# 🏥 RegHealth Navigator 2

**Authors:**  
Xiao Yan  
Dhruv Tangri  
Sarvesh Siras  
Saicharan Emmadi  
Seon Young Jhang  
Fanxing Bu  

**Last Updated:** 27 May 2025  
**Status:** 🚧 Draft  

[![Capstone Project](https://img.shields.io/badge/CMU-Capstone%20Project-red)](https://www.cmu.edu/)

This repository is the **Summer 2025 CMU Capstone** project, continuing the work from **Spring 2025** ([GitHub Repo](https://github.com/PaulHuatingSun/RegHealth-Navigator)). The project aims to:

---

RegHealth Navigator is an intelligent regulatory document analysis platform designed to facilitate efficient understanding and analysis of complex healthcare regulatory policies. The system supports large-scale XML document partitioning, semantic retrieval, question answering, and visualization.

## Project Purpose

- Enable healthcare, compliance, and policy professionals to efficiently interpret and track U.S. federal regulatory content.
- Provide structured parsing, section-based summarization, semantic search, question answering, comparison, and mind map visualization for large XML rule documents.
- Support local caching and high-performance retrieval for multi-turn interactive analysis.

## System Architecture

- **Frontend:** React 18, TypeScript, Tailwind CSS, Vite. Implements a three-column SPA interface for file selection, section operations, semantic Q&A, and visualization.
- **Backend:** FastAPI (Python 3.8+). Handles XML partitioning, chunking, embedding generation, vector retrieval, and LLM orchestration.
- **Static Site Deployment:** The frontend is built and deployed to GitHub Pages via GitHub Actions.
- **Backend Exposure:** Cloudflare Tunnel or frp is recommended to securely expose the FastAPI backend for API access by the frontend.

## Technical Workflow

1. **Document Ingestion:** Regulatory XML documents are ingested from the Federal Register or uploaded by users (≤ 200 MB). Documents are stored in a central repository.
2. **XML Partitioning:** Large XML files are automatically partitioned into logical sections (e.g., "Medicare Physician Fee Schedule").
3. **Chunking:** Each section is split into manageable text chunks for embedding and retrieval.
4. **Embedding & Indexing:** Chunks are embedded (e.g., via OpenAI API) and stored in a vector database with section and location metadata.
5. **Section-Level Operations:** All LLM-based features (Q&A, summarization, comparison) operate at the section level to optimize context and performance.
6. **API & Frontend:** The backend API and frontend support section selection and section-level operations. Users can select a section for Q&A, summary, or comparison.
7. **Caching:** Derived artifacts (summaries, embeddings, mind maps) are cached for efficient reuse.

## Recent Changes

- Added GitHub Actions workflow for automated frontend build and deployment to GitHub Pages.
- Updated Pages configuration to support static frontend and decoupled backend API deployment.
- Node.js version is set to 18 (see `.nvmrc`).

## Environment Requirements

- Node.js 18 (see `.nvmrc`)
- Python 3.8+
- npm
- Recommended: Cloudflare Tunnel or frp for backend exposure

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/RegHealth-Navigator.git
   cd RegHealth-Navigator
   ```
2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd front
   nvm use # Ensure Node.js 18 is active
   npm install
   ```
4. Start the backend:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Start the frontend:
   ```bash
   npm run dev
   ```
6. Access the application at [http://localhost:5173](http://localhost:5173)

## Deployment

### Frontend (Static Site)
- On push to the main or dev branch, GitHub Actions automatically builds the frontend and deploys the contents of `front/dist` to the `gh-pages` branch.
- In the repository Settings > Pages, set Source to "GitHub Actions".
- The deployed site is available at `https://<your-username>.github.io/RegHealth-Navigator/`.

### Backend (API Service)
- Deploy the FastAPI backend to a server or cloud platform supporting Python 3.8+.
- Use Cloudflare Tunnel or frp to securely expose the backend API endpoint to the public internet.
- Configure the frontend to use the public API endpoint for all backend requests.

## Repository Structure

```
RegHealth-Navigator/
├── app/                # FastAPI backend application
├── core/               # Core business logic
├── front/              # React frontend application
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── context/     # React context
│   │   └── store/       # State management
├── data/               # Data files
├── docs/               # Documentation
└── scripts/            # Utility scripts
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Features

- 🔄 **Real-time Regulation Updates & Parsing**: Continuously monitors and ingests newly published U.S. federal healthcare regulations (e.g., from Federal Register) in XML format and parses them into logical sections.
- 🧠 **Semantic Search & Question Answering**: Enables users to perform semantic queries and section-specific Q&A using LLMs integrated with vector retrieval.
- 📑 **Section-based Summarization**: Automatically summarizes selected regulatory sections with citations and metadata.
- 🔄 **Version Comparison**: Allows side-by-side comparison of similar sections across different regulatory versions.
- 🗺️ **Mind Map Visualization**: Generates interactive mind maps to visualize document structure and relationships between sections.
- ⚡ **Local Caching for Performance**: Caches derived artifacts like embeddings, summaries, and visualizations to support fast, repeated access.
- 🧩 **Frontend-Backend Integration**: SPA frontend interacts with FastAPI backend through a modular API interface supporting section-level operations.

## Tech Stack

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Vite
- React Query
- React Router

### Backend
- FastAPI
- Python 3.8+
- XML processing libraries
- Vector database
- LLM integration

## Development Guidelines

### Code Style
- Use ESLint and Prettier
- Enforce TypeScript strict mode
- Use Python type hints
- Write unit tests

### Commit Convention
Commit message format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Code style (formatting)
- refactor: Code refactoring
- test: Adding tests
- chore: Build process or tooling changes

## Contribution Guide

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Contact

- Project Maintainers: Xiao Yan, Dhruv Tangri, Sarvesh Siras, Saicharan Emmadi, Seon Young Jhang, Fanxing Bu
- Repository: [https://github.com/LoadingBFX/RegHealth-Navigator](https://github.com/LoadingBFX/RegHealth-Navigator)