import os
import sys
import time
import subprocess
import json
import shutil
import tracemalloc

# Models to benchmark
MODELS = {
    "minilm": "all-MiniLM-L6-v2",
    "bge_small": "BAAI/bge-small-en-v1.5",
    "nomic": "nomic-ai/nomic-embed-text-v1.5"
}

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DATASET_PATH = os.path.join(BASE_DIR, "scripts", "evaluation", "data", "retrieval_dataset.json")

results = {}

def get_dir_size(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

print("Starting Phase 1B Embedding Benchmarks...\n")

for key, model_name in MODELS.items():
    print(f"=========================================")
    print(f"Benchmarking Model: {model_name}")
    print(f"=========================================")
    
    chroma_dir = os.path.join(BASE_DIR, "data", "benchmark", key)
    
    # Cleanup previous benchmark index if exists
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)
        
    env = os.environ.copy()
    env["OVERRIDE_EMBEDDING_MODEL"] = model_name
    env["OVERRIDE_CHROMA_DIR"] = chroma_dir
    
    # 1. Measure Indexing Time
    print("1. Indexing documents...")
    start_time = time.monotonic()
    
    # We run index.py as a subprocess to keep memory state clean
    idx_proc = subprocess.run([sys.executable, "index.py"], cwd=BASE_DIR, env=env, capture_output=True, text=True)
    index_time = time.monotonic() - start_time
    
    if idx_proc.returncode != 0:
        print(f"Indexing failed for {model_name}. Error:\n{idx_proc.stderr}")
        results[model_name] = {"error": "Indexing failed"}
        continue
        
    # Measure index size
    index_size_mb = get_dir_size(chroma_dir) / (1024 * 1024)
    print(f"Index built in {index_time:.2f}s, Size: {index_size_mb:.2f} MB")
    
    # 2. Measure Retrieval Metrics via evaluate_retrieval.py
    print("2. Running retrieval evaluation...")
    eval_proc = subprocess.run([sys.executable, "scripts/evaluation/evaluate_retrieval.py"], cwd=BASE_DIR, env=env, capture_output=True, text=True)
    
    if eval_proc.returncode != 0:
        print(f"Evaluation failed for {model_name}. Error:\n{eval_proc.stderr}")
        results[model_name] = {"error": "Evaluation failed"}
        continue
        
    # Parse evaluation output
    # Expected output format in evaluate_retrieval.py:
    # Average Latency:   476.18 ms/query
    # MRR:               0.4675
    # Recall@5:          0.6000
    # Recall@10:         0.7200
    # Precision@5:       0.1560
    
    out = eval_proc.stdout
    metrics = {
        "index_time_s": round(index_time, 2),
        "index_size_mb": round(index_size_mb, 2)
    }
    
    for line in out.splitlines():
        if "Average Latency" in line:
            metrics["avg_latency_ms"] = float(line.split(":")[1].strip().split()[0])
        elif "MRR" in line:
            metrics["mrr"] = float(line.split(":")[1].strip())
        elif "Recall@5" in line:
            metrics["recall_5"] = float(line.split(":")[1].strip())
        elif "Recall@10" in line:
            metrics["recall_10"] = float(line.split(":")[1].strip())
        elif "Precision@5" in line:
            metrics["precision_5"] = float(line.split(":")[1].strip())
            
    print("Results:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
        
    results[model_name] = metrics
    print("\n")

# Save summary
with open(os.path.join(BASE_DIR, "scripts", "evaluation", "benchmark_1b_results.json"), "w") as f:
    json.dump(results, f, indent=2)

print("Benchmark complete. Summary saved to benchmark_1b_results.json")
