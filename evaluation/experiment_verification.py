"""
evaluation/experiment_verification.py
=====================================
Empirically tests and evaluates Phase 7 verification strategies:
1. Baseline hard threshold (0.3 on top-8 candidates)
2. Over-fetch + Verification (fetch top-16, verify provenance & quality, output top-8)
3. Adaptive threshold / Soft verification
Measures candidate Hit@1, Hit@8, MRR, nDCG@8, and false rejection rate.
"""

import os
import sys
import pickle
import numpy as np
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from evaluation.run_retrieval_benchmarks import (
    load_questions,
    is_chunk_relevant,
    calculate_dcg,
    calculate_idcg
)
from evaluation.experiment_retrieval_improvements import (
    build_or_load_clean_bm25,
    build_or_load_clean_chroma,
    ExperimentSearcher
)

def run_verification_experiments():
    questions = load_questions()
    bm25, chunks = build_or_load_clean_bm25()
    _, chroma_col = build_or_load_clean_chroma("all-MiniLM-L6-v2", "clean_minilm")

    searcher = ExperimentSearcher(
        bm25=bm25,
        chunks=chunks,
        chroma_client=None,
        chroma_col=chroma_col,
        embed_model_name="all-MiniLM-L6-v2"
    )

    strategies = {}

    # 1. Unverified Hybrid 70/30 (Candidate pool baseline)
    def strategy_unverified(q):
        return searcher.search_hybrid_linear(q, top_k=8, w_bm25=0.7, w_dense=0.3)
    strategies["1. Unverified Hybrid 70/30 (Top-8)"] = strategy_unverified

    # 2. Baseline Hard Threshold 0.3 on Top-8
    def strategy_hard_verif(q):
        hits = searcher.search_hybrid_linear(q, top_k=8, w_bm25=0.7, w_dense=0.3)
        return [c for c in hits if c.get("combined_score", 0.0) >= 0.3 and c.get("source_document") and c.get("source_document") != "unknown"]
    strategies["2. Baseline Hard 0.3 Threshold on Top-8"] = strategy_hard_verif

    # 3. Over-Fetch (16) + Provenance & Quality Verification -> Top-8
    def strategy_overfetch_verif(q):
        candidates = searcher.search_hybrid_linear(q, top_k=16, w_bm25=0.7, w_dense=0.3)
        verified = []
        for c in candidates:
            # Provenance checks
            doc = c.get("source_document")
            if not doc or doc in ("unknown", "None", ""):
                continue
            text = c.get("text", "").strip()
            if len(text) < 20: # noise / blank
                continue
            # Quality / min threshold
            if c.get("combined_score", 0.0) < 0.05:
                continue
            verified.append(c)
            if len(verified) == 8:
                break
        return verified
    strategies["3. Over-Fetch (16) + Provenance Verification -> Top-8"] = strategy_overfetch_verif

    # 4. Adaptive Rank-Preserving Verification
    def strategy_adaptive_verif(q):
        candidates = searcher.search_hybrid_linear(q, top_k=8, w_bm25=0.7, w_dense=0.3)
        verified = []
        for c in candidates:
            doc = c.get("source_document")
            if not doc or doc in ("unknown", "None", ""):
                continue
            text = c.get("text", "").strip()
            if len(text) < 20:
                continue
            verified.append(c)
        return verified
    strategies["4. Provenance Verification without Score Dropping (Top-8)"] = strategy_adaptive_verif

    print(f"\nEvaluating Verification Strategies on {len(questions)} queries...")
    results = []

    for name, s_fn in strategies.items():
        hits1, hits8, mrrs, ndcgs = [], [], [], []
        false_drops = 0
        total_relevant_in_candidates = 0

        for q in questions:
            if q["corpus_available_guess"] != "YES":
                continue
            target_file = q["candidate_source_file"]
            target_passage = q["candidate_passage"]

            raw_cand = searcher.search_hybrid_linear(q["query"], top_k=8, w_bm25=0.7, w_dense=0.3)
            raw_rels = [1 if is_chunk_relevant(c, target_file, target_passage) else 0 for c in raw_cand]
            had_rel_in_raw = any(raw_rels)
            if had_rel_in_raw:
                total_relevant_in_candidates += 1

            retrieved = s_fn(q["query"])
            ret_rels = [1 if is_chunk_relevant(c, target_file, target_passage) else 0 for c in retrieved]
            has_rel_in_ret = any(ret_rels)

            if had_rel_in_raw and not has_rel_in_ret:
                false_drops += 1

            hits1.append(1.0 if any(ret_rels[:1]) else 0.0)
            hits8.append(1.0 if any(ret_rels[:8]) else 0.0)

            # MRR
            rr = 0.0
            for r_idx, rel in enumerate(ret_rels):
                if rel == 1:
                    rr = 1.0 / (r_idx + 1)
                    break
            mrrs.append(rr)

            # nDCG@8
            dcg = calculate_dcg(ret_rels, 8)
            num_rel = sum(ret_rels)
            idcg = calculate_idcg(max(1, num_rel), 8)
            ndcg = min(1.0, dcg / idcg) if idcg > 0 else 0.0
            ndcgs.append(ndcg)

        false_drop_rate = round((false_drops / total_relevant_in_candidates) * 100, 2) if total_relevant_in_candidates else 0.0
        results.append({
            "Strategy": name,
            "Hit@1": f"{round(float(np.mean(hits1))*100, 2)}%",
            "Hit@8": f"{round(float(np.mean(hits8))*100, 2)}%",
            "MRR": round(float(np.mean(mrrs)), 4),
            "nDCG@8": round(float(np.mean(ndcgs)), 4),
            "False_Rejections": false_drops,
            "False_Rejection_Rate": f"{false_drop_rate}%"
        })

    print("\n==========================================================================================")
    print("VERIFICATION STRATEGY COMPARISON")
    print("==========================================================================================")
    for r in results:
        print(f"{r['Strategy']:<55} | Hit@8: {r['Hit@8']} | MRR: {r['MRR']} | False Drops: {r['False_Rejections']} ({r['False_Rejection_Rate']})")

if __name__ == "__main__":
    run_verification_experiments()
