"""
evaluation/run_controlled_comparison.py
=======================================
Conducts a strictly controlled, head-to-head empirical comparison
using the IDENTICAL 1,067 clean canonical chunks and the IDENTICAL 100 test queries.

Configurations evaluated on the identical 1,067 chunk corpus:
1. BM25 (Canonical 1,067)
2. Original Dense: all-MiniLM-L6-v2 (Canonical 1,067)
3. Original Hybrid: 50/50 Linear Min-Max (MiniLM + BM25, Canonical 1,067)
4. Original Hybrid + Verification: Hard Threshold 0.3 (MiniLM, Canonical 1,067)
5. Improved Dense: BAAI/bge-small-en-v1.5 (Canonical 1,067)
6. Improved Hybrid: 70/30 Weighted Linear (BGE-small + BM25, Canonical 1,067)
7. Improved Hybrid + Verification: Provenance & Soft Threshold 0.05 (BGE-small + BM25, Canonical 1,067)
8. Improved Hybrid RRF: Weighted Reciprocal Rank Fusion k=60 (BGE-small + BM25, Canonical 1,067)

Measures:
- Hit@1, Hit@3, Hit@5, Hit@8
- MRR, nDCG@8
- Latency: median, p95, mean
- 95% Bootstrap CIs (1,000 iterations)
- Detailed failure analysis per query
"""

import os
import sys
import time
import json
import csv
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
    calculate_idcg,
    bootstrap_ci
)
from evaluation.experiment_retrieval_improvements import (
    build_or_load_clean_bm25,
    build_or_load_clean_chroma,
    ExperimentSearcher
)
from backend.app.services.guardrail_service import GuardrailService

def run_controlled_comparison():
    print("=" * 80)
    print("STRICTLY CONTROLLED RETRIEVAL COMPARISON (IDENTICAL 1,067 CHUNKS)")
    print("=" * 80)

    # 1. Load canonical 1,067 BM25 and chunks
    bm25, chunks = build_or_load_clean_bm25()
    print(f"Verified Canonical Chunks Count: {len(chunks)}")
    assert len(chunks) == 1067, f"Expected 1067 chunks, got {len(chunks)}"

    # 2. Load MiniLM Chroma collection
    _, chroma_minilm = build_or_load_clean_chroma("all-MiniLM-L6-v2", "clean_minilm")
    searcher_minilm = ExperimentSearcher(bm25, chunks, None, chroma_minilm, "all-MiniLM-L6-v2")

    # 3. Load BGE-small Chroma collection
    _, chroma_bge = build_or_load_clean_chroma("BAAI/bge-small-en-v1.5", "clean_bge")
    searcher_bge = ExperimentSearcher(bm25, chunks, None, chroma_bge, "BAAI/bge-small-en-v1.5")

    # 4. Load 100 evaluation questions
    questions = load_questions()
    answerable_q = [q for q in questions if q["corpus_available_guess"] == "YES"]
    print(f"Total Queries: {len(questions)} | Answerable Queries: {len(answerable_q)}")

    # Define Configurations
    configurations = {
        "1_BM25_Clean": {
            "name": "Canonical BM25",
            "type": "Lexical",
            "model": "BM25Okapi",
            "weights": "BM25 1.0",
            "search_fn": lambda q: searcher_bge.search_bm25(q, top_k=8)
        },
        "2_Dense_MiniLM_Original": {
            "name": "Original Dense (MiniLM)",
            "type": "Dense",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "weights": "Dense 1.0",
            "search_fn": lambda q: searcher_minilm.search_dense(q, top_k=8)
        },
        "3_Hybrid_50_50_MiniLM_Original": {
            "name": "Original Hybrid 50/50 (MiniLM)",
            "type": "Hybrid Linear",
            "model": "BM25 + MiniLM-L6-v2",
            "weights": "50% BM25 / 50% Dense",
            "search_fn": lambda q: searcher_minilm.search_hybrid_linear(q, top_k=8, w_bm25=0.5, w_dense=0.5)
        },
        "4_Hybrid_Verif_0_3_MiniLM_Original": {
            "name": "Original Hybrid + Verif 0.3 (MiniLM)",
            "type": "Hybrid + Threshold Filter",
            "model": "BM25 + MiniLM-L6-v2 + Verif 0.3",
            "weights": "50% BM25 / 50% Dense (score >= 0.3)",
            "search_fn": lambda q: [
                c for c in searcher_minilm.search_hybrid_linear(q, top_k=8, w_bm25=0.5, w_dense=0.5)
                if c.get("combined_score", 0.0) >= 0.3 and c.get("source_document") and c.get("source_document") != "unknown"
            ]
        },
        "5_Dense_BGE_Improved": {
            "name": "Improved Dense (BGE-small-v1.5)",
            "type": "Dense",
            "model": "BAAI/bge-small-en-v1.5",
            "weights": "Dense 1.0 (with query prefix)",
            "search_fn": lambda q: searcher_bge.search_dense(q, top_k=8)
        },
        "6_Hybrid_70_30_BGE_Improved": {
            "name": "Improved Hybrid 70/30 (BGE-small)",
            "type": "Hybrid Linear",
            "model": "BM25 + BGE-small-en-v1.5",
            "weights": "70% BM25 / 30% Dense",
            "search_fn": lambda q: searcher_bge.search_hybrid_linear(q, top_k=8, w_bm25=0.7, w_dense=0.3)
        },
        "7_Hybrid_Verif_Provenance_BGE_Improved": {
            "name": "Improved Hybrid + Provenance Verif (BGE-small)",
            "type": "Hybrid + Provenance Filter",
            "model": "BM25 + BGE-small-en-v1.5 + Provenance",
            "weights": "70% BM25 / 30% Dense (provenance checked)",
            "search_fn": lambda q: [
                c for c in searcher_bge.search_hybrid_linear(q, top_k=8, w_bm25=0.7, w_dense=0.3)
                if c.get("source_document") and c.get("source_document") not in ("unknown", "None", "")
                and len(c.get("text", "").strip()) >= 20 and c.get("combined_score", 0.0) >= 0.05
            ]
        },
        "8_Hybrid_RRF_BGE_Improved": {
            "name": "Improved Hybrid Weighted RRF k=60 (BGE-small)",
            "type": "Hybrid RRF",
            "model": "BM25 + BGE-small-en-v1.5",
            "weights": "RRF k=60 (w_bm25=0.7, w_dense=0.3)",
            "search_fn": lambda q: searcher_bge.search_hybrid_rrf(q, top_k=8, k_rrf=60, w_bm25=0.7, w_dense=0.3)
        }
    }

    summary_results = {}
    failure_records = defaultdict(list)
    per_query_results = []

    for cfg_id, cfg in configurations.items():
        print(f"\nEvaluating: {cfg['name']} ...")
        latencies = []
        hits1, hits3, hits5, hits8 = [], [], [], []
        mrrs, ndcgs = [], []
        category_stats = defaultdict(lambda: {"hits8": [], "mrr": []})

        for q in questions:
            is_ans = (q["corpus_available_guess"] == "YES")
            t_file = q["candidate_source_file"]
            t_pass = q["candidate_passage"]
            cat = q["category"]

            t0 = time.perf_counter()
            retrieved = cfg["search_fn"](q["query"])
            lat_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat_ms)

            if is_ans:
                # Binary relevance
                rels = [1 if is_chunk_relevant(c, t_file, t_pass) else 0 for c in retrieved]

                h1 = 1.0 if any(rels[:1]) else 0.0
                h3 = 1.0 if any(rels[:3]) else 0.0
                h5 = 1.0 if any(rels[:5]) else 0.0
                h8 = 1.0 if any(rels[:8]) else 0.0

                hits1.append(h1)
                hits3.append(h3)
                hits5.append(h5)
                hits8.append(h8)

                # MRR
                rr = 0.0
                for rank_idx, r_val in enumerate(rels):
                    if r_val == 1:
                        rr = 1.0 / (rank_idx + 1)
                        break
                mrrs.append(rr)

                # nDCG@8
                dcg = calculate_dcg(rels, 8)
                num_rel = sum(rels)
                idcg = calculate_idcg(max(1, num_rel), 8)
                ndcg = min(1.0, dcg / idcg) if idcg > 0 else 0.0
                ndcgs.append(ndcg)

                category_stats[cat]["hits8"].append(h8)
                category_stats[cat]["mrr"].append(rr)

                # Failure tracking
                if h8 == 0.0:
                    failure_records[cfg_id].append({
                        "case_id": q["case_id"],
                        "category": cat,
                        "query": q["query"],
                        "target_file": t_file,
                        "retrieved_top3": [
                            {"doc": c.get("source_document"), "page": c.get("page_number"), "score": round(c.get("score", c.get("combined_score", 0.0)), 4)}
                            for c in retrieved[:3]
                        ]
                    })

        # Calculate aggregates
        summary_results[cfg_id] = {
            "name": cfg["name"],
            "type": cfg["type"],
            "model": cfg["model"],
            "weights": cfg["weights"],
            "Hit@1": round(float(np.mean(hits1)) * 100, 2),
            "Hit@3": round(float(np.mean(hits3)) * 100, 2),
            "Hit@5": round(float(np.mean(hits5)) * 100, 2),
            "Hit@8": round(float(np.mean(hits8)) * 100, 2),
            "Hit@8_95CI": [round(x * 100, 2) for x in bootstrap_ci(hits8)],
            "MRR": round(float(np.mean(mrrs)), 4),
            "MRR_95CI": list(bootstrap_ci(mrrs)),
            "nDCG@8": round(float(np.mean(ndcgs)), 4),
            "nDCG@8_95CI": list(bootstrap_ci(ndcgs)),
            "Median_Latency_ms": round(float(np.median(latencies)), 2),
            "P95_Latency_ms": round(float(np.percentile(latencies, 95)), 2),
            "Mean_Latency_ms": round(float(np.mean(latencies)), 2),
            "Failures_Count": len(failure_records[cfg_id]),
            "Categories": {
                c: {
                    "Hit@8": round(float(np.mean(data["hits8"])) * 100, 2),
                    "MRR": round(float(np.mean(data["mrr"])), 4)
                }
                for c, data in category_stats.items()
            }
        }

    # Print Comparison Table
    print("\n" + "=" * 125)
    print(f"{'Configuration':<45} | {'Hit@1':<7} | {'Hit@8':<7} | {'MRR':<7} | {'nDCG@8':<7} | {'Med Lat':<8} | {'P95 Lat':<8} | {'Fails':<5}")
    print("=" * 125)
    for cfg_id, r in summary_results.items():
        print(f"{r['name']:<45} | {r['Hit@1']:<6}% | {r['Hit@8']:<6}% | {r['MRR']:<7} | {r['nDCG@8']:<7} | {r['Median_Latency_ms']:<5}ms | {r['P95_Latency_ms']:<5}ms | {r['Failures_Count']:<5}")
    print("=" * 125)

    # Save to disk
    os.makedirs(os.path.join(BASE_DIR, "evaluation"), exist_ok=True)
    out_json = os.path.join(BASE_DIR, "evaluation", "controlled_comparison_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=2)
    print(f"\nSaved summary to: {out_json}")

    out_csv = os.path.join(BASE_DIR, "evaluation", "controlled_comparison_table.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Config_ID", "Name", "Type", "Model", "Weights", "Hit@1", "Hit@3", "Hit@5", "Hit@8", "Hit@8_LowerCI", "Hit@8_UpperCI", "MRR", "MRR_LowerCI", "MRR_UpperCI", "nDCG@8", "Median_Lat_ms", "P95_Lat_ms", "Failures"])
        for cfg_id, r in summary_results.items():
            writer.writerow([
                cfg_id, r["name"], r["type"], r["model"], r["weights"],
                r["Hit@1"], r["Hit@3"], r["Hit@5"], r["Hit@8"],
                r["Hit@8_95CI"][0], r["Hit@8_95CI"][1],
                r["MRR"], r["MRR_95CI"][0], r["MRR_95CI"][1],
                r["nDCG@8"], r["Median_Latency_ms"], r["P95_Latency_ms"],
                r["Failures_Count"]
            ])
    print(f"Saved CSV table to: {out_csv}")

    out_fails = os.path.join(BASE_DIR, "evaluation", "controlled_comparison_failures.json")
    with open(out_fails, "w", encoding="utf-8") as f:
        json.dump(failure_records, f, indent=2)
    print(f"Saved failure analysis to: {out_fails}")

if __name__ == "__main__":
    run_controlled_comparison()
