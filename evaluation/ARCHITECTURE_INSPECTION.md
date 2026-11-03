# Architecture Inspection & Technical Verification Report

**Document Version:** 1.0.0  
**Inspection Date:** November 3, 2026  
**Repository Branch:** `research-evaluation` (branched from `feature/rag-offline-updates`)  
**Scope:** Complete Codebase Architecture Audit for Final-Year Academic Research Evaluation  

---

## 1. Executive Summary

This inspection report provides a comprehensive, ground-truth audit of the **Insurance Agentic RAG** system (`InsuraLens`). It audits all 17 architectural subsystems directly against active source files, configuration declarations, container topologies, and database states.

All claims in this document reflect actual executing code in the workspace and explicitly document discrepancies between historical documentation and current implementation.

---

## 2. Comprehensive Subsystem Audit

### 2.1 Document Ingestion and Extraction
* **Source Files:** [`ingest.py`](file:///c:/Users/dhyan/Desktop/majorcode/ingest.py), [`backend/app/services/ingestion_service.py`](file:///c:/Users/dhyan/Desktop/majorcode/backend/app/services/ingestion_service.py)
* **Active Library:** `unstructured` (v0.18+) with `pypdf` fallback.
* **Extraction Strategy:** `partition_pdf(strategy="auto")` with layout preservation and OCR fallback for scanned pages.
* **Output Entity Structure:** Extracted into elements containing `text`, `type` (`Title`, `NarrativeText`, `ListItem`, `Table`), and coordinate metadata (`page_number`, `source_document`).
* **Canonical Corpus:** 8 authentic insurance documents totaling 882 pages and 32,304 raw elements.

### 2.2 PDF Processing & Table/OCR Limitations
* **Source Files:** [`ingest.py:82-140`](file:///c:/Users/dhyan/Desktop/majorcode/ingest.py#L82-L140), [`evaluation/corpus_manifest.csv`](file:///c:/Users/dhyan/Desktop/majorcode/evaluation/corpus_manifest.csv)
* **Processing Behavior:** Headings (`Title`) are tracked as section titles (`section_title`) and prepended as context to subsequent narrative text elements.
* **Observed Limitations:**
  - Complex nested surrender value tables (e.g., Annexure-4 of Bima Jyoti) and IRDAI statistical matrices are flattened into linear text sequences or row-wise strings.
  - Multi-column tables lose geometric column alignment; header-to-cell associations must be inferred by language models from surrounding text context.
  - Bilingual documents (DOC-007, DOC-008: IRDAI Annual Reports) interleave Hindi and English narrative sections.

### 2.3 ChromaDB Vector Database
* **Source Files:** [`index.py:142-198`](file:///c:/Users/dhyan/Desktop/majorcode/index.py#L142-L198), [`config.py:19-21`](file:///c:/Users/dhyan/Desktop/majorcode/config.py#L19-L21)
* **Storage Location:** Persistent directory at `data/chroma_db/`.
* **Collection Name:** `insurance_policies`
* **Distance Metric:** Cosine similarity (`"hnsw:space": "cosine"`).
* **Payload per Record:**
  - `id`: Unique UUIDv4 string.
  - `embedding`: 384-dimensional float vector.
  - `document`: Full text of the chunk.
  - `metadata`: `{"source_document": str, "page_number": str, "section_title": str}`.
* **Corpus Verification:** The canonical corpus produces exactly **1,067 chunks** across the 8 authentic policy documents.

### 2.4 BM25 Sparse Retrieval
* **Source Files:** [`index.py:203-228`](file:///c:/Users/dhyan/Desktop/majorcode/index.py#L203-L228), [`app.py:120-160`](file:///c:/Users/dhyan/Desktop/majorcode/app.py#L120-L160)
* **Library:** `rank_bm25.BM25Okapi` (v0.2.2).
* **Storage Location:** Pickled binary at `data/bm25_index.pkl`.
* **Tokenization Pipeline:** Lowercasing + Regex word extraction (`\b[a-z0-9]+\b`) + NLTK English stop-words filtering.
* **Serialization Structure:** Python dictionary containing:
  ```python
  {"bm25": <BM25Okapi Object>, "chunks": <List[Dict]>}
  ```
* **Performance:** Sub-2ms in-memory lexical query evaluation for exact alphanumeric codes (e.g., plan UINs like `512N339V03`, statutory sections like `Section 45`).

### 2.5 Hybrid Retrieval and Ranking
* **Source Files:** [`phase2/services/retrieval_service.py`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/services/retrieval_service.py), [`phase2/services/ranking_service.py`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/services/ranking_service.py)
* **Candidate Pool Oversampling:** Over-samples candidates with `fetch_k = top_k * 2 = 16` (16 from BM25 and 16 from ChromaDB, totaling up to 32 candidates).
* **Score Normalization:** Per-backend Min-Max normalization mapping unbounded raw BM25 scores and cosine distances to $[0.0, 1.0]$.
* **Dynamic Query-Classification Strategy Weights:**
  - *Policy Specific:* `bm25 = 0.7, vector = 0.3`
  - *Regulatory / Conceptual:* `bm25 = 0.4, vector = 0.6`
  - *Default / Standard:* `bm25 = 0.5, vector = 0.5`
* **Multi-Signal Re-Ranking:** Slices top candidates and re-ranks with:
  $$\text{ranking\_score} = 0.6 \cdot \text{retrieval\_score} + 0.2 \cdot \text{keyword\_overlap} + 0.2 \cdot \text{metadata\_completeness}$$

### 2.6 Embedding Model
* **Model Identifier:** `sentence-transformers/all-MiniLM-L6-v2`
* **Architecture:** 6-layer BERT-based bi-encoder, 384-dimensional dense embeddings.
* **Context Limit:** 256 tokens maximum sequence length.
* **Alternative Local Cache:** `BAAI/bge-small-en-v1.5` (512 token context window, 384 dimensions) is present in `~/.cache/huggingface/hub` and available for controlled comparative research.

### 2.7 Retrieval Top-K Configuration
* **Default Top-K:** `top_k = 8` (defined in `config.py:32` and `phase2/config/settings.py:204`).
* **Headroom Fetch:** `fetch_k = 16` (2x top_k) for dual candidate generation prior to deduplication.

### 2.8 Relevance & Validation Thresholds
* **Validation Minimum Top Score:** `min_top_score = 0.15` (triggers `LOW_SIMILARITY` warning).
* **Verification Agent Threshold:** `relevance_threshold = 0.30` (must score $\ge 0.30$ to pass verification).
* **Minimum Required Chunks:** `min_chunks_required = 1`.

### 2.9 The 7 Specialized Agents
Located under [`phase2/agents/`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/agents/):
1. **`QueryUnderstandingAgent`:** Intent extraction, query expansion, ambiguity detection, out-of-domain rejection.
2. **`RetrievalAgent`:** Executes dual-retrieval adapter, normalizes scores, deduplicates, and re-ranks.
3. **`VerificationAgent`:** Pre-generation gate verifying whether evidence contains sufficient factual grounding.
4. **`ReasoningAgent`:** Formulates structured multi-step deductive logic steps linking premise to explicit evidence IDs.
5. **`RiskAssessmentAgent`:** Evaluates medical, financial, and legal liability risk; flags exclusion terms.
6. **`ContradictionAgent`:** Detects conflicts between rider provisions and base policy conditions.
7. **`ResponseBuilder`:** Synthesizes final user-facing response with immutable UUID-mapped citations.

### 2.10 Agent Orchestration & Execution Watchdog
* **Source File:** [`phase2/orchestrator/orchestrator.py`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/orchestrator/orchestrator.py)
* **Architecture:** Sequential workflow engine driven by `WorkflowEngine`, isolated `ContextManager`, and `ExecutionManager`.
* **Execution Watchdog:** Hard boundary at `max_workflow_timeout_ms = 300000.0` (300 seconds), protecting system resources during local CPU generation.
* **Short-Circuit Optimizations:**
  - Flagged ambiguous queries bypass generation directly to clarification questions.
  - Flagged out-of-domain queries (`intent == "unknown"`) bypass retrieval and generation directly to safe refusal.

### 2.11 LLM Provider Configuration
* **Source File:** [`phase2/config/settings.py`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/config/settings.py)
* **Primary Provider:** Groq / OpenRouter cloud providers.
* **Local Provider:** Local Ollama runtime (`qwen2.5:3b` default, `qwen2.5:0.5b` lightweight option) at `http://ollama:11434/api/chat`.
* **Air-Gap Capability:** System operates with zero cloud API keys purely on local Ollama container.

### 2.12 LLM Fallback Mechanism
* **Source File:** [`phase2/services/llm_provider_manager.py`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/services/llm_provider_manager.py)
* **Provider Chain:** `[OpenRouter, Groq Key 1, Groq Key 2, Local Ollama]`.
* **Fault Handling:** Catches HTTP 429 rate limits, 5xx server errors, and network timeouts. Places failing provider into a 60-second cooldown and automatically falls over to the next provider in the chain.

### 2.13 Citation Generation & Source Grounding
* **Source Files:** [`backend/app/routers/query.py`](file:///c:/Users/dhyan/Desktop/majorcode/backend/app/routers/query.py), [`phase2/services/response_formatter.py`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/services/response_formatter.py)
* **Mechanism:** Strictly non-hallucinatory UUID mapping. The LLM only cites logical identifiers (`EVIDENCE_1`, `EVIDENCE_2`). The backend maps these tokens back to the database chunk UUID, retrieving verified `source_document` and `page_number` from ingestion records.

### 2.14 Dual-Layer Guardrails
* **Source File:** [`backend/app/services/guardrail_service.py`](file:///c:/Users/dhyan/Desktop/majorcode/backend/app/services/guardrail_service.py)
* **Input Guardrails:** Validates payload size ($\le 10,000$ chars), detects SQL injection patterns, and filters jailbreaks/prompt injection attempts.
* **Output Guardrails:** Scans for refusal phrases (`"i could not find"`, `"not explicitly mentioned"`). When detected or when zero sources exist, resets confidence to 0.0 and strips ungrounded text.

### 2.15 Verification Mechanism
* **Source File:** [`phase2/agents/verification_agent.py`](file:///c:/Users/dhyan/Desktop/majorcode/phase2/agents/verification_agent.py)
* **Components:** `RelevanceChecker`, `CitationValidator`, `ConsistencyChecker`, `CompletenessChecker`.
* **Enforcement:** If `is_valid_for_reasoning == False`, the downstream Reasoning Agent refuses to guess and triggers the refusal/HITL escalation flow.

### 2.16 Human-in-the-Loop (HITL) Mechanism
* **Source Files:** [`backend/app/repositories/review_repository.py`](file:///c:/Users/dhyan/Desktop/majorcode/backend/app/repositories/review_repository.py), [`backend/app/services/review_service.py`](file:///c:/Users/dhyan/Desktop/majorcode/backend/app/services/review_service.py)
* **Trigger Conditions:** Verification failure, contradiction detection, or low confidence ($0.0$).
* **Data Store:** `ReviewTask` records persisted in PostgreSQL, visible and actionable via the Next.js `/management/` portal.

### 2.17 Existing Evaluation & Testing Infrastructure
* **Test Suites:**
  - `phase2/tests/`: 233 unit/integration tests passing (100%).
  - `backend/app/tests/`: FastAPI route, auth, and HITL integration tests.
  - `evaluation/run_retrieval_benchmarks.py`: Historical retrieval benchmark harness.
  - `evaluation/corpus_manifest.csv`: Audited manifest of 8 authentic PDFs and chunk counts.

---

## 3. Differences Between Documentation and Actual Code

| Documented Claim | Actual Code State | Impact / Action |
|---|---|---|
| Historical validation report claimed "12 checks passed in 2.21s". | Audit revealed `phase2/validation/tests/` contained placeholder `assert True` statements. | Unit tests in `phase2/tests/` (233 tests) are genuine and verified; validation tests must not be confused with retrieval accuracy. |
| Total indexed chunks previously reported as 1,814 chunks. | Per-document manifest sums to **1,067 chunks**. The extra 747 chunks were synthetic chunks appended during upload integration tests (`backend/app/services/ingestion_service.py`). | Fixed: Canonical corpus verified at exactly 1,067 chunks. |
| Documented retrieval method claimed Linear 50/50 Hybrid. | Code implements dynamic intent-based weighting (70/30 for policy-specific, 50/50 default) and 3-signal re-ranking in Phase 2. | Evaluation framework will benchmark both baseline linear hybrid and phase 2 dynamic hybrid against pure BM25 and pure vector retrieval. |
| Watchdog timeout documented as 120 seconds. | Watchdog timeout updated to 300 seconds across settings and orchestrator to prevent premature timeouts during CPU reasoning generation. | Documented and verified active in `.env` and `settings.py`. |

---
*Report certified for research evaluation on branch `research-evaluation`.*

