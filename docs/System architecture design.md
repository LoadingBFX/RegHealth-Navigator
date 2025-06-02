# System Architecture Design

# 1\. Introduction

**RegHealth Navigator** is a compliance intelligence platform designed to assist healthcare stakeholders in understanding and operationalizing complex U.S. federal regulatory policies. Originally developed in collaboration between Simply Compliance Consulting, LLC and Carnegie Mellon University (CMU) Heinz College, the system has evolved into a production-ready tool leveraging **large language models (LLMs)** with a **retrieval-augmented generation (RAG)** architecture.

The platform ingests rule-based documents such as the **Medicare Physician Fee Schedule (MPFS)** and the **Quality Payment Program (QPP)** from the **Federal Register**, processes them into semantically searchable representations, and enables natural language question-answering, summarization, and policy comparisons.

This system architecture document outlines:

* Target user groups and regulatory use cases  
* Data ingestion and vector-based indexing strategies  
* End-to-end workflow from XML parsing to LLM orchestration  
* Deployment architecture including **FastAPI backend**, **Cloudflare Tunnel**, and **React frontend**

The intended audience includes engineers, ML developers, technical leads, and product owners involved in regulatory, compliance, and health-tech tooling.

# 2\. Target Users

RegHealth Navigator serves a broad spectrum of professionals involved in interpreting and applying U.S. healthcare regulations. Its primary users include:

* Regulatory Analysts (Hospice / SNF / MPFS / QPP)  
  Professionals responsible for translating new federal rules into internal operating procedures. They require:  
  * Fast identification of **payment-rate changes** and **quality measure updates**  
  * Accurate document diffs between Proposed and Final Rules  
  * Trusted, citation-backed answers for legal traceability

* Policy Researchers & Think Tanks  
  Stakeholders tracking long-term regulatory trends across programs such as MPFS, QPP, and IPPS. They need:  
    
  * Multi-year comparative analysis  
  * Access to semantic search across document corpus  
  * Exportable summaries and dashboards for reporting

* Compliance Officers  
  Personnel fielding day-to-day operational questions such as “When does this rule take effect?” or “Which version applies to us?”. They expect:  
  * Conversational Q\&A with clear citations  
  * Ability to retrieve effective dates, rule scope, enforcement context  
  * Fast lookup without needing to know document names or years  
      
* Product & Strategy Teams (Health SaaS / LegalTech)  
  Technical and product stakeholders who aim to embed compliance insights into internal systems or SaaS tools. They benefit from:

  * APIs for programmatic access  
  * Integration with internal workflows (e.g., quality reporting, claims)  
  * High-level summaries and structured metadata feeds

# 3\. Data

## 3.1 Data Sources

RegHealth Navigator ingests publicly available rule-based regulatory content from the [Federal Register](https://www.federalregister.gov), with a primary focus on:

* **Medicare Physician Fee Schedule (MPFS)**  
* **Quality Payment Program (QPP)**

All documents are obtained in **XML format**, either through **manual ingestion** or **automated API scraping**.

## 3.2 Data Format (Federal Register XML)

Regulatory XML documents follow a standardized structure. Key XML elements include:

| XML Element | Description | Example Content |
| :---- | :---- | :---- |
| `<RULE>` / `<PRORULE>` | Root element for final or proposed regulations | `<RULE>...</RULE>` |
| `<PREAMB>` | Preamble section containing summary and metadata | CMS, published in 2025 |
| `<AGENCY>` | Publishing federal agency | DEPARTMENT OF HEALTH AND HUMAN SERVICES |
| `<SUBAGY>` | Publishing sub-agency | Centers for Medicare & Medicaid Services |
| `<SUBJECT>` | Regulation title | Medicare Program; CY 2025 Physician Fee Schedule |
| `<SUPLINF>` | Core regulatory content (Supplementary Information) | Detailed explanation of regulatory intent and background |
| `<REGTEXT>` | Formal regulatory text (amendments, rules) | Contains changes to the Code of Federal Regulations |
| `<AMDPAR>` | Amended paragraph (regulatory change) | 1\. The authority citation for part 401 is revised... |
| `<SECTION>` | Section block under REGTEXT | Contains CFR citations and related rules |
| `<SECTNO>` | Section number of a CFR provision | § 405.2410 |
| `<AUTH>` | Legal authority for the regulation | 42 U.S.C. 1302, 1395hh |
| `<HD>` | Section header. May include a `SOURCE` attribute like `HD1`, `HD2`, `HD3` indicating heading level. If `SOURCE` is absent, hierarchy may be inferred from formatting (e.g. I., A., 1.). | I. Executive Summary, A. Purpose, 1\. Overview |
| `<P>` | Paragraph text | This final rule addresses changes to... |
| `<FP>` | Framed paragraph (e.g., bullet or list item) | • Background (section II.A.) |
| `<E>` | Embedded entity (email, URL, inline term) | [MedicarePhysicianFeeSchedule@cms.hhs.gov](mailto:MedicarePhysicianFeeSchedule@cms.hhs.gov) |
| `<FTNT>` | Footnote block | Contains citations or supplemental explanations |
| `<GPH>` | Graphical element container | Table or figure element |
| `<GID>` | Graphical element ID | ER09DE24.000 |
| `<BILCOD>` | Billing code for Federal Register document | BILLING CODE 4120-01-P |
| `<DATES>` | Regulation effective date section | These regulations are effective on January 1, 2025 |
| `<NOTE>` | Notes or appendix references | Note: The following appendices will not appear in... |
| `<PRTPAGE>` | Page number from printed Federal Register | PRTPAGE="97710" |
| `<SIG>` | Signature block | Includes NAME and TITLE of signer |
| `<NAME>` | Signer's full name | Xavier Becerra |
| `<TITLE>` | Signer's title | Secretary, Department of Health and Human Services |

These structures enable reliable programmatic parsing and downstream semantic indexing.

![][image1]

## 3.3 Data Update Cycle

Regulatory documents follow a **predictable yearly update cycle**:

* **Proposed Rule**: Published \~April–June  
* **Final Rule**: Published \~August–November, effective January 1 (following year)

Updates are currently pulled manually but will soon be automated via [Federal Register API](https://www.federalregister.gov/reader-aids/developer-resources) jobs.

## 3.4 Data Workflow

**Federal Register XML**  
Source of truth: official Medicare rules in XML format  
**Admin Download / API Crawler**  
Manual download or automated ingestion using federalregister.gov APIs  
**XML Parser & Chunker**  
Extracts and content  
Splits content into semantically meaningful chunks

**Embeddings → Vector DB**  
Converts chunks into dense vectors using OpenAI Embedding API  
Stores vectors in **FAISS** for semantic search

**RAG API Layer**  
Accepts user queries  
Retrieves relevant chunks  
Sends to LLM for response generation

**Answer / Summary / Comparison**  
Returns answer with citation  
Supports summary, FQA, policy difference views

The ingestion pipeline transforms XML into structured chunks, computes embeddings, and stores them in a **vector database** for fast retrieval via the **LLM backend**.

## 3.5 Data Security & Compliance

RegHealth Navigator enforces **strict data governance**, aligned with HIPAA and regulatory best practices:

* All ingestion and processing occur in a **controlled, auditable environment**  
* Sensitive data is separated and encrypted  
* Only public federal documents are processed; no PHI or proprietary content is ingested  
* System-level access controls protect metadata and LLM query logs

# 4\. Workflow

## 4.1 Document Retrieval & Guideline Inference

Users interact with the system via a **natural-language chat interface**.  
The system supports two primary usage modes:

* **Selected Document Mode**  
  If the user has explicitly selected a document (via UI filters), all operations (Q\&A, summary, comparison) are scoped to that file.  
* **Corpus Mode**  
  If no document is selected, the system performs:  
  * **Guideline inference** (e.g., MPFS, QPP, SNF) using a zero-shot classifier  
  * **Vector search** within relevant documents to identify matching context  
  * If ambiguity remains, it prompts a **clarifying follow-up question**

⚠️ Users are **not permitted to upload documents**. All content ingestion is handled by backend systems through **manual import** or **automated API crawling** of the Federal Register.

## 4.2 Data Ingestion & Indexing

A scheduled backend job (via **GitHub Actions** and **Cloudflare Workers**) ingests new XML documents from the **Federal Register API**.

The ingestion pipeline includes:

1. **XML parsing** to extract `<SUPLINF>` and `<REGTEXT>` sections  
2. **Chunking** into semantically coherent passages  
3. **Embedding generation** using OpenAI Embedding API  
4. **Indexing** into a **FAISS** vector store

Indexing latency is minimal; new documents are usually searchable within minutes.

## 4.3 Backend Query Flow (Intent → Prompt → Response)

Once the user’s query reaches the backend, it is processed through the following sequence:

1. **Intent Classification**  
   A zero-shot classifier determines the user’s goal:  
   `ask_fact`, `summarize_doc`, `compare_rules`, `upload_attempt`, `unknown`  
     
2. **Prompt Template Selection**  
   Based on the inferred intent, the system selects an appropriate prompt type and retrieval strategy:  
     
   - `ask_fact` → FAISS top-6 chunks → Q\&A prompt  
   - `summarize_doc` → entire document → summary prompt  
   - `compare_rules` → two document versions → comparison prompt

   

3. **Contextual Retrieval**  
   If applicable, relevant chunks are retrieved from FAISS and passed as context.  
     
4. **LLM Execution**  
   Prompt \+ context are sent to OpenAI GPT-4o to generate a grounded, citation-backed response.  
     
5. **Confidence Handling**  
   If the retriever or LLM is uncertain, the system auto-generates a clarifying follow-up.

## 4.4 Caching & Regeneration

All outputs from summarization, Q\&A, and comparisons are cached per:  
`(document_id, user_query_hash, feature_type)`

When a repeated query is detected:

- Cached results are returned immediately  
- Users may click **Regenerate** to force fresh computation and update the cache

This layer significantly improves performance and reduces OpenAI API usage across common queries.

# 5\. System Overview

RegHealth Navigator is built on a modular **Retrieval-Augmented Generation (RAG)** architecture designed for efficient, accurate, and explainable analysis of federal healthcare regulations. It includes the following core layers:  
![][image2]

## 5.1 User Interaction Layer

The frontend is built in **React**, offering a conversational interface for exploring and understanding regulations.

**Core Features:**

- **Natural-language Q\&A**  
  Ask open-ended questions about federal rules and receive grounded answers with citations.  
    
- **Program & Year Filters**  
  Select documents by program (e.g., MPFS, QPP), year, and rule type (Proposed/Final).  
    
- **Interactive Panels**  
    
  - Left: Document selection & chat history  
  - Center: Chat-based document interaction  
  - Right: Summary, FQA, and Policy Comparison tools

⚠️ No user-upload support. Documents are centrally managed by backend ingestion only.

## 5.2 Data Processing Layer

Transforms raw regulatory XML into structured, queryable formats.

**Pipeline Components:**

- **XML Parser**  
  Extracts `<SUPLINF>` and `<REGTEXT>` sections from each document.  
    
- **Chunker**  
  Splits documents into semantically meaningful sections (based on `<HD>`, `<P>`, and structure).  
    
- **Embedder**  
  Uses **OpenAI Embedding API** to convert each chunk into dense vector representations.  
    
- **Indexer**  
  Stores embeddings in **FAISS**, enabling high-performance semantic similarity search.

## 5.3 Application Logic Layer (RAG Model & Backend)

This layer governs core AI-driven capabilities and orchestrates end-to-end tasks.

**Key Responsibilities:**

- **Guideline Classification**  
  Zero-shot classifier routes user queries to relevant programs (MPFS, QPP, SNF, etc.)  
    
- **Retriever**  
  Fetches top-K matching chunks from the vector database (e.g., MMR, recency-adjusted)  
    
- **LLM Answer Generation**  
  Invokes **OpenAI GPT-4o API** to:  
    
  - Generate grounded Q\&A responses  
  - Compose executive summaries  
  - Identify and describe policy changes


- **Clarification Logic**  
  If confidence is low, the system proactively requests more details (e.g., rule year, program).

## 5.4 Data Storage & Cache Layer

Maintains structured and intermediate data to enhance speed, traceability, and cost efficiency.

### 

| Component | Description |
| :---- | :---- |
| docs/ | Raw XML documents from the Federal Register |
| chunks.json | Preprocessed text blocks with metadata |
| FAISS | Vector index for similarity search |
| summary\_cache/ | Stored summaries keyed by document ID |
| qa\_cache/ | Q\&A results keyed by hash of query and doc |
| compare\_cache/ | Cached diffs between documents |

### 

## 5.5 External Integrations

The system leverages reliable third-party APIs to enable LLM and embedding capabilities:

- **OpenAI Embedding API**  
  For converting regulatory text into high-dimensional vectors.  
- **OpenAI GPT-4o API**  
  For summarization, question answering, and clarification prompts.

# 6\. Technical Components

![][image3]

## 6.1 Frontend (UI/UX)

Built using **React** and hosted via **static site deployment** (e.g., GitHub Pages \+ Cloudflare).

**Key Features:**

- **Document Selector**  
  Filter by year, program, and rule type (Final / Proposed)  
    
- **Q\&A Interface**  
  Chat-style question answering with citations to source XML  
    
- **Common Functionalities Panel**  
  Trigger predefined tasks: Summary, FQA, and Policy Comparison  
    
- **Result Caching UI**  
  Shows cached output with option to regenerate

## 6.2 Backend Services

Modular backend implemented in **Python**, deployed via **Cloudflare Workers** (API routing) and **VM/container backend** (heavy processing).

| Service | Role |
| :---- | :---- |
| **Ingestion Service** | Periodically fetches and parses new XML from Federal Register |
| **XML Parser** | Extracts structured sections for processing |
| **Indexer** | Embeds text chunks and stores in FAISS |
| **RAG Query Engine** | Handles query → retrieve → LLM → respond pipeline |
| **Clarification Engine** | Triggers follow-up prompts if user input is vague |
| **Cache Manager** | Reads/writes result cache to reduce LLM load |

## 6.3 Data Storage

| Component | Purpose |
| :---- | :---- |
| **FAISS Vector Index** | Stores text chunk embeddings for similarity search |
| **Regulation XML Store** | Source-of-truth for parsed documents |
| **Result Cache** | Stores generated outputs (summaries, Q\&A, comparisons) keyed by hash |
| **Chat History DB** | Maintains user-level and document-level conversation history |

# 7\. Functions Design

## 7.1 Document Retrieval & Filtering

- **fetchDocuments(year, program, rule\_type)**  
  Retrieve available documents from the local registry, filtered by year, program (e.g., MPFS, QPP), and rule type (Proposed / Final).

## 7.2 XML Parsing & Indexing

- **parseXML(xml\_file)**  
  Parse and extract structured content from XML, focusing on `<SUPLINF>`, `<REGTEXT>`, and headers.  
    
- **indexDocument(parsed\_content)**  
  Generate embeddings from the parsed text and insert them into the FAISS vector database for semantic search.

## 7.3 Query and LLM Functionalities

- **generateSummary(document\_id)**  
  Produce an executive summary and bullet list of key changes for the specified rule.  
    
- **generateFQA(document\_id)**  
  Generate a list of commonly asked questions and grounded answers based on the document content.  
    
- **queryDocument(document\_id, user\_question)**  
  Answer free-form user questions using Retrieval-Augmented Generation, citing original text chunks.  
    
- **comparePolicies(document\_id\_1, document\_id\_2)**  
  Detect and summarize textual or numerical differences between two rules (e.g., Proposed vs Final, year-over-year).

## 7.4 Cache Management

- **checkCache(document\_id, feature\_type)**  
  Determine if a cached result already exists for the given document and task (e.g., summary, Q\&A, comparison).  
    
- **storeCache(document\_id, feature\_type, result)**  
  Save a new result into persistent storage for reuse.  
    
- **forceRefreshCache(document\_id, feature\_type)**  
  Allow the user to regenerate cached content and overwrite existing data.

## 7.5 Prompt Templates

The following prompt structures are maintained centrally and versioned for reproducibility and improvement:

- **Document Summary Prompt**  
  *"Please summarize the following Medicare regulation into a 300-word executive summary with 5–8 bullet points..."*  
    
- **Q\&A Prompt (Selected Document)**  
  *"Based on the following regulatory text, answer this user question as specifically as possible with citations..."*  
    
- **Clarification Prompt (Corpus Mode fallback)**  
  *"The user asked: 'When did the MPFS Final Rule take effect?'*  
  *Please determine which regulation document is likely relevant or ask a clarifying follow-up."*

All prompts are stored with version tags (`v1`, `v2`, etc.) and can be tested in sandbox mode prior to production deployment.

# 8\. MVP Scope and Future Expansion Considerations

## 8.1 Current MVP Key Functionalities (High Priority)

- **Federal Register document ingestion (manual \+ automated pipeline under development)**  
  Ingest publicly available XML rules, focusing on MPFS and QPP initially.  
    
- **Document parsing and FAISS indexing**  
  Automatically process structured XML and index it into a vector store for semantic retrieval.  
    
- **Real-time regulatory Q\&A (Selected Document mode)**  
  Support natural-language questions with citations grounded in selected rule documents.  
    
- **Common functionalities with cache layer**  
    
  - Executive summary generation  
  - Frequently asked questions (FQA) generation  
  - Policy comparison (Proposed vs Final or Year-over-Year)


- **Frontend interaction via React**  
  Modular panels for document selection, chat history, and common insights.

## 8.2 Future Expansion Functionalities (Lower Priority)

- **Automated crawling from Federal Register API**  
  GitHub Actions \+ Cloudflare Workers nightly ingestion with retry and CAPTCHA handling.  
    
- **Cross-document Q\&A (Corpus Mode)**  
  Inference-based document identification when no file is selected, using guideline classifier \+ vector search.  
    
- **Advanced analytics**  
    
  - Year-over-year trend charts  
  - Quantitative impact summaries on payment rates, quality measures, etc.


- **Mind Map generation & narrative synthesis**  
  Visual flow of how rules evolve and relate across sections and years.  
    
- **Product Management Assistant tools**  
  Risk flagging, milestone reminders, “What changed this year?” digest automation.

# 9\. Intent Classification & Prompt Selection

To support natural language interaction without requiring users to preselect a document, the system includes a lightweight **intent recognition** and **prompt routing** mechanism. This layer bridges ambiguous user inputs with the correct downstream task (e.g., Q\&A, summarization, comparison).

## 9.1 Intent Classifier

| Component | Description |
| :---- | :---- |
| **Input** | Raw user question (free-form text) |
| **Output** | One of: `ask_fact`, `summarize_doc`, `compare_rules`, `upload_attempt`, `unknown` |
| **Model** | Zero-shot classifier using OpenAI `gpt-4o` with system prompt: \_“Classify the user's intent as one of: ask\_fact, summarize\_doc, compare\_rules, upload\_attempt, unknown.”\_ |

## 9.2 Prompt Template Selector

Once the intent is classified, the system selects the appropriate prompt and retrieval strategy:

| Intent | Retrieval Scope | Prompt Template |
| :---- | :---- | :---- |
| `ask_fact` | FAISS top-6 chunks (inferred guideline) | Q\&A Prompt: “Based on the following regulatory text, answer…” |
| `summarize_doc` | Entire XML doc (based on metadata match) | Summarization Prompt |
| `compare_rules` | 2 XML docs (diffed on ID or year) | Comparison Prompt: “What changed between these two rules…” |

## 9.3 Example Classifier Output

{

  "user\_question": "When did the CY 2024 MPFS Final Rule become effective?",

  "intent": "ask\_fact",

  "retrieval\_doc": "MPFS CY2024 Final",

  "prompt\_template": "Q\&A: Answer the question based on..."

}

# 10\. Error Handling & Fallback Strategy

To ensure system robustness and graceful degradation, the following fallback strategies are implemented:

## 10.1 LLM Failures

- If OpenAI API returns rate-limit (429) or server errors (5xx), system retries with exponential backoff (up to 3 attempts).  
- If failure persists, user is shown a friendly error: *"We're having trouble reaching the AI model. Please try again later."*

## 10.2 Empty or Ambiguous Queries

- If no relevant documents can be retrieved (low retriever confidence), the system prompts the user for clarification (e.g., "Which year or program does your question refer to?").  
- If the LLM returns vague or generic answers, the system includes a disclaimer: *"Answer may be incomplete; please refine your question or select a document."*

## 10.3 Embedding or Indexing Errors

- If new documents fail to parse or index, errors are logged and flagged for admin review via Slack/Webhook.

## 10.4 Cache Misses

- If no cached summary/FAQ/comparison is found, fallback is to regenerate on demand.

# 11\. Deployment & DevOps Strategy

## 11.1 Frontend Deployment

- **Tech Stack:** React \+ TailwindCSS  
- **Deployment:** GitHub Pages via `gh-pages` branch  
- **Hosting:** Cloudflare Pages proxy → GitHub static bundle  
- **CI/CD:** GitHub Actions auto-build on push to `main`

## 11.2 Backend Deployment

- **API Routing Layer:** Cloudflare Workers (routes REST API calls to backend Python service)  
- **Processing Backend:** Python (FastAPI) hosted on free-tier platforms (e.g., Render, Railway, Fly.io)

## 11.3 Vector Index Storage

- **Vector Store:** FAISS with file-based persistence (`.faiss`, `.json`), mounted on disk or S3-compatible storage  
- **Cache Layer:** Disk-based JSON or SQLite for summaries and responses

## 11.4 Automation Jobs

- GitHub Actions nightly crawler fetches new XML files from Federal Register API (`0 3 * * *`)  
- Triggers downstream indexing and cache invalidation tasks via Webhook

All secrets (OpenAI API keys, admin emails) are stored in GitHub Encrypted Secrets or Cloudflare KV bindings.  


[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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yUnOwW9LSFpYVaYcISKE5AsKEUkTq8pQiAipfShEJE2sKkMhIqT2oRCRNLGqDIWIkNqHQkTSxKoyFKLKg+knUM4M34ZDDjnELKIiMKWHma/eQxwoRCRNrLW31Ap+2WWXqU6tDPt6ffv2NYuniC233NI0ES+63mFOqYEDB5rmuueggw4yTc5QiEiahN/t3xHlEEwaNGhgmuqeqPLDLK433HCDaSbet088YUSVab2z//77myYnKEQkTax3tOtN75quHrn44otNkwJTl7/11lummXxHWNmwroVTbtlQiEiaWGuta8V2TVePhJUNhSiasLIJK09SftlQiEiaWGuta8V2TVePhJUNhSiasLIJK09SftlQiEiaWGuta8V2TVePhJUNhSiasLIJK8+4fPHFF6Ypd5RbNhQikibWWutasV3T1SNhZVNtIfr666/VuYwaNUoNTqufF9YxHfnll1+u5fjW/uijjxbYqkVY2YSVZ7k89NBDap8LFixQy/fff99MkhvKLRsKEUkTa611rdiu6VzB/iTknbBrqLYQmefRokUL76OPPlLrDRs2VOsQI2H16tXekCFDivJVi7CySfp8zP1JGUj9a9myZUEc4dBDD/XzYf2EE05Q8U8//bQg7fXXX18QBxB7rPfp00fFk8S8FlcoRCRNrLXWtWK7pnNh6NCh6t87+Oabb1SHz48//tjfvmjRIrWcP3++t3z5cu/LL7/0NmzY4E2ePFnZFy5cqJYvvviiWup9TtauXevdf//9/v6wD9hkn2JLkrCySVuIUHb33Xef/6Rkbpe4aa8WYWWT9PkE7e+AAw7w18877zy1lHRHHHGE99VXX6l1jDQPIfr8888L0kycOLEgrh9DhK4Szj/oWlyoxLkQ4oq11rpWbNd0LohjxA2Of+VA7xyKzqJAv8lHjx6tXiGh/8nOO++s/snDGZiO4OSTT1bL3Xff3bd3795dzTjarVu3grRJEba/tIVIBF7sU6ZMUevyJwDrEpC22oSVjXkdcTH3J9csDB482Fu3bp1v08vioosuUvVUkPLD8rrrrvPzyPL5559Xv/u5556rQtKY1+IKhYikibXWulZs13Sl0q5dOyUsuhDhNRKQY2K7AAHS48OGDVNLSXvssccWOBr9vLG+YsUKb9y4cb4tCcLKptpChG8f4ighxHoZ4Kly48aNan3q1KmqvN955x0/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SoJpNTCgqgyQivCrX/0qsaddClG2oBCRtLCqTJJCFAUG0Ozfv7+ahvnnP/+57/iigjxF2AKmrm3durX3+OOP+6NP5xWMQYeBXFu1aqUch3mtQeH73/++t8UWWxTZzYAx5jDn0c0331w0HUIloBBlCwoRSQurysBBEVIJKETZgkJE0sKqMhQiUikoRNmCQkTSwqoyFKL8gCkc0LoPw+q/8MILaoZQTLqGadfx2hNzG40bN059C8P3urSbkFdKiDBhH+Z3qseAKUTKhUJE0sKqMhSidEGDgT/+8Y/eXnvtVfA9B9N7o0EDGhNgIruoSepswHlhptzbbrtNzQK70047FRzr5JNP9v7v//7PzBabpIUI54r5meodNAKSubxKgUJE0sKqMhSi6oPm0CICaLiBGVbXr19vJqsaaKqNxh5yTr/85S+9Z5991kxWMkkKEetpITKjbilQiEhaWO/eNG9wvGZCvx604rrqqqu8888/32vZsqV34okner/+9a+9/fbbz2vUqJF33HHHec2bN/cuuOACr0OHDqr/z3PPPeetWLHC3GUmkVkPjzrqKG/dunXm5syCWWBFnDD1e6kkJUQXXXSRaSJe6fcuhYikhbWmllqZXVi7dq163aQ3Kd5hhx28iy++2Bs5cqS3cOFCM0ss5s2bp149NWvWzD+ehLZt26byOgeiiePr03vnHeng6kpSQlTKMeuNzz//3DSFQiEiaWG9g+Pe5C+++KK3/fbbq/3gNdPDDz9sJskEmKoYT1k4T7xj/+CDD8wkiRG3TLMOPppfdtllprmIpISoffv2pol8x/XXX2+aQqEQkbSwesRynOY111yj8sEh5Rk8LeE68HowKf7lX/7FNNUkqAM2khIil2PVK6WUDYWIpIVVZUoRojZt2qgP2bUIygGt0+JSSnnmGZfrpBBVnlLKhkJE0sLqLVwcCihl1OW8gibMf/3rX01zSaA8t91228RH884SeBU7adIk01wEhajylFI2FCKSFlaVcRUi13R5J+516vmx/pOf/CSVxhJJc+ONN6rr6dy5s4pTiLJBKWVDISJpYfWqro4X6WbNmmWaawp09nQtjzDC8ksTbgzQilEPss4dd9yhzhch6JUlhSgblFI2FCKSFsFeUSPMcZog3dSpU9VyzZo15uZcg86bUg6u5RGGa36MdnDaaaf5zv7YY4/17r333qo+PeFVJBpsyEgLO+64o3f//febyQKhEGWDUsqGQkTSwuoVXR2nnu6jjz5SUw/AhrHO8gg6xeL8DzzwwAK7a3mEETc/mD9/vtelSxc1txM69OL1nghWOQHTaaDJOuYdwrBBSbQSpBBlg1LKhkJE0sLqFV0dZ1Q6TH4nnR0Rrr32Wm/z5s1mstTo3r27t9VWW6lz22abbdRgoWFEXacLcfPnBQpRNiilbChEJC2sXtHVcbqmE9DjGwMzHnDAAQX/ziEEv/nNb7xLL73Ue+CBB7wZM2aoUaVLAcPkoCPtn//8ZzWCAf7tm08BP/3pT9WYbsuWLTOzR1LqdZrEzZ8XKETZoJSyoRCRtLB6RVfH6ZquXDDoJ6YtwDTfmFocA3FOnjxZCRU+7uPbCUagLmVIk3KIe51x8+cFClE2KKVsKEQkLaxe0dVxuqbLO3GvM25+k7hOvFJQiLJBKWVDISJpYfWKro7TNV3eiXudUfmxDSNJSwCY0E7PI3Y4+kMPPVRNcrfvvvt6nTp18vcxbdo0NYfQEUcc4eeTbUHrUbimM6EQZYNSyoZCRNLC6mVcHZFrurwT9zqj8gdtE3HauHGjiosQbbfddnoyv1k1RMm0CUFChCWCvNJ88803fRtmdMVywIABasZXrMtxsb777rv7+zOhEGWDUsqGQkTSotjzGQQ5xyBc0+WduNcZlV8EAAFPO+Dwww/3twF97h09/WeffaZsMlArAr6n6UCYZCrxESNGeOedd573zTffqG2yf1lievEgO4QKrQqjrgPUmxDtvPPOammWV9qUUjYUIpIW1rvF9YZyTZd34l5nVH5zG8RIREW2iRBhskAdbIfIYGpx3Wai7wtLiIGETZs2FeWROAa0FTC1gJnOpN6EKKuUUjYUIpIW0d7EC3ZmQbimyztxrzMqv7lNj/fq1Ut9DxIhaty4sZohFaDFoC4uAK0Mzf0BXYjGjx/v78PMH7Zs2LBhQTwMClE2KKVsKEQkLaK9iWd3OIJrurwT9zrj5td5//33VWMGjLSgg28706dPL7CFgSeocePGFdgwzboAkZB+XEOGDPFf5dmgEGWDUsqGQkTSwuoVXR2na7q8E/c64+bPCxSibFBK2VCISFpYvaKr43RJh5ZfeLWD10qCOKNSuPLKK01TEejcihEWksblOqOImz8vUIiyQSllQyEiaWH1iq6O0yWdnkbWXfKZlJMnKeIeO27+vEAhygallA2FiKSF1Su6Ok5bOr1/iw7yYdRnU5g++OADb9GiRapZLGzIj5GhJc3atWvVEk4MfVuwj549e/r7ffvtt70VK1aoTp1weLJfpEXAUxnGs5P96WmicEkTRdz8Jvhuc+utt5rmAtIYAZ1ClA1KKRsKEUkLq1d0dZy2dGHbxY4RuvW4LkRmWixlHR/bsY4P9zoiRCIygn4est6nT5+ibWG4pIkibn4TtKILE3mhffv2pqniUIiyQSllQyEiaWH1iq6O05aua9eu3sSJE/24LirgzjvvLIgPHTpUiUmYEKFfy+zZs/1tr7zySsE5iBBJK6+WLVt6EyZMCBSiUaNGFcSjcEkTRdz8JroQYd/6kx2W+qyy6BzbpEkTP44nww0bNqhlqSOc26imEDVv3tw0ke+QjskuUIhIWli9oqvjdEmHNBL69evn24AuROjICecYJUSyhCPF8uijj/ZHITj//PN9IcIwNOKc4Wzl+LDLOdSKEOlPduhH9Mwzz6g4ZnoV+xtvvKECxqITW7NmzdR6klRTiJIu01rhqaeeMk2RUIhIWljvYNeb3DVdtcDUEJg2ImniXmfc/Ca6EOmCiunax44dq+L4fiZ2E9jMceuSwEWITj31VLWMK0ToR4Wx8EghQb93FBQikhbWmupamV3TVQv5x580ca8zbn6TMCGSpf6qDk+B+qs5WWJyQozOkCQuQvSf//mfahlXiMDFF19c0Fil3imnnlGISFpYa+sJJ5zg/f3vfzfNRZRT8fNI3OuMmz8vuAhRJcoCM/xiv/UcHn30UbNYnJBX24RUG6snwOudVq1ameYicAPUA3GvM27+vFCqEFXiNSopDYzGTkgaOHlFF+fpkqYWiHudJ510kmmqSVzK6eqrr/bXu3Tpom0haYBBdQlJA7u3+Aenn366aSrCxfHUAklcZ6NGjbzrrrvONNcMLmU0cuTIgrhLHlI5MD8VIWnhfPdjls4o6sWRJHmdu+yyi9ofJprLO7/4xS/UtUiTcRtmOZpxUl1Y/iRNnGufraJi6oBOnTqZ5ppi1113NU2Jcccdd6gyRvjLX/5ibs4U77zzjnpKxrn+6le/Uv21SmX06NGmqWh0DFI9fve735kmQqpGtLoYYKppG3BOY8aMMc25BsOk2IQ4aTB6OEYZF3FCQH+gBx98sGAW1krx4osveldddZW3xx57+MfHK8VSO0kGEVaWYXZSWdhIgaRNSXd+KR0fDzvsMOVYMK10HsGQQDj/Sy65xNyUCRYuXKi+s+AjPxzJQQcdVCBargEjV5x44olex44dvfvuu8+bOnWq8+R35fDss896K1euNM2KZcuWedOmTTPNpML88pe/NE2EVJWShAiU868VPd/RBFyc3xlnnOHNmTPHTJYKS5cuVZ0h5dyOP/54b9OmTWYykhC2TpP4DTAmIKkO5dzPhCRNWbXwP/7jP0xTWcycOVO1Httvv/0K/qX/27/9m3fUUUepV1ODBg3yXn31VTUS9+rVq9XkekFAPNAX5a233vJeeuklr2/fvl7btm3VdA9bb711wf4xwsD//u//elOmTDF3QyqIq9PTJ04klYPfhUhWcPMMASQlRnGoxAyspDK4ipDwwx/+0DSRBMFQT2h0QkgWKM07GJTqXEj9gafYcusJxgvs37+/aSYxKff3IKRSxKqReB3GSk3C+OSTT2LXD7xGveeee0wzKYMvvvhC/R4uY0cSUk3ieYnv+H//7/+pKbkJEeDw9IkQ44L92aZEJ8FMnz5dld9f//pXcxMhmSARIRIuvPBCVeFd+huR2gLzP+2www7q90fn5kqBRibS6AT9qtCgBf28GP4ZWrRoob6xoYyOPPJIswgJyRyJCpEORu3GFBLiNBhqM+y5555er169zJ+fEEKcqZgQEUIIIS5QiAghhKQKhYgQQkiqUIgIIYSkCoWIEEJIqlCICCGEpAqFiBBCSKr8f+czQOr38nvCAAAAAElFTkSuQmCC>

[image3]: <data:image/png;base64,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>