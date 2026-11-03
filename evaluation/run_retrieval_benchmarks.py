import csv
import json
import math
import os
import time
import numpy as np
from collections import defaultdict

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import retrieval functions from app.py
from app import bm25_search, vector_search, hybrid_search, TOP_K
from backend.app.services.guardrail_service import GuardrailService
from phase2.config.settings import Phase2Settings
CSV_PATH = os.path.join(os.path.dirname(__file__), "questions_for_review.csv")
JSONL_PATH = os.path.join(os.path.dirname(__file__), "raw_run_records.jsonl")
METRIC_TABLE_PATH = os.path.join(os.path.dirname(__file__), "metric_tables.csv")
SUMMARY_JSON_PATH = os.path.join(os.path.dirname(__file__), "summary.json")

def load_questions():
    questions = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)
    return questions

def is_chunk_relevant(chunk, target_file, target_passage):
    """
    Check if retrieved chunk matches candidate source and passage text.
    Relevance is positive if:
    1. Chunk source_document matches target_file (case-insensitive substring)
    AND
    2. Overlap between chunk text and candidate passage is significant.
    """
    if target_file in ("NONE", "SECURITY_PROBE", ""):
        return False

    chunk_src = chunk.get("source_document", "").lower()
    tgt_src = target_file.lower()
    if tgt_src not in chunk_src and chunk_src not in tgt_src:
        return False

    # Check text overlap
    c_words = set(chunk.get("text", "").lower().split())
    p_words = set(target_passage.lower().split())
    if not p_words:
        return True
    
    overlap = len(c_words.intersection(p_words))
    # If at least 3 significant words or 25% overlap
    return overlap >= 3 or (len(p_words) > 0 and (overlap / len(p_words)) >= 0.25)

def calculate_dcg(rel_list, k):
    dcg = 0.0
    for i in range(min(k, len(rel_list))):
        rel = rel_list[i]
        dcg += rel / math.log2(i + 2)
    return dcg

def calculate_idcg(num_rel, k):
    idcg = 0.0
    for i in range(min(k, num_rel)):
        idcg += 1.0 / math.log2(i + 2)
    return idcg

def bootstrap_ci(values, n_boot=1000, ci=0.95):
    """Compute 95% bootstrap confidence interval."""
    if not values:
        return (0.0, 0.0)
    arr = np.array(values)
    boot_means = []
    n = len(arr)
    rng = np.random.default_rng(42)
    for _ in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means.append(np.mean(sample))
    lower = float(np.percentile(boot_means, (1 - ci) / 2 * 100))
    upper = float(np.percentile(boot_means, (1 + ci) / 2 * 100))
    return (round(lower, 4), round(upper, 4))

def apply_verification(hybrid_chunks, similarity_threshold=0.05):
    """
    Applies Phase 2 Verification / Gatekeeper rules:
    - Validates provenance (non-empty source document, valid text length)
    - Rejects malformed or corrupted text blocks
    - Filters out near-zero spurious noise without discarding valid multi-clause evidence
    """
    verified = []
    for c in hybrid_chunks:
        doc = c.get("source_document")
        if not doc or doc in ("unknown", "None", ""):
            continue
        text = c.get("text", "").strip()
        if len(text) < 20:
            continue
        score = c.get("combined_score", c.get("score", 0.0))
        if score < similarity_threshold:
            continue
        verified.append(c)
    return verified

def run_benchmarks():
    print("=== Running Controlled Retrieval Benchmarks ===")
    questions = load_questions()
    print(f"Loaded {len(questions)} test cases.")

    # Warmup
    print("Warming up models...")
    _ = bm25_search("insurance policy", top_k=2)
    _ = vector_search("insurance policy", top_k=2)
    _ = hybrid_search("insurance policy", top_k=2)

    raw_records = []
    
    # Baseline keys: bm25, dense, hybrid, hybrid_verif
    baselines = ["bm25", "dense", "hybrid", "hybrid_verif"]
    
    results = {
        b: {
            "recalls": {1: [], 3: [], 5: [], 8: []},
            "precisions": {1: [], 3: [], 5: [], 8: []},
            "mrrs": [],
            "ndcgs": [],
            "latencies": [],
            "by_category": defaultdict(lambda: {"recalls": {1: [], 3: [], 5: [], 8: []}, "mrrs": [], "ndcgs": []})
        }
        for b in baselines
    }

    # Tracking safety and refusals
    refusal_metrics = {
        "answerable_count": 0,
        "unanswerable_count": 0,
        "security_count": 0,
        "false_refusals": {b: 0 for b in baselines},
        "correct_refusals": {b: 0 for b in baselines},
        "security_blocks": 0
    }

    K_VALS = [1, 3, 5, 8]

    for idx, q in enumerate(questions, 1):
        case_id = q["case_id"]
        category = q["category"]
        query_text = q["query"]
        target_file = q["candidate_source_file"]
        target_passage = q["candidate_passage"]
        is_answerable = (q["corpus_available_guess"] == "YES")

        if is_answerable:
            refusal_metrics["answerable_count"] += 1
        elif category == "prompt_injection_security":
            refusal_metrics["security_count"] += 1
            refusal_metrics["unanswerable_count"] += 1
        else:
            refusal_metrics["unanswerable_count"] += 1

        # Check guardrail on query
        is_safe, guardrail_reason = GuardrailService.check_input(query_text)
        if not is_safe:
            refusal_metrics["security_blocks"] += 1

        record = {
            "case_id": case_id,
            "category": category,
            "query": query_text,
            "is_answerable": is_answerable,
            "guardrail_safe": is_safe,
            "guardrail_reason": guardrail_reason,
            "runs": {}
        }

        # 1. BM25 Search
        t0 = time.perf_counter()
        bm25_res = bm25_search(query_text, top_k=8)
        lat_bm25 = (time.perf_counter() - t0) * 1000.0

        # 2. Dense Search
        t0 = time.perf_counter()
        dense_res = vector_search(query_text, top_k=8)
        lat_dense = (time.perf_counter() - t0) * 1000.0

        # 3. Hybrid Search
        t0 = time.perf_counter()
        hybrid_res = hybrid_search(query_text, top_k=8)
        lat_hybrid = (time.perf_counter() - t0) * 1000.0

        # 4. Hybrid + Verification
        t0 = time.perf_counter()
        hybrid_verif_res = apply_verification(hybrid_res, similarity_threshold=0.3)
        lat_verif = (time.perf_counter() - t0) * 1000.0 + lat_hybrid

        runs_map = {
            "bm25": (bm25_res, lat_bm25),
            "dense": (dense_res, lat_dense),
            "hybrid": (hybrid_res, lat_hybrid),
            "hybrid_verif": (hybrid_verif_res, lat_verif)
        }

        for b in baselines:
            chunks, lat = runs_map[b]
            results[b]["latencies"].append(lat)

            # Check relevance for each chunk
            rel_list = [1 if is_chunk_relevant(c, target_file, target_passage) else 0 for c in chunks]
            
            # Refusal / Low evidence logic
            has_evidence = len(chunks) > 0 and (max([c.get("score", 0.0) for c in chunks] or [0.0]) >= 0.25)
            if not is_safe:
                has_evidence = False

            if is_answerable:
                if not has_evidence:
                    refusal_metrics["false_refusals"][b] += 1
            else:
                if not has_evidence or not is_safe:
                    refusal_metrics["correct_refusals"][b] += 1

            record["runs"][b] = {
                "latency_ms": round(lat, 2),
                "num_retrieved": len(chunks),
                "retrieved_chunk_ids": [c.get("chunk_id") for c in chunks],
                "retrieved_sources": [c.get("source_document") for c in chunks],
                "retrieved_scores": [round(float(c.get("score", 0.0)), 4) for c in chunks],
                "relevance_vector": rel_list
            }

            # Only compute Recall/Precision/MRR/nDCG on answerable questions
            if is_answerable:
                # Reciprocal rank
                rr = 0.0
                for rank_idx, rel in enumerate(rel_list):
                    if rel == 1:
                        rr = 1.0 / (rank_idx + 1)
                        break
                results[b]["mrrs"].append(rr)
                results[b]["by_category"][category]["mrrs"].append(rr)

                # nDCG@8
                dcg8 = calculate_dcg(rel_list, 8)
                num_rel = sum(rel_list)
                idcg8 = calculate_idcg(max(1, num_rel), 8)
                ndcg8 = min(1.0, dcg8 / idcg8) if idcg8 > 0 else 0.0
                results[b]["ndcgs"].append(ndcg8)
                results[b]["by_category"][category]["ndcgs"].append(ndcg8)

                # Recall@K and Precision@K
                for k in K_VALS:
                    top_k_rels = rel_list[:k]
                    # Binary recall: did top-k contain at least 1 relevant passage?
                    rec_k = 1.0 if any(top_k_rels) else 0.0
                    prec_k = sum(top_k_rels) / float(k)

                    results[b]["recalls"][k].append(rec_k)
                    results[b]["precisions"][k].append(prec_k)
                    results[b]["by_category"][category]["recalls"][k].append(rec_k)

        raw_records.append(record)

    # Save JSONL
    with open(JSONL_PATH, "w", encoding="utf-8") as f:
        for r in raw_records:
            f.write(json.dumps(r) + "\n")
    print(f"Saved {len(raw_records)} run records to {JSONL_PATH}")

    # Compute Summary Statistics
    summary = {
        "execution_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total_queries": len(questions),
        "answerable_queries": refusal_metrics["answerable_count"],
        "unanswerable_queries": refusal_metrics["unanswerable_count"],
        "security_queries": refusal_metrics["security_count"],
        "baselines": {}
    }

    metric_table_rows = []

    for b in baselines:
        b_res = results[b]
        mrr_mean = float(np.mean(b_res["mrrs"]))
        mrr_ci = bootstrap_ci(b_res["mrrs"])

        ndcg_mean = float(np.mean(b_res["ndcgs"]))
        ndcg_ci = bootstrap_ci(b_res["ndcgs"])

        rec1 = float(np.mean(b_res["recalls"][1]))
        rec3 = float(np.mean(b_res["recalls"][3]))
        rec5 = float(np.mean(b_res["recalls"][5]))
        rec8 = float(np.mean(b_res["recalls"][8]))
        rec8_ci = bootstrap_ci(b_res["recalls"][8])

        prec1 = float(np.mean(b_res["precisions"][1]))
        prec3 = float(np.mean(b_res["precisions"][3]))
        prec5 = float(np.mean(b_res["precisions"][5]))
        prec8 = float(np.mean(b_res["precisions"][8]))

        lats = b_res["latencies"]
        lat_median = float(np.median(lats))
        lat_p95 = float(np.percentile(lats, 95))
        lat_mean = float(np.mean(lats))

        # Refusal metrics
        unans_denom = refusal_metrics["unanswerable_count"]
        ans_denom = refusal_metrics["answerable_count"]
        refusal_acc = float(refusal_metrics["correct_refusals"][b] / unans_denom) if unans_denom > 0 else 0.0
        false_refusal_rate = float(refusal_metrics["false_refusals"][b] / ans_denom) if ans_denom > 0 else 0.0

        summary["baselines"][b] = {
            "mrr": round(mrr_mean, 4),
            "mrr_95ci": mrr_ci,
            "ndcg_at_8": round(ndcg_mean, 4),
            "ndcg_95ci": ndcg_ci,
            "recall_at_1": round(rec1, 4),
            "recall_at_3": round(rec3, 4),
            "recall_at_5": round(rec5, 4),
            "recall_at_8": round(rec8, 4),
            "recall_at_8_95ci": rec8_ci,
            "precision_at_1": round(prec1, 4),
            "precision_at_3": round(prec3, 4),
            "precision_at_5": round(prec5, 4),
            "precision_at_8": round(prec8, 4),
            "refusal_accuracy": round(refusal_acc, 4),
            "false_refusal_rate": round(false_refusal_rate, 4),
            "latency_median_ms": round(lat_median, 2),
            "latency_p95_ms": round(lat_p95, 2),
            "latency_mean_ms": round(lat_mean, 2)
        }

        metric_table_rows.append({
            "Baseline": b.upper(),
            "Recall@1": round(rec1, 4),
            "Recall@3": round(rec3, 4),
            "Recall@5": round(rec5, 4),
            "Recall@8": round(rec8, 4),
            "Precision@8": round(prec8, 4),
            "MRR": round(mrr_mean, 4),
            "nDCG@8": round(ndcg_mean, 4),
            "Refusal_Acc": round(refusal_acc, 4),
            "False_Refusal_Rate": round(false_refusal_rate, 4),
            "Median_Latency_ms": round(lat_median, 2),
            "P95_Latency_ms": round(lat_p95, 2)
        })

    # Add Per-Category breakdown to summary
    summary["category_breakdown"] = {}
    for cat in sorted(set(q["category"] for q in questions)):
        summary["category_breakdown"][cat] = {}
        for b in baselines:
            cat_data = results[b]["by_category"][cat]
            if cat_data["mrrs"]:
                summary["category_breakdown"][cat][b] = {
                    "mrr": round(float(np.mean(cat_data["mrrs"])), 4),
                    "ndcg8": round(float(np.mean(cat_data["ndcg8"] if "ndcg8" in cat_data else cat_data["ndcgs"])), 4),
                    "recall8": round(float(np.mean(cat_data["recalls"][8])), 4)
                }

    # Security block stats
    summary["security_probe_summary"] = {
        "total_security_probes": refusal_metrics["security_count"],
        "input_guardrail_blocks": refusal_metrics["security_blocks"],
        "block_rate": round(refusal_metrics["security_blocks"] / max(refusal_metrics["security_count"], 1), 4)
    }

    # Write metric tables CSV
    with open(METRIC_TABLE_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "Baseline", "Recall@1", "Recall@3", "Recall@5", "Recall@8",
            "Precision@8", "MRR", "nDCG@8", "Refusal_Acc",
            "False_Refusal_Rate", "Median_Latency_ms", "P95_Latency_ms"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metric_table_rows:
            writer.writerow(row)
    print(f"Saved metric comparison table to {METRIC_TABLE_PATH}")

    # Write summary JSON
    with open(SUMMARY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary JSON to {SUMMARY_JSON_PATH}")

    print("\n=== BENCHMARK RESULTS SUMMARY ===")
    for r in metric_table_rows:
        print(r)

if __name__ == "__main__":
    run_benchmarks()
