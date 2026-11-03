# PART 1 — EXECUTIVE SUMMARY
The InsuraLens Agentic RAG system is an advanced enterprise-grade AI architecture designed specifically for the insurance domain. It upgrades traditional Retrieval-Augmented Generation (RAG) by integrating a multi-agent orchestration pipeline. Instead of a single LLM processing queries, the system uses 7 specialized agents (Understanding, Retrieval, Verification, Reasoning, Risk Assessment, Contradiction, and Response Building) that operate in a supervised chain. It employs hybrid retrieval (ChromaDB for semantic density and BM25 for sparse keywords) and includes a robust Human-in-the-Loop (HITL) fallback mechanism to escalate unverified claims to human experts. 

# PART 2 — PROJECT IN SIMPLE WORDS
**A. Project title:** InsuraLens: Agentic RAG System for Insurance  
**B. Problem statement:** Insurance policies are massive, complex, and full of dense legal jargon. When customers or agents need specific details (like surrender value conditions), finding the exact clause takes too much time, and asking standard AI risks "hallucinations" (made-up answers), which is legally dangerous in insurance.  
**C. Proposed solution:** A smart AI system that doesn't just guess answers, but acts like a team of meticulous researchers. It reads the actual policy documents, verifies its own findings, checks for risks, and provides the answer with exact page citations.  
**D. Main objective:** To provide 100% verifiable, accurate, and safe answers to insurance queries based strictly on uploaded policy documents, minimizing legal risk.  
**E. Who uses the system:** Insurance policyholders (customers) via the main frontend, and Insurance Experts/Administrators via the management frontend.  
**F. What problem the system solves:** Eliminates the risk of AI hallucinations in high-stakes financial/insurance queries and automates document-heavy research.  
**G. Why normal chatbot/LLM is not sufficient:** A normal LLM (like ChatGPT) guesses the next word based on internet training data. It does not know your specific, proprietary insurance policy rules and will confidently invent fake clauses if asked.  
**H. Why RAG is used:** RAG (Retrieval-Augmented Generation) fixes the chatbot problem by first searching a database of *your* uploaded documents, extracting the relevant paragraphs, and forcing the LLM to read *only* those paragraphs to answer the question.  
**I. Why Agentic RAG is used instead of simple RAG:** Simple RAG just hands the retrieved text to the LLM and hopes for the best. Agentic RAG breaks the AI into a "team of workers" (agents). One agent understands the question, another searches, another verifies if the found text actually answers the question, another checks for contradictions, and another formats the answer. It is significantly safer.  

**In simple words:**  
User asks a question → System understands it → Searches insurance documents using keywords and meaning → Verifies if the found evidence is correct → Reasons about the information → Checks for financial/medical risks → Checks for contradictory clauses → Generates an answer with exact citations.

# PART 3 — COMPLETE SYSTEM ARCHITECTURE
**USER** → Types query in UI.  
**FRONTEND** → Next.js React application sends authenticated request.  
**AUTHENTICATION** → API checks JWT token/RBAC permissions.  
**QUERY API** → FastAPI endpoint receives the request and initializes orchestrator.  
**QUERY UNDERSTANDING** → Agent extracts intent (e.g., "surrender_value") and formulates search terms.  
**RETRIEVAL** → Agent queries the vector database and keyword database.  
**HYBRID SEARCH** → Merges results from ChromaDB (embeddings) and BM25 (keywords).  
**VERIFICATION** → Agent grades the retrieved chunks for relevance to the question.  
**REASONING** → Agent processes the verified chunks and deduces the logical answer.  
**RISK ASSESSMENT** → Agent flags if the topic involves high financial or medical risk.  
**CONTRADICTION CHECK** → Agent scans the evidence to see if clause A contradicts clause B.  
**RESPONSE GENERATION** → Agent formats the final text using the reasoning output.  
**GUARDRAILS** → System checks if the AI admitted it doesn't know. If the confidence is too low, it intercepts the response.  
**CITATIONS** → Backend maps the UUIDs of the text chunks back to human-readable filenames and page numbers.  
**FINAL RESPONSE** → Delivered to the user interface.

*Failure & Alternative Flows:*
- **HITL / Review Task flow:** If Verification fails (no relevant docs) or Contradiction is detected, the system safely refuses to answer and creates a `ReviewTask` in PostgreSQL. An expert logs into the Management Portal to resolve it.
- **Provider failure flow:** Handled by `LLMProviderManager`. If OpenRouter fails -> tries Groq -> tries Local Ollama. 
- **Security audit flow:** All queries are logged via `AuditService` into PostgreSQL.

# PART 4 — END-TO-END QUERY FLOW (EXAMPLE)
**Question:** "What is the surrender value of LIC Bima Jyoti?"
1. **Frontend:** User submits the question via the Next.js chat interface.
2. **Query API:** FastAPI `routers/query.py` receives the payload and passes it to the Orchestrator.
3. **QueryUnderstandingAgent:** Analyzes the text. Identifies intent: "policy_surrender". Creates optimized search query: "surrender value calculation LIC Bima Jyoti".
4. **RetrievalAgent:** Converts the query to an embedding using `all-MiniLM-L6-v2`. 
5. **Hybrid Search:** Queries ChromaDB for semantic matches (dense) and BM25 index for keyword matches ("Bima", "Jyoti", "surrender"). Merges and ranks the Top-K results.
6. **VerificationAgent:** The LLM evaluates the Top-K chunks. It confirms that Chunk #3 actually contains the surrender formula.
7. **ReasoningAgent:** The LLM reads Chunk #3 and deduces: "The policy can be surrendered after 2 years. The value is a percentage of premiums paid."
8. **Risk/Contradiction Agents:** Confirm this is a standard financial query with no conflicting clauses in the retrieved text.
9. **ResponseBuilder:** Crafts a user-friendly markdown response.
10. **Backend Mapping:** Attaches `LIC_Bima_Jyoti.pdf (Page 12)` as a citation based on Chunk #3's metadata.
11. **Frontend:** Displays the formatted answer and clickable citation to the user.

# PART 5 — MODELS USED
**1. Embedding Model**
- **Model name:** `all-MiniLM-L6-v2` (via sentence-transformers)
- **Model type:** Dense Vector Embedding Model
- **Purpose:** Converts text into fixed-size arrays of numbers (vectors) representing semantic meaning.
- **Where it is used:** Document Ingestion Pipeline and RetrievalAgent.
- **Why it was selected:** It is extremely lightweight, runs instantly on local CPUs, and provides excellent semantic clustering for general English text. 
- **Embeddings in simple words:** Translates human sentences into coordinates on a map. Sentences with similar meanings are placed close together on the map, allowing ChromaDB to find them instantly.

**2. Main Generation / Reasoning Model**
- **Model name:** `qwen2.5:3b` (Currently configured local default) / `qwen/qwen3.8-27b` (Groq configuration)
- **Model type:** Large Language Model (LLM)
- **Purpose:** Acts as the "brain" for the Agents.
- **Model vs Provider vs Platform:**
  - *Model:* The actual neural network architecture (e.g., Qwen 2.5 3B).
  - *Provider:* The company serving the model via API (e.g., Groq, OpenRouter).
  - *Runtime:* How the model is executed (e.g., Ollama runs it locally on your laptop).

**3. RAG Evaluation Model**
- **Model name:** `qwen2.5:3b` via Ollama
- **Model type:** LLM-as-a-judge
- **Purpose:** Evaluates the system's own answers during automated testing.
- **Why evaluation is heuristic:** We cannot mathematically prove a generated English sentence is "correct." Instead, we ask a separate AI (the judge) to read the answer and the source document, and score whether the answer is factually supported by the document.

# PART 6 — AGENTS USED
| Agent | Main Responsibility | Input | Output |
|---|---|---|---|
| QueryUnderstanding | Analyzes user intent & cleans query | User String | JSON (Intent, Optimized Query) |
| Retrieval | Fetches evidence from DB | Optimized Query | List of Text Chunks |
| Verification | Checks if evidence answers the query | Query + Chunks | Boolean + Confidence Score |
| Reasoning | Deduces the logical answer | Query + Verified Chunks | Logical deduction string |
| RiskAssessment | Flags legal/financial risk | Query + Deduction | Risk Level (Low/High) |
| Contradiction | Checks for conflicting evidence | Verified Chunks | Boolean (Has contradiction?) |
| ResponseBuilder | Formats final markdown string | Deduction + Risk | Formatted Markdown text |

# PART 7 — HYBRID RETRIEVAL SYSTEM
The system relies on Hybrid Retrieval combining two distinct mathematical approaches:
- **Dense Retrieval (ChromaDB):** Understands *meaning*. If you search "cancel policy", it knows to retrieve documents containing "surrender policy" because the vectors are close together.
- **Sparse Retrieval (BM25):** Understands *keywords*. If you search a highly specific ID like "Form 10B-X", BM25 finds the exact keyword match which the dense model might accidentally ignore.
- **How it works:** The RetrievalAgent sends the query to both systems. ChromaDB returns top semantic matches, BM25 returns top keyword matches. The system mathematically merges the scores and takes the Top-K (e.g., top 8) most relevant chunks to feed to the VerificationAgent.

# PART 8 — DOCUMENT INGESTION
**Pipeline flow:** PDF Document → `unstructured` library extracts text → Text is cleaned of special characters → Sliced into overlapping chunks (e.g., 500 tokens) → Metadata (filename, page number) is attached → `all-MiniLM-L6-v2` converts chunks to vectors → Saved into ChromaDB (vectors) and BM25 Index (keywords).

# PART 9 — CHROMADB
ChromaDB is an open-source Vector Database. Normal databases (like SQL) search for exact text matches. Vector databases store arrays of numbers (embeddings) and search using geometry (Cosine Similarity). 
**Simple words:** ChromaDB is like a smart librarian who doesn't just look at the title of a book, but understands the actual meaning of what you are asking and finds paragraphs with the same meaning.

# PART 10 — BM25
BM25 (Best Matching 25) is a sparse retrieval algorithm based on Term Frequency-Inverse Document Frequency (TF-IDF). It scores documents based on how often your exact search keywords appear in a document, while penalizing words that appear everywhere (like "the", "and"). 
**Simple words:** BM25 is a strict keyword-search engine. It ensures that specific insurance terminology is never missed by the AI.
