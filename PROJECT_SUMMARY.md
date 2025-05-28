# Project Changelog & Discussion Summary

---

## 2024-06-09 — v0.2

### Summary of Changes
- Refactored backend and workflow to support **section-based processing** for large XML files (partition, chunk, embed, section-level LLM operations)
- Updated PRD and team instructions to reflect new architecture
- Added/updated modules:
  - `core/xml_partition.py`: Partition XML into logical sections
  - `core/xml_chunker.py`: Chunk each section
  - `core/embedding.py`: Embedding and storage for section chunks
  - `core/llm.py`: Section-level LLM summarization, Q&A, comparison
- Improved API and frontend design for section selection and section-level operations

### Technical Decisions
- All LLM-based features (Q&A, summarization, comparison) now operate at the **section level** to avoid LLM context overflow and improve performance
- Rationale: Handles very large documents efficiently (scalable to >300MB, >1000 pages), avoids LLM context window limitations, enables future expansion

### User–Assistant Discussion Highlights
- User clarified the need for section-based processing due to document size and LLM limits
- Assistant proposed and implemented partition–chunk–embed–section-level LLM workflow
- Both agreed on API and frontend supporting section selection and section-level operations

---

## 2024-06-07 — v0.1

### Summary of Changes
- Initial project scaffold: frontend (React), backend (FastAPI), scripts, and basic core modules
- Basic XML chunking and whole-document embedding/LLM workflow
- Initial PRD and team instructions

### Technical Decisions
- Started with whole-document chunking and LLM operations
- No section-based processing; scalability and LLM context not yet addressed

### User–Assistant Discussion Highlights
- User requested a fullstack scaffold and best practices
- Assistant provided initial codebase and documentation

--- 