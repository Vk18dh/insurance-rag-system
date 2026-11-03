# Software Test Execution Report

**Date of Execution:** 2026-10-11T11:27:00+05:30  
**Environment:** Windows 11 Home Single Language (Build 10.0.26200), AMD Ryzen 7 6800H (16 CPUs, ~3.2GHz), 16 GB RAM  
**Python Runtime:** Python 3.13.7  
**Git HEAD:** `5000a20065aee85c9c8c99a98ac7e0e07d1769dc` (`feature/rag-offline-updates`, dirty working tree)  

---

## 1. Executive Summary

Four distinct automated test suites were discovered and executed in the local repository environment. All raw outputs, exit codes, and timestamps have been captured directly to `evaluation/raw/`.

| Suite | Target Directory / Command | Total Collected | Passed | Failed | Skipped | Duration | Exit Code | Genuine vs Mock/Stub |
|---|---|---|---|---|---|---|---|---|
| **Phase 2 Agent & Service Tests** | `pytest phase2/tests/ -v` | 233 | 232 | 1 | 0 | 3.07s | 1 | **Genuine Unit / Component** (with mocked LLM/retriever calls) |
| **Backend & API Tests** | `$env:PYTHONPATH="."; pytest backend/app/tests/ -v` | 47 | 46 | 1 | 0 | 127.82s | 1 | **Genuine Integration / API** (database, auth, routers, guardrails) |
| **Phase 2 Observability Tests** | `pytest phase2/observability/tests/ -v` | 22 | 22 | 0 | 0 | 0.54s | 0 | **Genuine Unit / Storage** (sqlite, json, audit, tracing) |
| **Phase 2 Validation Suite** | `pytest phase2/validation/tests/ -v` | 12 | 12 | 0 | 0 | 0.33s | 0 | **Placeholder / Stubs** (`assert True` smoke checks) |
| **Phase 2 Validation Runner** | `python -m phase2.validation` | 12 checks | 12 | 0 | 0 | 2.36s | 0 | **Placeholder / Stubs** (wrapper around validation stubs) |

---

## 2. Granular Breakdown & Analysis

### 2.1. Phase 2 Agent & Service Tests (`phase2/tests/`)
- **Raw Log:** `evaluation/raw/pytest_phase2_tests.log`
- **Result:** 232 Passed, 1 Failed (233 total) in 3.07 seconds.
- **Components Covered:**
  - `QueryUnderstandingAgent`: Intent classification, entity extraction, input validation.
  - `RetrievalAgent`: Adaptive strategy weighting, Phase 1 adapter, deduplication, ranking service.
  - `VerificationAgent`: Evidence relevance, structural consistency, citation presence.
  - `ReasoningAgent`: Multi-step deduction, clause linkage, contradiction cross-checking.
  - `RiskAssessmentAgent`: Ambiguity detection, legal sensitivity, exclusion checks, escalation.
  - `ContradictionAgent`: Clause conflict detection, product alignment rules.
  - `ResponseBuilder`: Structured citation assembly, fallback response formatting.
  - `AgentOrchestrator`: Linear agent sequencing, retry policies, timeout propagation.
- **Failure Analysis:**
  - `phase2/tests/test_ambiguous_001.py::test_valid_supported_insurance_query_continues`
  - **Trace:** `AssertionError: assert 'RetrievalAgent' in ['QueryUnderstandingAgent']`
  - **Root Cause:** In `phase2/orchestrator/orchestrator.py`, prompt hardening added an early exit or strict check on query context which stopped the mock pipeline prematurely in this test fixture before reaching `RetrievalAgent`.

### 2.2. Backend & API Tests (`backend/app/tests/`)
- **Raw Log:** `evaluation/raw/pytest_backend_tests.log`
- **Result:** 46 Passed, 1 Failed (47 total) in 127.82 seconds.
- **Components Covered:**
  - Auth & RBAC: Token generation, role validation, unauthorized route blocking.
  - Conversations: Session creation, message persistence, user data isolation.
  - Guardrails: Input injection detection, toxic prompt blocking, unsupported claim detection.
  - Evaluation API & Service: SQLite persistence, evaluation run isolation, metrics computation.
  - Provider Failover: Failover mechanics across providers.
- **Failure Analysis:**
  - `backend/app/tests/test_hitl_e2e.py::test_hitl_workflow_end_to_end`
  - **Trace:** Test client dispatched POST `/api/v1/query` with `"What is the capital of France?"`. The orchestrator attempted real calls to the local LLM (`http://ollama:11434`), which failed with `[Errno 11001] getaddrinfo failed` because the Ollama Docker container was not running on host network, and external API failover timed out, returning HTTP 503.

### 2.3. Phase 2 Observability Tests (`phase2/observability/tests/`)
- **Raw Log:** `evaluation/raw/pytest_observability_tests.log`
- **Result:** 22 Passed, 0 Failed in 0.54 seconds.
- **Components Covered:**
  - Metrics service thread safety and lifecycle timing.
  - Tracing spans and child context inheritance.
  - Audit logging with SHA-256 query hashing and salt security.
  - SQLite and JSON storage persistence.
  - System health monitor failure rate alerts.

### 2.4. Phase 2 Validation Suite (`phase2/validation/tests/`)
- **Raw Logs:** `evaluation/raw/pytest_validation_tests.log`, `evaluation/raw/phase2_validation_runner.log`, `evaluation/raw/validation_report_20261011_055657.md`
- **Result:** 12 Passed in 0.33s (pytest) / 2.36s (runner).
- **Distinction Between Real vs Mock/Placeholder Tests:**
  - Inspection of `phase2/validation/tests/` revealed that tests in `unit`, `stress`, `performance`, `concurrency`, `regression`, `recovery`, and `deployment` consist strictly of empty assertions (`assert True`).
  - `test_security.py` checks only that a mock list has length $\ge 3$ and that `settings.fail_on_prompt_injection is True`. No actual security probing occurs against the application.
  - **Historical Artefact Verification:** The repository's historical validation report from 13 July 2026 (`validation_report_20260713_211343.md`) which reported 12 passing checks in 2.21 seconds was generated by this exact runner. These checks are smoke/placeholder tests and **cannot be used as scientific evidence** of performance, concurrency, stress tolerance, or retrieval accuracy.

---

## 3. Genuine Behavioural Capabilities Audit

| Behaviour | Implementation Status | Evidence / Location |
|---|---|---|
| **Dense Semantic Retrieval** | Implemented | `app.py:vector_search()`, `phase2/services/retrieval_service.py` via ChromaDB |
| **BM25 Keyword Retrieval** | Implemented | `app.py:bm25_search()`, `index.py:build_bm25_index()` via rank_bm25 |
| **Score Fusion & Deduplication** | Implemented | Min-Max Normalisation + weighted linear combination (`app.py:hybrid_search()`) |
| **Source & Page Metadata** | Implemented | Preserved in JSON elements and ChromaDB metadata (`source_document`, `page_number`, `section_title`) |
| **Verification Gates** | Implemented | `VerificationAgent`, `EvidenceValidatorService` |
| **Insufficient Evidence Refusal** | Implemented | System prompt fallback ("I could not find this information..."), `ResponseBuilder` |
| **Ambiguity / Out-of-Domain Detection** | Implemented | `QueryUnderstandingAgent`, `AmbiguityDetectorService` |
| **Prompt Injection Defense** | Partially Implemented | Rule-based regex in `GuardrailService`, but validation suite test is a mock |
| **LLM Provider Failover** | Implemented | OpenRouter $\to$ Groq $\to$ Ollama chain in `phase2/services/llm_provider_manager.py` |
| **Citations & Traceability** | Implemented | Structured citation records generated in `ResponseBuilder` |
| **Authentication & RBAC** | Implemented | JWT Bearer tokens + User/Admin/Expert roles in `backend/app/dependencies/auth.py` |
| **HITL Escalation Logging** | Implemented | SQLite database escalation queue in `backend/app/repositories/` |
