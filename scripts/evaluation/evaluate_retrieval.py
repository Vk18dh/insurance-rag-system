import json
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import app

DATASET_PATH = "scripts/evaluation/data/retrieval_dataset.json"

def load_dataset(path=DATASET_PATH):
    if not os.path.exists(path):
        print(f"Dataset not found at {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_match(retrieved_chunk, expected_source, expected_page):
    c_source = retrieved_chunk.get("source_document", "")
    c_page = str(retrieved_chunk.get("page_number", ""))
    
    # We consider it a match if it comes from the exact document and page
    if expected_source == c_source and str(expected_page) == c_page:
        return True
    return False

def evaluate(label="CURRENT BASELINE"):
    dataset = load_dataset()
    if not dataset:
        return
        
    print(f"=== {label} ===")
    print(f"Evaluating {len(dataset)} queries...\n")
    
    total_latency = 0
    mrr_sum = 0
    hits_at_5 = 0
    hits_at_10 = 0
    total_precision_5 = 0
    
    for i, item in enumerate(dataset):
        q = item["question"]
        expected_src = item["expected_source"]
        expected_page = item["expected_page"]
        
        start = time.monotonic()
        results = app.hybrid_search(q, top_k=10)
        total_latency += (time.monotonic() - start)
        
        # Rank calculations
        hit_rank = -1
        matches_in_top_5 = 0
        
        for rank, chunk in enumerate(results):
            match = is_match(chunk, expected_src, expected_page)
            if match:
                if hit_rank == -1:
                    hit_rank = rank + 1
                if rank < 5:
                    matches_in_top_5 += 1
                    
        # Metrics
        if hit_rank != -1:
            mrr_sum += (1.0 / hit_rank)
            if hit_rank <= 10:
                hits_at_10 += 1
            if hit_rank <= 5:
                hits_at_5 += 1
                
        total_precision_5 += (matches_in_top_5 / 5.0)
        
        # Progress
        if (i + 1) % 10 == 0:
            print(f"Processed {i+1}/{len(dataset)} queries...")

    n = len(dataset)
    mrr = mrr_sum / n
    recall_5 = hits_at_5 / n
    recall_10 = hits_at_10 / n
    precision_5 = total_precision_5 / n
    avg_latency = (total_latency / n) * 1000
    
    print("\n--- RESULTS ---")
    print(f"Queries Evaluated: {n}")
    print(f"Average Latency:   {avg_latency:.2f} ms/query")
    print(f"MRR:               {mrr:.4f}")
    print(f"Recall@5:          {recall_5:.4f}")
    print(f"Recall@10:         {recall_10:.4f}")
    print(f"Precision@5:       {precision_5:.4f}")
    print("-----------------\n")

if __name__ == "__main__":
    evaluate()
