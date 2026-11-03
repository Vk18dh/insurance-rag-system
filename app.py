#phase 1 complete
"""
app.py — Hybrid Retrieval + Grounded QA Interface.

Combines BM25 keyword search and ChromaDB vector search (50/50 weighting),
deduplicates results, and passes context to an LLM acting as an
"Insurance Auditor" for grounded, citation-backed answers.
"""

import os
import pickle
import re
import sys
import argparse

from config import (
    BM25_INDEX_PATH,
    BM25_WEIGHT,
    CHROMA_COLLECTION_NAME,
    CHROMA_DIR,
    EMBEDDING_MODEL,
    FUSION_METHOD,
    LLM_MODEL,
    TOP_K,
    VECTOR_WEIGHT,
    setup_logging,
)

logger = setup_logging()

# ═══════════════════════════════════════════════════════════════════════════
#  Insurance Auditor System Prompt
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are an Insurance Auditor AI. Your role is to answer questions about insurance policies and regulations STRICTLY using the provided context.

RULES — follow these without exception:
1. Answer ONLY using the information in the CONTEXT below.
2. DO NOT use any external knowledge, training data, or assumptions.
3. If the answer cannot be found in the provided context, respond EXACTLY with:
   "I could not find this information in the provided documents."
4. Provide a highly detailed, comprehensive explanation. Be exhaustive and extract every single rule, numerical value, waiting period, option, and definition provided in the text.
5. DO NOT apologize if specific math formulas are missing. Simply provide an extremely rich, detailed, and completely exhaustive summary of the components you DO have.
6. Tailor the depth and focus to the user's prompt organically. Break down the information clearly using bullet points and structured paragraphs.
7. DO NOT manually place inline citations (like "[1]") directly in the sentences. Just write the answer in plain English.

CONTEXT:
{context}

USER QUESTION:
{question}

ANSWER (with citations):"""


# ═══════════════════════════════════════════════════════════════════════════
#  BM25 Search
# ═══════════════════════════════════════════════════════════════════════════

_bm25_cache = None
_bm25_chunks_cache = None

def _load_bm25():
    """Load the persisted BM25 index and chunk list."""
    global _bm25_cache, _bm25_chunks_cache
    if _bm25_cache is not None:
        return _bm25_cache, _bm25_chunks_cache

    if not os.path.isfile(BM25_INDEX_PATH):
        logger.error("BM25 index not found at %s. Run index.py first.", BM25_INDEX_PATH)
        return None, None

    with open(BM25_INDEX_PATH, "rb") as fh:
        data = pickle.load(fh)
        
    _bm25_cache = data["bm25"]
    _bm25_chunks_cache = data["chunks"]
    return _bm25_cache, _bm25_chunks_cache


def _tokenize(text: str) -> list[str]:
    """Mirror the tokenizer from index.py."""
    import nltk
    from nltk.corpus import stopwords

    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", quiet=True)

    stop_words = set(stopwords.words("english"))
    tokens = re.findall(r"\b[a-z0-9]+\b", text.lower())
    return [t for t in tokens if t not in stop_words]


def bm25_search(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve top-k chunks via BM25 keyword search.

    Returns:
        List of dicts with keys: chunk_id, text, score, metadata
    """
    bm25, chunks = _load_bm25()
    if bm25 is None:
        return []

    tokenized_query = _tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for idx, score in ranked:
        if score <= 0:
            continue
        c = chunks[idx]
        results.append({
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "score": float(score),
            "source_document": c["source_document"],
            "page_number": c["page_number"],
            "section_title": c["section_title"],
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  Vector Search — ChromaDB
# ═══════════════════════════════════════════════════════════════════════════

_embedding_model_cache = None
_chroma_client_cache = None
_chroma_collection_cache = None

def _get_embedding_model():
    global _embedding_model_cache
    if _embedding_model_cache is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model_cache = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
    return _embedding_model_cache

def _get_chroma_collection():
    global _chroma_client_cache, _chroma_collection_cache
    if _chroma_collection_cache is None:
        import chromadb
        _chroma_client_cache = chromadb.PersistentClient(path=CHROMA_DIR)
        _chroma_collection_cache = _chroma_client_cache.get_collection(name=CHROMA_COLLECTION_NAME)
    return _chroma_collection_cache

def vector_search(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve top-k chunks via ChromaDB cosine-similarity search.

    Returns:
        List of dicts with keys: chunk_id, text, score, metadata
    """
    if not os.path.isdir(CHROMA_DIR):
        logger.error("ChromaDB directory not found: %s. Run index.py first.", CHROMA_DIR)
        return []

    model = _get_embedding_model()
    # Support instruction-tuned models like BGE
    if "bge" in EMBEDDING_MODEL.lower():
        encoded_query = f"Represent this sentence for searching relevant passages: {query}"
    else:
        encoded_query = query
    query_embedding = model.encode(encoded_query).tolist()

    collection = _get_chroma_collection()

    response = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    if response and response["ids"]:
        for i, chunk_id in enumerate(response["ids"][0]):
            distance = response["distances"][0][i]
            # Convert cosine distance → similarity score (1 - distance)
            score = 1.0 - distance
            meta = response["metadatas"][0][i]

            results.append({
                "chunk_id": chunk_id,
                "text": response["documents"][0][i],
                "score": float(score),
                "source_document": meta.get("source_document", "unknown"),
                "page_number": meta.get("page_number", "N/A"),
                "section_title": meta.get("section_title", "Unknown"),
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  Hybrid Retrieval (Linear, RRF, or Cross-Encoder Reranking)
# ═══════════════════════════════════════════════════════════════════════════

def _normalise_scores(results: list[dict]) -> list[dict]:
    """Min-max normalise scores to [0, 1]."""
    if not results:
        return results

    scores = [r["score"] for r in results]
    min_s, max_s = min(scores), max(scores)
    spread = max_s - min_s if max_s != min_s else 1.0

    for r in results:
        r["norm_score"] = (r["score"] - min_s) / spread

    return results


def hybrid_search(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Combine BM25 and vector search results with configurable weights and fusion strategies.

    Strategies supported:
      - 'linear': Min-max normalized linear combination (BM25_WEIGHT * s_bm25 + VECTOR_WEIGHT * s_dense)
      - 'rrf': Reciprocal Rank Fusion (k=60)
      - 'rerank': RRF candidate retrieval + CrossEncoder reranker
    """
    if FUSION_METHOD == "rrf":
        pool_size = max(20, top_k * 3)
        bm25_hits = bm25_search(query, top_k=pool_size)
        dense_hits = vector_search(query, top_k=pool_size)

        rrf_scores = {}
        meta_map = {}
        k_rrf = 60

        for rank, hit in enumerate(bm25_hits):
            cid = hit["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (BM25_WEIGHT / (k_rrf + rank + 1))
            meta_map[cid] = hit

        for rank, hit in enumerate(dense_hits):
            cid = hit["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (VECTOR_WEIGHT / (k_rrf + rank + 1))
            if cid not in meta_map:
                meta_map[cid] = hit

        ranked_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]
        results = []
        for cid in ranked_cids:
            hit = dict(meta_map[cid])
            hit["score"] = float(rrf_scores[cid])
            hit["combined_score"] = float(rrf_scores[cid])
            results.append(hit)
        return results

    # Default: Weighted Linear Fusion
    bm25_results = _normalise_scores(bm25_search(query, top_k=top_k * 2))
    vector_results = _normalise_scores(vector_search(query, top_k=top_k * 2))

    # Merge into a dict keyed by chunk_id
    combined: dict[str, dict] = {}

    for r in bm25_results:
        cid = r["chunk_id"]
        combined[cid] = {
            **r,
            "combined_score": r.get("norm_score", 0) * BM25_WEIGHT,
        }

    for r in vector_results:
        cid = r["chunk_id"]
        vec_score = r.get("norm_score", 0) * VECTOR_WEIGHT
        if cid in combined:
            combined[cid]["combined_score"] += vec_score
        else:
            combined[cid] = {**r, "combined_score": vec_score}

    # Sort by combined score descending and return top_k
    ranked = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)
    return ranked[:top_k]


# ═══════════════════════════════════════════════════════════════════════════
#  Grounded QA — LLM Answer Generation
# ═══════════════════════════════════════════════════════════════════════════

def _format_context(chunks: list[dict]) -> str:
    """Format retrieved chunks as numbered context blocks for the prompt."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(
            f"[{i}] (Source: {c['source_document']}, Page: {c['page_number']}, "
            f"Section: {c['section_title']})\n{c['text']}"
        )
    return "\n\n".join(blocks)


def answer_query(query: str) -> dict:
    """
    End-to-end: retrieve context via hybrid search, generate grounded answer.

    Returns:
        Dict with keys: query, answer, sources
    """
    # Retrieve context
    chunks = hybrid_search(query, top_k=TOP_K)

    if not chunks:
        return {
            "query": query,
            "answer": "I could not find this information in the provided documents.",
            "sources": [],
        }

    context = _format_context(chunks)
    prompt = SYSTEM_PROMPT.format(context=context, question=query)

    # Use keys from config
    from config import OPENROUTER_API_KEY, GOOGLE_API_KEY

    # Generate answer via OpenRouter (Primary) or Google Gemini SDK (Secondary)
    try:
        import json
        import urllib.request
        
        # 1. OpenRouter (Primary)
        if OPENROUTER_API_KEY:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Insurance Auditor"
            }
            # Correct OpenRouter mapping based on available_models.txt
            model_map = {
                "gemma-3-27b-it": "google/gemma-3-27b-it:free",
                "gemini-2.0-flash": "google/gemini-2.0-flash-001",
                "gemini-1.5-flash": "google/gemini-flash-1.5"
            }
            or_model = model_map.get(LLM_MODEL, f"google/{LLM_MODEL}" if "/" not in LLM_MODEL else LLM_MODEL)
            
            payload = {
                "model": or_model,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    answer_text = result["choices"][0]["message"]["content"]
                    # If success, return immediately
                    sources = [{"source_document": c["source_document"], "page_number": c["page_number"], "section_title": c["section_title"]} for c in chunks]
                    return {"query": query, "answer": answer_text, "sources": sources}
            except Exception as e:
                logger.error("OpenRouter failed: %s", e)

        # 2. Google Gemini SDK (Secondary)
        if GOOGLE_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Correct prefix handling for Google SDK
            native_model = LLM_MODEL
            if not native_model.startswith("models/"):
                native_model = f"models/{native_model}"
            model = genai.GenerativeModel(native_model)
            
            response = model.generate_content(prompt)
            answer_text = response.text
        else:
            raise Exception("No working API key or service responded.")

    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        answer_text = (
            f"[SYSTEM WARNING: LLM request failed. Real Error: {str(exc)}]\n\n"
            + "\n".join(f"► {c['text'][:500]}..." for c in chunks)
        )

    sources = [
        {
            "source_document": c["source_document"],
            "page_number": c["page_number"],
            "section_title": c["section_title"],
        }
        for c in chunks
    ]

    return {"query": query, "answer": answer_text, "sources": sources}


# ═══════════════════════════════════════════════════════════════════════════
#  CLI Interface
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Interactive CLI for the Insurance Knowledge Assessment System."""
    parser = argparse.ArgumentParser(
        description="AI-Driven Insurance Knowledge Assessment System"
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run document ingestion before querying.",
    )
    parser.add_argument(
        "--index",
        action="store_true",
        help="Build/rebuild indices before querying.",
    )
    args = parser.parse_args()

    if args.ingest:
        from ingest import run_ingestion
        run_ingestion()

    if args.index:
        from index import build_index
        build_index()

    print("\n" + "=" * 60)
    print("  Insurance Knowledge Assessment System")
    print("  Type your question below.  Type 'quit' to exit.")
    print("=" * 60 + "\n")

    while True:
        try:
            query = input("📋 Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        print("\n🔍 Searching...\n")
        result = answer_query(query)

        print("─" * 60)
        print("📝 ANSWER:\n")
        print(result["answer"])
        print("\n📚 SOURCES:")
        for s in result["sources"]:
            print(
                f"   • {s['source_document']} — Page {s['page_number']} "
                f"({s.get('section_title', '')})"
            )
        print("─" * 60 + "\n")


if __name__ == "__main__":
    main()
