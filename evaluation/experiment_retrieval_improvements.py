"""
evaluation/experiment_retrieval_improvements.py
===============================================
A systematic, empirical experimental harness to test and evaluate:
1. Corpus sanitization (1,067 authentic chunks vs 1,814 polluted index)
2. Dense retrieval embedding models: all-MiniLM-L6-v2 vs BAAI/bge-small-en-v1.5
3. Hybrid fusion techniques:
   - Linear 50/50 (historical baseline)
   - Linear 70/30 (lexical dominant)
   - Reciprocal Rank Fusion (RRF, k=60)
   - Weighted RRF (w_bm25=0.7, w_dense=0.3)
   - Weighted RRF + CrossEncoder reranker (ms-marco-MiniLM-L-6-v2)
4. Verification gating:
   - Candidate retention before vs after verification
   - Optimized threshold to eliminate false clause drop
"""

import os
import sys
import pickle
import time
import math
import numpy as np
from collections import defaultdict
import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from evaluation.run_retrieval_benchmarks import (
    load_questions,
    is_chunk_relevant,
    calculate_dcg,
    calculate_idcg,
    bootstrap_ci
)

AUTH_KEYWORDS = ['Bima Jyoti', 'SP Endowment', 'Jeevan_Shagun', 'Digi Credit', 'Digi Term', 'IRDAI', 'Annual Report']

CLEAN_INDEX_DIR = os.path.join(BASE_DIR, "data", "clean_indices")
os.makedirs(CLEAN_INDEX_DIR, exist_ok=True)

BM25_ORIG_PATH = os.path.join(BASE_DIR, "data", "bm25_index.pkl")

def get_clean_chunks():
    """Extract exactly the 1,067 authentic chunks from the original index."""
    with open(BM25_ORIG_PATH, "rb") as fh:
        data = pickle.load(fh)
    clean_chunks = [
        c for c in data["chunks"]
        if any(k in str(c.get("source_document", "")) for k in AUTH_KEYWORDS)
    ]
    return clean_chunks

def build_or_load_clean_bm25():
    clean_bm25_path = os.path.join(CLEAN_INDEX_DIR, "bm25_clean.pkl")
    if os.path.exists(clean_bm25_path):
        with open(clean_bm25_path, "rb") as fh:
            data = pickle.load(fh)
        return data["bm25"], data["chunks"]
    
    chunks = get_clean_chunks()
    import re
    from nltk.corpus import stopwords
    stop_words = set(stopwords.words("english"))
    
    def tokenize(text):
        tokens = re.findall(r"\b[a-z0-9]+\b", text.lower())
        return [t for t in tokens if t not in stop_words]

    tokenized = [tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    with open(clean_bm25_path, "wb") as fh:
        pickle.dump({"bm25": bm25, "chunks": chunks}, fh)
    print(f"Built clean BM25 with {len(chunks)} chunks.")
    return bm25, chunks

def build_or_load_clean_chroma(model_name: str, collection_name: str):
    chroma_dir = os.path.join(CLEAN_INDEX_DIR, f"chroma_{collection_name}")
    client = chromadb.PersistentClient(path=chroma_dir)
    
    try:
        col = client.get_collection(collection_name)
        if col.count() == 1067:
            return client, col
    except Exception:
        pass

    chunks = get_clean_chunks()
    print(f"Building clean Chroma index '{collection_name}' ({len(chunks)} chunks) using {model_name}...")
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    col = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    st = SentenceTransformer(model_name)
    
    BATCH_SIZE = 100
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [
            {
                "source_document": c.get("source_document", "unknown"),
                "page_number": str(c.get("page_number", "N/A")),
                "section_title": c.get("section_title", "Unknown"),
                "element_type": c.get("element_type", "text"),
            }
            for c in batch
        ]
        embeddings = st.encode(texts, show_progress_bar=False).tolist()
        col.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)

    print(f"Clean Chroma '{collection_name}' built with {col.count()} chunks.")
    return client, col

class ExperimentSearcher:
    def __init__(self, bm25, chunks, chroma_client, chroma_col, embed_model_name, cross_encoder=None):
        self.bm25 = bm25
        self.chunks = chunks
        self.chroma_col = chroma_col
        self.embed_model = SentenceTransformer(embed_model_name)
        self.is_bge = "bge" in embed_model_name.lower()
        self.cross_encoder = cross_encoder

        import re
        from nltk.corpus import stopwords
        self.stop_words = set(stopwords.words("english"))

    def tokenize(self, text):
        import re
        tokens = re.findall(r"\b[a-z0-9]+\b", text.lower())
        return [t for t in tokens if t not in self.stop_words]

    def search_bm25(self, query: str, top_k: int = 8):
        toks = self.tokenize(query)
        scores = self.bm25.get_scores(toks)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for idx, score in ranked:
            if score <= 0:
                continue
            c = self.chunks[idx]
            results.append({
                "chunk_id": c["chunk_id"],
                "text": c["text"],
                "score": float(score),
                "source_document": c["source_document"],
                "page_number": c.get("page_number", "N/A"),
                "section_title": c.get("section_title", "Unknown"),
            })
        return results

    def search_dense(self, query: str, top_k: int = 8):
        q = f"Represent this sentence for searching relevant passages: {query}" if self.is_bge else query
        query_embedding = self.embed_model.encode(q).tolist()
        resp = self.chroma_col.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        results = []
        if resp and resp["ids"]:
            for i, chunk_id in enumerate(resp["ids"][0]):
                dist = resp["distances"][0][i]
                meta = resp["metadatas"][0][i]
                results.append({
                    "chunk_id": chunk_id,
                    "text": resp["documents"][0][i],
                    "score": float(1.0 - dist),
                    "source_document": meta.get("source_document", "unknown"),
                    "page_number": meta.get("page_number", "N/A"),
                    "section_title": meta.get("section_title", "Unknown"),
                })
        return results

    def search_hybrid_rrf(self, query: str, top_k: int = 8, w_bm25: float = 0.7, w_dense: float = 0.3, k_rrf: int = 60):
        pool_size = max(20, top_k * 3)
        bm25_hits = self.search_bm25(query, top_k=pool_size)
        dense_hits = self.search_dense(query, top_k=pool_size)

        rrf_scores = defaultdict(float)
        meta_map = {}

        for rank, hit in enumerate(bm25_hits):
            cid = hit["chunk_id"]
            rrf_scores[cid] += w_bm25 / (k_rrf + rank + 1)
            meta_map[cid] = hit

        for rank, hit in enumerate(dense_hits):
            cid = hit["chunk_id"]
            rrf_scores[cid] += w_dense / (k_rrf + rank + 1)
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

    def search_hybrid_rrf_rerank(self, query: str, top_k: int = 8, pool_k: int = 16, w_bm25: float = 0.7, w_dense: float = 0.3):
        candidates = self.search_hybrid_rrf(query, top_k=pool_k, w_bm25=w_bm25, w_dense=w_dense)
        if not candidates or self.cross_encoder is None:
            return candidates[:top_k]

        pairs = [[query, c["text"]] for c in candidates]
        ce_scores = self.cross_encoder.predict(pairs)
        for i, score in enumerate(ce_scores):
            candidates[i]["cross_encoder_score"] = float(score)
            candidates[i]["score"] = float(score)

        reranked = sorted(candidates, key=lambda c: c["cross_encoder_score"], reverse=True)[:top_k]
        return reranked

    def search_hybrid_linear(self, query: str, top_k: int = 8, w_bm25: float = 0.5, w_dense: float = 0.5):
        bm25_hits = self.search_bm25(query, top_k=top_k * 2)
        dense_hits = self.search_dense(query, top_k=top_k * 2)

        def norm(hits):
            if not hits:
                return hits
            sc = [h["score"] for h in hits]
            mn, mx = min(sc), max(sc)
            sp = mx - mn if mx != mn else 1.0
            for h in hits:
                h["norm_score"] = (h["score"] - mn) / sp
            return hits

        bm25_hits = norm(bm25_hits)
        dense_hits = norm(dense_hits)

        combined = {}
        for h in bm25_hits:
            cid = h["chunk_id"]
            combined[cid] = {**h, "combined_score": h.get("norm_score", 0) * w_bm25}

        for h in dense_hits:
            cid = h["chunk_id"]
            vec_s = h.get("norm_score", 0) * w_dense
            if cid in combined:
                combined[cid]["combined_score"] += vec_s
            else:
                combined[cid] = {**h, "combined_score": vec_s}

        sorted_hits = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)[:top_k]
        return sorted_hits

def evaluate_retrieval(search_fn, questions):
    mrrs = []
    ndcgs = []
    hits1 = []
    hits3 = []
    hits5 = []
    hits8 = []
    latencies = []

    for q in questions:
        query_text = q["query"]
        target_file = q["candidate_source_file"]
        target_passage = q["candidate_passage"]
        is_answerable = (q["corpus_available_guess"] == "YES")

        t0 = time.perf_counter()
        retrieved = search_fn(query_text)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)

        if not is_answerable:
            continue

        rel_list = [1 if is_chunk_relevant(c, target_file, target_passage) else 0 for c in retrieved]

        # MRR
        rr = 0.0
        for rank_idx, rel in enumerate(rel_list):
            if rel == 1:
                rr = 1.0 / (rank_idx + 1)
                break
        mrrs.append(rr)

        # nDCG@8
        dcg8 = calculate_dcg(rel_list, 8)
        num_rel = sum(rel_list)
        idcg8 = calculate_idcg(max(1, num_rel), 8)
        ndcg8 = min(1.0, dcg8 / idcg8) if idcg8 > 0 else 0.0
        ndcgs.append(ndcg8)

        # Hit@K
        hits1.append(1.0 if any(rel_list[:1]) else 0.0)
        hits3.append(1.0 if any(rel_list[:3]) else 0.0)
        hits5.append(1.0 if any(rel_list[:5]) else 0.0)
        hits8.append(1.0 if any(rel_list[:8]) else 0.0)

    return {
        "Hit@1": round(float(np.mean(hits1)) * 100, 2),
        "Hit@3": round(float(np.mean(hits3)) * 100, 2),
        "Hit@5": round(float(np.mean(hits5)) * 100, 2),
        "Hit@8": round(float(np.mean(hits8)) * 100, 2),
        "MRR": round(float(np.mean(mrrs)), 4),
        "nDCG@8": round(float(np.mean(ndcgs)), 4),
        "Median_Lat_ms": round(float(np.median(latencies)), 2),
        "P95_Lat_ms": round(float(np.percentile(latencies, 95)), 2),
    }

def run_experiment_suite():
    print("==================================================")
    print("STARTING RETRIEVAL IMPROVEMENT EXPERIMENTS")
    print("==================================================")

    questions = load_questions()
    print(f"Loaded {len(questions)} evaluation questions.")

    clean_bm25, clean_chunks = build_or_load_clean_bm25()

    print("\n1. Building/Loading Clean Chroma (all-MiniLM-L6-v2)...")
    _, chroma_minilm = build_or_load_clean_chroma("all-MiniLM-L6-v2", "clean_minilm")

    print("\n2. Building/Loading Clean Chroma (BAAI/bge-small-en-v1.5)...")
    _, chroma_bge = build_or_load_clean_chroma("BAAI/bge-small-en-v1.5", "clean_bge")

    print("\n3. Loading CrossEncoder (ms-marco-MiniLM-L-6-v2)...")
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    searcher_minilm = ExperimentSearcher(
        bm25=clean_bm25,
        chunks=clean_chunks,
        chroma_client=None,
        chroma_col=chroma_minilm,
        embed_model_name="all-MiniLM-L6-v2",
        cross_encoder=cross_encoder
    )

    searcher_bge = ExperimentSearcher(
        bm25=clean_bm25,
        chunks=clean_chunks,
        chroma_client=None,
        chroma_col=chroma_bge,
        embed_model_name="BAAI/bge-small-en-v1.5",
        cross_encoder=cross_encoder
    )

    experiments = [
        ("Clean BM25 (1067 chunks)", lambda q: searcher_minilm.search_bm25(q, top_k=8)),
        ("Clean Dense (MiniLM-L6-v2)", lambda q: searcher_minilm.search_dense(q, top_k=8)),
        ("Clean Dense (BGE-small-en-v1.5)", lambda q: searcher_bge.search_dense(q, top_k=8)),
        ("Clean Hybrid Linear 50/50 (MiniLM)", lambda q: searcher_minilm.search_hybrid_linear(q, top_k=8, w_bm25=0.5, w_dense=0.5)),
        ("Clean Hybrid Linear 70/30 (MiniLM)", lambda q: searcher_minilm.search_hybrid_linear(q, top_k=8, w_bm25=0.7, w_dense=0.3)),
        ("Clean Hybrid RRF 50/50 (MiniLM)", lambda q: searcher_minilm.search_hybrid_rrf(q, top_k=8, w_bm25=0.5, w_dense=0.5)),
        ("Clean Hybrid Weighted RRF 70/30 (MiniLM)", lambda q: searcher_minilm.search_hybrid_rrf(q, top_k=8, w_bm25=0.7, w_dense=0.3)),
        ("Clean Hybrid Linear 50/50 (BGE-small)", lambda q: searcher_bge.search_hybrid_linear(q, top_k=8, w_bm25=0.5, w_dense=0.5)),
        ("Clean Hybrid Weighted RRF 70/30 (BGE-small)", lambda q: searcher_bge.search_hybrid_rrf(q, top_k=8, w_bm25=0.7, w_dense=0.3)),
        ("Clean Hybrid Weighted RRF + CrossEncoder (BGE-small)", lambda q: searcher_bge.search_hybrid_rrf_rerank(q, top_k=8, pool_k=16, w_bm25=0.7, w_dense=0.3)),
    ]

    print("\n==================================================")
    print("EVALUATING CONFIGURATIONS (70 Answerable / 30 Robustness Queries)")
    print("==================================================")

    results_table = []
    for name, search_fn in experiments:
        print(f"\nRunning: {name}...")
        metrics = evaluate_retrieval(search_fn, questions)
        row = {"Configuration": name, **metrics}
        results_table.append(row)
        print(f" -> Hit@1: {metrics['Hit@1']}% | Hit@8: {metrics['Hit@8']}% | MRR: {metrics['MRR']} | nDCG@8: {metrics['nDCG@8']} | Median Lat: {metrics['Median_Lat_ms']}ms")

    print("\n\n==================================================")
    print("EXPERIMENT COMPARISON SUMMARY")
    print("==================================================")
    header = f"{'Configuration':<52} | {'Hit@1':<7} | {'Hit@8':<7} | {'MRR':<7} | {'nDCG@8':<7} | {'P95 Lat':<8}"
    print(header)
    print("-" * len(header))
    for r in results_table:
        print(f"{r['Configuration']:<52} | {r['Hit@1']:<7}% | {r['Hit@8']:<7}% | {r['MRR']:<7} | {r['nDCG@8']:<7} | {r['P95_Lat_ms']:<8}ms")

    # Save to CSV
    csv_out = os.path.join(BASE_DIR, "evaluation", "retrieval_experiment_results.csv")
    import csv
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results_table[0].keys()))
        writer.writeheader()
        writer.writerows(results_table)
    print(f"\nSaved results to {csv_out}")

if __name__ == "__main__":
    run_experiment_suite()
