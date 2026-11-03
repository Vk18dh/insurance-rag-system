# PART 10 — DOCUMENT INGESTION CODE
**Flow:** PDF -> Extraction -> Cleaning -> Chunking -> Metadata -> Embedding -> ChromaDB/BM25.
1. **Extraction:** The system uses the `unstructured` library (`unstructured[all-docs]`) to convert PDF layouts into raw strings.
2. **Chunking & Overlap:** To avoid feeding a 500-page document into the LLM, the text is sliced into chunks. Overlap is crucial so that a sentence split between two chunks doesn't lose its meaning.
3. **Metadata:** Each chunk receives a UUID, a `document_id` (filename), and `page_number`. This metadata is stored alongside the vector in ChromaDB.
4. **Insertion:** The text is passed to `sentence-transformers` for embedding, then pushed into ChromaDB. The raw string is added to the `rank-bm25` index.

# PART 11 — EMBEDDING MODEL DEEP DIVE
**Model:** `all-MiniLM-L6-v2`
**Architecture:** A lightweight Transformer model.
**What embeddings are:** It takes a sentence and outputs a 384-dimensional vector (an array of 384 floating-point numbers). Sentences with similar meanings produce vectors that are geometrically close.
**Where it is loaded:** Locally on the CPU/GPU via the `sentence-transformers` Python package.
**Why it was selected:** 
- *Alternatives:* BGE-m3, E5-large, OpenAI text-embedding-3.
- *Reasoning:* While BGE or OpenAI might score 2% higher on retrieval benchmarks, they require massive VRAM or paid cloud APIs. `all-MiniLM-L6-v2` is selected because this project prioritizes a completely local, air-gapped, privacy-first deployment on consumer hardware. It provides excellent semantic clustering for English text at a fraction of the computational cost.

# PART 12 — CHROMADB CODE
**What it is:** A local vector database.
**How it is used:** The `RetrievalAgent` passes the user's embedded query to ChromaDB. ChromaDB calculates the Cosine Similarity between the query vector and all millions of document chunk vectors. It returns the chunks with the smallest geometric distance.
**Simple words:** It's a search engine that understands synonyms. If you search "dog", it will find documents containing "puppy" because their vectors are close.

# PART 13 — BM25 CODE
**What it is:** A sparse retrieval engine using `rank-bm25`.
**How it works:** It uses TF-IDF (Term Frequency - Inverse Document Frequency). If you search for "Form-10B", it counts how many times "Form-10B" appears in a chunk. It heavily penalizes words that appear everywhere (like "the", "policy").
**Why used:** ChromaDB often fails at exact alphanumeric matches. BM25 guarantees that exact policy IDs or names are found perfectly.

# PART 14 — HYBRID RETRIEVAL LOGIC
**The Combination:**
The system queries both ChromaDB and BM25 simultaneously. 
1. ChromaDB returns a list of chunks scored by semantic distance.
2. BM25 returns a list of chunks scored by keyword frequency.
3. Because Chroma scores and BM25 scores use completely different math scales, the scores are *normalized* (scaled between 0 and 1).
4. The normalized scores are summed (typically 50/50 weighting).
5. Duplicates (chunks found by both systems) have their scores combined, pushing them to the top of the ranking.
6. The system takes the **Top-K** (highest combined scores) and passes them to the VerificationAgent. 

**Worked Example:**
Query: "What is the surrender value of LIC Bima Jyoti?"
- Chunk A (Semantic match: explains surrender value formula, but doesn't explicitly name the policy): Chroma Score: 0.9, BM25 Score: 0.1 -> Combined: 1.0
- Chunk B (Keyword match: mentions "LIC Bima Jyoti surrender" in a table of contents): Chroma Score: 0.4, BM25 Score: 0.8 -> Combined: 1.2
- Chunk B wins the ranking because both semantic and exact keyword components were present.
