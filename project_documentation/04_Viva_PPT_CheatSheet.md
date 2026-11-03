# PART 28 — PPT CONTENT
**Slide 1: Title:** InsuraLens - Agentic RAG System for Insurance  
**Slide 2: Problem Statement:** LLMs hallucinate. Insurance requires 100% factual accuracy.  
**Slide 3: Proposed System:** An Agentic RAG architecture that acts as a team of AI researchers.  
**Slide 4: Why Agentic RAG?** Explain the difference between handing text to a single LLM (Normal RAG) vs having specialized agents verify, reason, and check for contradictions (Agentic RAG).  
**Slide 5: Architecture Diagram:** Visual flow (Frontend -> Orchestrator -> ChromaDB/BM25 -> 7 Agents -> Response).  
**Slide 6: Hybrid Retrieval:** ChromaDB (Meaning) + BM25 (Keywords).  
**Slide 7: Human-in-the-Loop (HITL):** How unverified claims are routed to PostgreSQL Review Tasks for human experts.  
**Slide 8: Citations:** How backend UUID mapping ensures no hallucinated page numbers.  
**Slide 9: Limitations & Future Scope:** Acknowledge local hardware speed limits and propose reranking.

# PART 29 — 40 VIVA QUESTIONS AND ANSWERS
1. **What is RAG?** Retrieval-Augmented Generation. It gives the AI a searchable database of your documents to read before answering.
2. **Why RAG?** To prevent AI hallucinations by grounding it in factual, private documents.
3. **What is Agentic RAG?** Instead of one AI step, it's a workflow of multiple specialized AI agents checking each other's work.
4. **Why not normal RAG?** Normal RAG can't verify its own evidence or check for contradictions. 
5. **What is an embedding?** A mathematical array (vector) that represents the meaning of a sentence.
6. **Why all-MiniLM-L6-v2?** Fast, runs locally, small memory footprint, great for standard text.
7. **What is ChromaDB?** A vector database designed to store and search embeddings using geometry.
8. **What is BM25?** A keyword-matching algorithm (sparse retrieval).
9. **Why hybrid retrieval?** Embeddings understand meaning (e.g. "cancel" = "surrender"), BM25 understands exact ID numbers. You need both.
10. **Which LLM is used?** `qwen2.5:3b` running locally via Ollama.
11. **Difference between model and provider?** Qwen 2.5 is the *model* (the brain). Groq is a *provider* (a cloud company hosting it). Ollama is a *runtime* (running it on my laptop).
12. **What is the VerificationAgent?** It checks if the retrieved document actually contains the answer.
13. **What is HITL?** Human-In-The-Loop. When the AI is unsure, it flags a human expert.
14. **How are citations generated?** By mapping database chunk UUIDs back to the original PDF filename and page number.
15. **Why PostgreSQL?** To store users, chat history, and ReviewTasks permanently.
16. **Why Docker?** So the entire complex system runs instantly on any machine without installing Python libraries one by one.
*(Answer similar conceptual questions using the Simple Words explanations provided in Part 2)*

# PART 30 — ELEVATOR PITCHES
**30-Second Explanation (For Non-Tech Examiner):** "My project solves the problem of AI inventing fake information. Instead of just asking ChatGPT an insurance question, my system searches the actual PDF policy, extracts the exact paragraph, and uses an AI 'research team' to verify the answer is correct before showing it to the user with a clickable page number."

**3-Minute Explanation (Technical):** "InsuraLens is an Agentic RAG system. Normal RAG just retrieves text and passes it to an LLM. We built a 7-agent orchestrator. First, we use Hybrid Retrieval—ChromaDB for semantic dense vectors using MiniLM, and BM25 for sparse keyword matching. Then, the retrieved chunks pass through a Verification Agent to score relevance, a Reasoning Agent to deduce the answer, and Risk/Contradiction agents for safety. If verification fails, it triggers a Human-in-the-Loop review task stored in PostgreSQL. The frontend is Next.js, the backend is FastAPI, and the local LLM is Qwen 2.5 3B via Ollama. It guarantees citations by mapping UUIDs, eliminating hallucinated page numbers."

# PART 31 — FINAL ONE-PAGE CHEAT SHEET
**Tech Stack:** Next.js, FastAPI, PostgreSQL, ChromaDB, Rank-BM25, Docker, Ollama.  
**Models:** `all-MiniLM-L6-v2` (Embeddings), `qwen2.5:3b` (Inference).  
**Orchestration Pipeline:** Query -> Understand -> Retrieve -> Verify -> Reason -> Risk -> Contradict -> Build -> Guardrail.  
**Difference between DBs:** Postgres = Relational app data. ChromaDB = Vector text data.  
**Why it's better:** Factual grounding, verifiable citations, safe failure via human expert fallback.
