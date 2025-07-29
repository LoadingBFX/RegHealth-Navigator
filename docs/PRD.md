# RegHealth MVP – Product Requirements Document

**Author:** \[Your Name\]  
**Last Updated:** 27 May 2025  
**Status:** Draft

---

## 0\. Background (Updated 2025‑06‑02)

* A **previous engineering team** delivered a first‑pass ingestion & retrieval pipeline covering **Hospice Quality Reporting Program (HQRP)** and **Skilled Nursing Facility (SNF)** final & proposed rules.  
    
  * Early tests show the pipeline basically works, but **answer quality and latency are still unverified**.  
  * We will **migrate their codebase and data into this project**, but stabilization is a **P2 backlog item** (target: Q4 2025).


* The **current project (Phase 2)** will **prioritize Medicare Physician Fee Schedule (MPFS)** and **Quality Payment Program (QPP)** regulations because:  
    
  1. They are updated annually and have the **broadest financial impact** on providers.  
  2. Internal stakeholders need payment‑rate diffs and QPP measure mapping **before the next CY rule cycle** (deadline: CY 2026 Proposed Rule, expected July 2025).  
  3. MPFS/QPP content structure is representative enough to design a **generic, rule‑agnostic ingestion pipeline**.


* **Compatibility**:  
    
  * All new components (document schema, retriever logic, embeddings) must be **rule‑type agnostic** so Hospice/SNF and any future rule families (e.g., IPPS, OPPS) can be plugged in with minimal effort.  
  * Feature priority: **P0 = MPFS/QPP accuracy & latency**, **P1 = cross‑rule corpus Q\&A**, **P2 = Hospice/SNF stabilization**.


* **Personas / Use‑cases impact**:  
    
  * Regulatory analysts who cover Hospice/SNF will continue to use the migrated v1 flow; improvements will arrive once MPFS/QPP is stable.  
  * Policy researchers now get **premium support for MPFS/QPP** use‑cases like trend graphs and auto‑alerts.  
  * The compliance chat will transparently surface which rule family is being referenced in every answer.

---

## 1\. Purpose & Vision

Professionals who track regulatory or standards‑driven content (e.g., health‑tech, pharma, clinical research) waste hours opening dense XML documents, skimming for relevant changes, and re‑summarising them for colleagues. **RegHealth** turns any XML bundle into an *actionable knowledge notebook*: an always‑visible chat space paired with living summaries, mind‑maps, and change‑tracking—everything cached locally for speed, while the canonical XML lives on the server.

---

## 2\. Technical Workflow Update (2024-06)

### Large XML Handling & Chunk-Based Processing

- **XML Parsing:** Large XML files (often \>300MB, \>1000 pages) are parsed to extract regulatory content from `<SUPLINF>` and `<REGTEXT>` sections.
- **Chunking:** Content is split into manageable text chunks (500 words with 1 sentence overlap) for embedding and retrieval.
- **Embedding & Storage:** Chunks are embedded (e.g., via OpenAI API) and stored in a vector database (FAISS), with metadata for source file and location.
- **Chunk-Level Operations:** All LLM-based features (Q\&A, summarization, comparison) operate at the chunk level to ensure performance and manage API costs.
- **API & Frontend:** Backend API and frontend are designed to support document selection and chunk-level operations. Users can select documents for Q\&A, summary, or comparison.
- **Rationale:**  
  - Enables handling of very large documents without exceeding LLM context limits.  
  - Improves performance and scalability by processing manageable chunks.
  - Provides cost-effective processing through incremental updates and caching.

### Core Backend Modules (MVP)

- `core/xml_chunker.py`: Parse XML and create text chunks with metadata.
- `core/incremental_chunker.py`: Process new files incrementally.
- `core/incremental_faiss.py`: Update FAISS index with new embeddings.
- `core/search.py`: Chunk-level search and Q\&A operations.
- `core/summarizer.py`: Chunk-based summary generation.
- `core/compare.py`: Document comparison using chunk-level analysis.

### Extensibility

- The architecture supports future expansion to multi-document operations, as well as more advanced caching and retrieval strategies.

---

## 2\. Goals & Success Metrics

| Goal | Measure of Success | Target (MVP) |
| :---- | :---- | :---- |
| Faster comprehension of large XML | Avg. time from upload / selection to first summary ready | ≤ 90 s on 200 MB (≈1,000 pages) file |
| Trusted answers | % of answers containing ≥1 inline citation | ≥ 95 % |
| Continuous use | Median chat turns per session | ≥ 8 |
| Re‑use of cached artefacts | Cache hit rate on repeat file selections | ≥ 80 % |
| High unit‑test coverage | `core/` modules | ≥ 90 % |

---

## 3\. Personas & Core Jobs

| Persona | Job‑to‑be‑Done | Pain Today | Desired Outcome |
| :---- | :---- | :---- | :---- |
| **Regulatory Analyst Alice** | "Spot what changed between two guideline releases." | Manual red‑line diffing, copy/paste into Word. | One‑click trend/comparison view with citations. |
| **Medical Writer Ben** | "Extract sections relevant to device safety." | Endless scrolling, missed updates. | Ask in chat → get paragraph plus source id. |
| **Quality Lead Carla** | "Produce weekly summaries for execs." | Writing recap emails from scratch. | Export mind‑map \+ bullet summary in seconds. |

---

## 4\. Scope (MVP)

### 4.1 Functional Requirements

1. **Server‑side XML repository**  
   * Primary flow: user searches and selects XML already in the central library.  
   * Secondary (lower‑priority) flow: user uploads a private XML file (≤ 200 MB); stored in object storage, processed with same pipeline.  
2. **High‑volume ingestion**  
   * Stream‑based parser and chunker must handle **≥ 200 MB** XML without loading the whole file into RAM.  
   * Pre‑processing runs as asynchronous server job; UI shows progress and auto‑refreshes when ready.  
3. **Interactive mind‑map**  
   * Auto‑expand top nodes; click node → display source paragraph.  
4. **Summaries with source‑aware notes**  
   * Bullet list per section, each bullet links back (e.g. `§1.2`).  
5. **Contextual Q\&A chat**  
   * Multi‑turn; answers show inline citations; memory resets on demand.  
6. **Document comparison**  
   * Select ≥ 2 files → ask aspect (e.g., "dosage changes") → receive diff summary.  
7. **History & caching**  
   * Derived artefacts (summaries, embeddings, mind‑maps) cached in Redis \+ disk; keyed by server file ID.  
8. **Tab-based interface with modal overlays**  
   * **Top:** Tab navigation (Chat, Summary, Compare). **Center:** Main content area. **Modals:** History and citation details.

### 4.2 Non‑Functional Requirements

| Category | Requirement |
| :---- | :---- |
| Performance | **Server ingest:** ≤ 90 s to parse, chunk, embed and cache a 200 MB / 1,000‑page XML on a 4‑core node; subsequent queries ≤ 3 s. |
| Storage | XML files stored in central S3‑compatible bucket with versioning; derived artefacts cached locally. |
| Usability | All primary actions reachable in ≤ 2 clicks; keyboard shortcut to focus chat (⌘/Ctrl \+ K). |
| Reliability | Graceful error messages; autosave chat state every 5 s. |
| Security | Role‑based ACL on library XML; private uploads default to owner‑only; redact XML attributes labelled "PII". |
| Internationalisation | UTF‑8 throughout; token estimates accurate for CJK characters. |
| Accessibility | WCAG 2.1 AA colours; ARIA labels on mind‑map nodes. |

### 4.3 Out of Scope (MVP)

* Real‑time multi‑user collaboration  
* Non‑XML formats (PDF, HTML)  
* Fully offline LLM (will rely on OpenAI gpt‑4o via LangChain wrapper)

---

## 5\. User Journey (Happy Path)

1. **Access Application** → Load tab-based interface (Chat, Summary, Compare).
2. **Select Documents** (Chat tab) → Choose documents from available list for querying.
3. **Ask Questions** (Chat tab) → Input natural language questions and receive grounded answers with citations.
4. **View Summaries** (Summary tab) → Browse generated document summaries by program type and year.
5. **Compare Documents** (Compare tab) → Input comparison queries and receive detailed analysis.
6. **Return Later** → Cached content loads instantly for future sessions.

---

## 6\. Detailed Requirements Traceability

| Epic / Feature | Key Modules | Acceptance Criteria |
| :---- | :---- | :---- |
| **XML Parser** | `xml_parser.py` | Streams 200 MB file with \< 500 MB peak RAM; passes test suite. |
| **Mind‑map Renderer** | `mindmap_builder.py`, React (SPA) component | Markdown → Markmap renders; special chars escaped. |
| **Vector Index & Retrieval** | `index_builder.py`, `retriever.py` | Top‑3 chunks contain ≥1 query keyword in 90 % of tests. |
| **Summariser** | `summarizer.py` | Summary ≤ 30 % original tokens; ≥ 80 % ROUGE‑1 vs. human baseline. |
| **Chat Engine** | `chat_engine.py` | Memory remembers entities across 5 turns; `reset` clears state. |
| **Caching & History** | Redis / disk | Cached artefacts keyed by file ID; load ≤ 2 s. |
| **UI Shell** | `app/main.py` | 3‑column layout stable ≥ 1280 px; responsive down to 1024 px. |

---

## 7\. Milestones & Timeline (8 Weeks)

| Week | Deliverable | Owner | Exit Criteria |
| :---- | :---- | :---- | :---- |
| 1 | Repo scaffold, React (SPA) hello world | FE Lead | App runs; placeholder 3‑column layout. |
| 2 | XML parser \+ tests | Backend Lead | CI passes; coverage \> 90 %. |
| 3 | Mind‑map component | FE Lead | Renders static markdown demo file. |
| 4 | FAISS index & retrieval | Backend Lead | `get_relevant_chunks` returns sensible top‑3. |
| 5 | Q\&A pipeline | AI Lead | Chat answers with citations on sample XML. |
| 6 | Summariser UI | AI & FE | Summary \+ mind‑map linked; click bullet reveals source. |
| 7 | Stateful chat & comparison | AI Lead | 5‑turn chat demo; diff summary across two docs. |
| 8 | Final polish, Docker, E2E tests | All | One‑command Docker up; 5 scripted E2E tests pass. |

---

## 8\. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
| :---- | :---- | :---- | :---- |
| OpenAI rate limits slow summarisation | Medium | High | Batch embeddings; exponential back‑off; optional local model toggle. |
| 200 MB uploads saturate embedding quota | Medium | High | Chunk in 1,000‑token windows; queue jobs with concurrency limits. |
| Long ingest time frustrates users | Medium | Medium | Background job \+ progress bar; e‑mail/UI notification on completion. |
| Citation drift from LLM hallucinations | Medium | High | Grounded retrieval prompt; highlight low‑similarity answers for review. |
| Mind‑map JS fails in older browsers | Low | Medium | Fallback to outline view. |

---

## 9\. Open Questions

1. What is the maximum expected XML size beyond 200 MB, and do we need sharding?  
2. Do private uploads count against a per‑organisation storage quota?  
3. Which regulatory domains (FDA, EMA, etc.) will seed demo content?

---

## 10\. Appendix

* **Glossary:**  
  * **RAG** – Retrieval‑Augmented Generation  
  * **FAISS** – Facebook AI Similarity Search  
* **Relevant Docs:** Architectural Decision Records ADR‑001 – ADR‑005 (link forthcoming)

---

## 8\. Backlog & Non‑MVP Features

| Feature | Rationale | Priority |
| :---- | :---- | :---- |
| **Interactive Mind‑Map View** | Visual exploratory navigation across regulations, measures, and cross‑references. | P3 (post‑MVP) |
| Hospice/SNF v1 Stabilization Dashboards | Quality & latency benchmarking for migrated pipeline. | P2 |
| Auto‑PDF Render for Diff Reports | Nice‑to‑have export option. | P3 |

*Items here are not required for MVP launch and can be re‑prioritized in future sprints.*

### Frontend

- Built with **React** (SPA).  
- Deployed via **GitHub Pages**.

