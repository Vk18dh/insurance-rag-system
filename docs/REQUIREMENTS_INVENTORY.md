# Requirements Inventory

| ID | Requirement | Source | Component | Current State | Evidence | Status |
|----|-------------|--------|-----------|---------------|----------|--------|
| REQ-01 | Separate User and Management Websites without frontend cross-navigation | 01_PRD, 03_APP_FLOW | Frontend | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-02 | Backend RBAC enforcement for USER, EXPERT, ADMIN roles | 02_TRD, 05_SCHEMA | Backend Auth | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-03 | Multi-conversation persistent chat management | 01_PRD, 05_SCHEMA | Backend DB | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-04 | Hybrid Retrieval (ChromaDB + BM25) for RAG context | 01_PRD, 02_TRD | Phase 1 / 2 | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-05 | Agentic RAG Pipeline (Query, Retrieval, Verification, Reasoning, Risk, Contradiction) | 01_PRD, 02_TRD | Phase 2 Orchestrator | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-06 | LLM Provider Resilience (OpenRouter -> Groq -> Local Ollama) | 01_PRD, 02_TRD | Phase 2 LLM Manager | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-07 | Human-in-the-Loop (HITL) ReviewTasks for low confidence | 01_PRD, 03_APP_FLOW | Phase 2 / Backend | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-08 | Source document citations and explanations in final response | 01_PRD, 05_SCHEMA | Phase 2 Response | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-09 | Admin Document Management (Ingest PDF, Chunk, Embed) | 01_PRD, 02_TRD | Phase 1 / Backend | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-10 | Configurable Top-K=8, min_relevance_score=0.3 | 02_TRD | Phase 1 / 2 | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-11 | Secure Audit Logging (no raw PII, keys, or passwords) | 02_TRD, 05_SCHEMA | Backend Audit | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-12 | RAG Evaluation system using local Ollama | 01_PRD | Phase 2 Eval | NOT TESTED | Pending Audit | NOT TESTED |
| REQ-13 | Guardrails (Input prompt injection, output validation) | 01_PRD, 02_TRD | Phase 2 | NOT TESTED | Pending Audit | NOT TESTED |
