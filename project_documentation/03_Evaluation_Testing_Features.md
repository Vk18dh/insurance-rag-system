# PART 21 — EVALUATION
The repository includes an advanced RAG evaluation framework using the LLM-as-a-judge paradigm. 
**What it is:** Because manual testing of hundreds of AI answers is impossible, a separate LLM (the Judge) reads the system's output and scores it.
**Evaluation cases handled:**
- Supported Query: Answer is in the documents.
- Unknown/Unavailable: Answer is NOT in the documents. (A correct refusal scores 100%).
- Ambiguous: Query is unclear.
- Prompt Injection: Malicious user tries to trick the AI.
**Correct Refusal vs Hallucination:** If a policy doesn't mention "dental cover," and the AI says "I don't know," that is a CORRECT REFUSAL (Score 1.0). If the AI invents dental cover, that is a HALLUCINATION (Score 0.0).

# PART 22 — TESTING
The system uses `pytest` for automated backend testing.
- **Unit Tests:** Test individual components (e.g., verifying that the `VerificationAgent` correctly flags a bad chunk).
- **Integration Tests:** Test the entire flow from FastAPI endpoint down to PostgreSQL and back.
- **What passing tests prove:** They prove the software logic, routing, fallback chains, and agent pipelines execute without crashing.
- **What they DO NOT prove:** They do not prove the system is 100% hallucination-free in the real world, as LLM outputs are inherently non-deterministic.

# PART 23 — ALL FEATURES
**Core AI Features:** Multi-agent orchestration, Hybrid Retrieval, Semantic Verification, Contradiction Detection.
**User Features:** Chat UI, View exact PDF citations.
**Admin Features:** Review Task dashboard, Audit logs.
**Security Features:** JWT Authentication, RBAC, Prompt Injection filtering.
**Reliability Features:** Automatic LLM provider fallback, Dockerized isolation.

# PART 24 — CURRENT LIMITATIONS
1. **Local LLM Latency:** Running a 3B parameter model on a local CPU/GPU takes 2-3 minutes per query. 
2. **Semantic Verification is Heuristic:** The VerificationAgent relies on the LLM's understanding. It is not an absolute mathematical guarantee.
3. **Corpus Dependency:** If the PDF uploaded is a scanned image (no text), `unstructured` might fail to extract it perfectly, causing retrieval to fail.

# PART 25 — FUTURE ENHANCEMENTS
*(PLANNED / FUTURE WORK)*
1. **Cross-Encoder Reranking:** Adding a dedicated neural reranker after ChromaDB to perfectly sort the top 10 results.
2. **Streaming Responses:** Streaming the text word-by-word to the frontend so the user doesn't stare at a loading spinner for 3 minutes.
3. **Multimodal RAG:** Allowing the AI to understand charts and tables inside the PDF, not just raw text.

# PART 26 — IMPLEMENTED VS PLANNED
| Component | Status | Evidence/File |
|---|---|---|
| Multi-Agent Orchestrator | IMPLEMENTED | `routers/query.py` & `agents/` |
| Hybrid Retrieval (Chroma + BM25) | IMPLEMENTED | `retrieval/` |
| HITL (Review Task) | IMPLEMENTED | `review_repository.py` |
| PostgreSQL Storage | IMPLEMENTED | `docker-compose.yml` & `database.py` |
| Local Ollama Fallback | IMPLEMENTED | `llm_adapters.py` & `.env` |
| Cross-Encoder Reranking | PLANNED | Not in current source code |
| Word-by-word Streaming | PLANNED | `stream=False` in current codebase |
| OpenRouter / Groq APIs | IMPLEMENTED | `llm_provider_manager.py` |

# PART 27 — REPORT-READY CONTENT (STRUCTURE)
For your final university report, structure your chapters as follows:
1. **Introduction:** Define Agentic RAG and why insurance needs it.
2. **Problem Statement:** Hallucinations and manual document parsing.
3. **System Architecture:** Detailed breakdown of the 7 agents.
4. **Implementation:** Code-level details (FastAPI, Next.js, ChromaDB).
5. **Results & Evaluation:** Discussion of the LLM-as-a-judge scores.
6. **Limitations & Conclusion:** Honest assessment of local hardware limits.
