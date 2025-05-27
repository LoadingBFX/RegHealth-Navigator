# RegHealth MVP – Product Requirements Document  
**Author:** [Your Name]  
**Last Updated:** 27 May 2025  
**Status:** Draft  

---

## 1. Purpose & Vision  
Professionals who track regulatory or standards‑driven content (e.g., health‑tech, pharma, clinical research) waste hours opening dense XML documents, skimming for relevant changes, and re‑summarising them for colleagues. **RegHealth** turns any XML bundle into an *actionable knowledge notebook*: an always‑visible chat space paired with living summaries, mind‑maps, and change‑tracking—everything cached locally for speed, while the canonical XML lives on the server.

---

## 2. Goals & Success Metrics  

| Goal | Measure of Success | Target (MVP) |
| ---- | ----------------- | ------------- |
| Faster comprehension of large XML | Avg. time from upload / selection to first summary ready | ≤ 90 s on 200 MB (≈1 000 pages) file |
| Trusted answers | % of answers containing ≥1 inline citation | ≥ 95 % |
| Continuous use | Median chat turns per session | ≥ 8 |
| Re‑use of cached artefacts | Cache hit rate on repeat file selections | ≥ 80 % |
| High unit‑test coverage | `core/` modules | ≥ 90 % |

---

## 3. Personas & Core Jobs  

| Persona | Job‑to‑be‑Done | Pain Today | Desired Outcome |
| ------- | -------------- | ---------- | --------------- |
| **Regulatory Analyst Alice** | “Spot what changed between two guideline releases.” | Manual red‑line diffing, copy/paste into Word. | One‑click trend/comparison view with citations. |
| **Medical Writer Ben** | “Extract sections relevant to device safety.” | Endless scrolling, missed updates. | Ask in chat → get paragraph plus source id. |
| **Quality Lead Carla** | “Produce weekly summaries for execs.” | Writing recap emails from scratch. | Export mind‑map + bullet summary in seconds. |

---

## 4. Scope (MVP)  

### 4.1 Functional Requirements  
1. **Server‑side XML repository**  
   * Primary flow: user searches and selects XML already in the central library.  
   * Secondary (lower‑priority) flow: user uploads a private XML file (≤ 200 MB); stored in object storage, processed with same pipeline.  
2. **High‑volume ingestion**  
   * Stream‑based parser and chunker must handle **≥ 200 MB** XML without loading the whole file into RAM.  
   * Pre‑processing runs as asynchronous server job; UI shows progress and auto‑refreshes when ready.  
3. **Interactive mind‑map**  
   * Auto‑expand top nodes; click node → display source paragraph.  
4. **Summaries with source‑aware notes**  
   * Bullet list per section, each bullet links back (e.g. `§1.2`).  
5. **Contextual Q&A chat**  
   * Multi‑turn; answers show inline citations; memory resets on demand.  
6. **Document comparison**  
   * Select ≥ 2 files → ask aspect (e.g., “dosage changes”) → receive diff summary.  
7. **History & caching**  
   * Derived artefacts (summaries, embeddings, mind‑maps) cached in Redis + disk; keyed by server file ID.  
8. **NotebookLM‑style three‑column UI**  
   * **Left:** files & history. **Center:** persistent chat. **Right:** actions/results.  

### 4.2 Non‑Functional Requirements  

| Category | Requirement |
| -------- | ----------- |
| Performance | **Server ingest:** ≤ 90 s to parse, chunk, embed and cache a 200 MB / 1 000‑page XML on a 4‑core node; subsequent queries ≤ 3 s. |
| Storage | XML files stored in central S3‑compatible bucket with versioning; derived artefacts cached locally. |
| Usability | All primary actions reachable in ≤ 2 clicks; keyboard shortcut to focus chat (⌘/Ctrl + K). |
| Reliability | Graceful error messages; autosave chat state every 5 s. |
| Security | Role‑based ACL on library XML; private uploads default to owner‑only; redact XML attributes labelled “PII”. |
| Internationalisation | UTF‑8 throughout; token estimates accurate for CJK characters. |
| Accessibility | WCAG 2.1 AA colours; ARIA labels on mind‑map nodes. |

### 4.3 Out of Scope (MVP)  
* Real‑time multi‑user collaboration  
* Non‑XML formats (PDF, HTML)  
* Fully offline LLM (will rely on OpenAI gpt‑4o via LangChain wrapper)  

---

## 5. User Journey (Happy Path)  

1. **Select / Upload File(s)** → XML added to processing queue.  
2. **Generate Summary** (Right sidebar) → bullet list & mind‑map appear; cached for future sessions.  
3. **Ask Follow‑up** (“What are new safety requirements?”) → grounded answer with `[§3.2]` references.  
4. **Compare** previous vs. new XML → diff summary; user scrolls chat while results stay in Right column.  
5. **Return next week**; cached artefacts load instantly.  

---

## 6. Detailed Requirements Traceability  

| Epic / Feature | Key Modules | Acceptance Criteria |
| -------------- | ----------- | ------------------- |
| **XML Parser** | `xml_parser.py` | Streams 200 MB file with < 500 MB peak RAM; passes test suite. |
| **Mind‑map Renderer** | `mindmap_builder.py`, Streamlit component | Markdown → Markmap renders; special chars escaped. |
| **Vector Index & Retrieval** | `index_builder.py`, `retriever.py` | Top‑3 chunks contain ≥1 query keyword in 90 % of tests. |
| **Summariser** | `summarizer.py` | Summary ≤ 30 % original tokens; ≥ 80 % ROUGE‑1 vs. human baseline. |
| **Chat Engine** | `chat_engine.py` | Memory remembers entities across 5 turns; `reset` clears state. |
| **Caching & History** | Redis / disk | Cached artefacts keyed by file ID; load ≤ 2 s. |
| **UI Shell** | `app/main.py` | 3‑column layout stable ≥ 1280 px; responsive down to 1024 px. |

---

## 7. Milestones & Timeline (8 Weeks)  

| Week | Deliverable | Owner | Exit Criteria |
| ---- | ----------- | ----- | ------------- |
| 1 | Repo scaffold, Streamlit hello world | FE Lead | App runs; placeholder 3‑column layout. |
| 2 | XML parser + tests | Backend Lead | CI passes; coverage > 90 %. |
| 3 | Mind‑map component | FE Lead | Renders static markdown demo file. |
| 4 | FAISS index & retrieval | Backend Lead | `get_relevant_chunks` returns sensible top‑3. |
| 5 | Q&A pipeline | AI Lead | Chat answers with citations on sample XML. |
| 6 | Summariser UI | AI & FE | Summary + mind‑map linked; click bullet reveals source. |
| 7 | Stateful chat & comparison | AI Lead | 5‑turn chat demo; diff summary across two docs. |
| 8 | Final polish, Docker, E2E tests | All | One‑command Docker up; 5 scripted E2E tests pass. |

---

## 8. Risks & Mitigations  

| Risk | Likelihood | Impact | Mitigation |
| ---- | ---------- | ------ | ---------- |
| OpenAI rate limits slow summarisation | Medium | High | Batch embeddings; exponential back‑off; optional local model toggle. |
| 200 MB uploads saturate embedding quota | Medium | High | Chunk in 1 000‑token windows; queue jobs with concurrency limits. |
| Long ingest time frustrates users | Medium | Medium | Background job + progress bar; e‑mail/UI notification on completion. |
| Citation drift from LLM hallucinations | Medium | High | Grounded retrieval prompt; highlight low‑similarity answers for review. |
| Mind‑map JS fails in older browsers | Low | Medium | Fallback to outline view. |

---

## 9. Open Questions  

1. What is the maximum expected XML size beyond 200 MB, and do we need sharding?  
2. Do private uploads count against a per‑organisation storage quota?  
3. Which regulatory domains (FDA, EMA, etc.) will seed demo content?  

---

## 10. Appendix  

* **Glossary:**  
  * **RAG** – Retrieval‑Augmented Generation  
  * **FAISS** – Facebook AI Similarity Search  
* **Relevant Docs:** Architectural Decision Records ADR‑001 – ADR‑005 (link forthcoming)  

