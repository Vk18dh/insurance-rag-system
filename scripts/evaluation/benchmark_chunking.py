import os
import sys
import time
import subprocess
import json
import shutil
import pickle

CONFIGS = {
    "Config_A_4096": {"size": 4096, "overlap": 512},
    "Config_B_1024": {"size": 1024, "overlap": 128},
    "Config_C_512": {"size": 512, "overlap": 64}
}

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
MODEL_NAME = "BAAI/bge-small-en-v1.5"
DATASET_PATH = os.path.join(BASE_DIR, "scripts", "evaluation", "data", "retrieval_dataset.json")

results = {}

def get_dir_size(path):
    total = 0
    if not os.path.exists(path): return 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

print("Starting Phase 1C Chunking Benchmarks...\n")

for config_name, params in CONFIGS.items():
    print(f"=========================================")
    print(f"Benchmarking {config_name}")
    print(f"=========================================")
    
    size = params["size"]
    overlap = params["overlap"]
    
    chroma_dir = os.path.join(BASE_DIR, "data", "benchmark", f"bge_chunk_{size}")
    bm25_path = os.path.join(BASE_DIR, "data", "benchmark", f"bge_chunk_{size}", "bm25_index.pkl")
    
    # Cleanup previous benchmark index if exists
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)
    os.makedirs(chroma_dir, exist_ok=True)
        
    env = os.environ.copy()
    env["OVERRIDE_EMBEDDING_MODEL"] = MODEL_NAME
    env["OVERRIDE_CHROMA_DIR"] = chroma_dir
    env["OVERRIDE_BM25_INDEX_PATH"] = bm25_path
    env["OVERRIDE_CHUNK_SIZE"] = str(size)
    env["OVERRIDE_CHUNK_OVERLAP"] = str(overlap)
    
    # 1. Measure Indexing Time
    print(f"1. Indexing documents with CHUNK_SIZE={size}...")
    start_time = time.monotonic()
    
    idx_proc = subprocess.run([sys.executable, "index.py"], cwd=BASE_DIR, env=env, capture_output=True, text=True)
    index_time = time.monotonic() - start_time
    
    if idx_proc.returncode != 0:
        print(f"Indexing failed for {config_name}. Error:\n{idx_proc.stderr}")
        results[config_name] = {"error": "Indexing failed"}
        continue
        
    # Measure index size and chunk counts
    index_size_mb = get_dir_size(chroma_dir) / (1024 * 1024)
    
    num_chunks = 0
    if os.path.exists(bm25_path):
        with open(bm25_path, "rb") as fh:
            bm25_data = pickle.load(fh)
            num_chunks = len(bm25_data["chunks"])
            
    print(f"Index built in {index_time:.2f}s, Size: {index_size_mb:.2f} MB, Chunks: {num_chunks}")
    
    # 2. Measure Retrieval Metrics via evaluate_retrieval.py
    print("2. Running retrieval evaluation...")
    eval_proc = subprocess.run([sys.executable, "scripts/evaluation/evaluate_retrieval.py"], cwd=BASE_DIR, env=env, capture_output=True, text=True)
    
    if eval_proc.returncode != 0:
        print(f"Evaluation failed for {config_name}. Error:\n{eval_proc.stderr}")
        results[config_name] = {"error": "Evaluation failed"}
        continue
        
    # Parse evaluation output
    out = eval_proc.stdout
    metrics = {
        "index_time_s": round(index_time, 2),
        "index_size_mb": round(index_size_mb, 2),
        "num_chunks": num_chunks
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
        
    results[config_name] = metrics
    print("\n")

# Save summary
with open(os.path.join(BASE_DIR, "scripts", "evaluation", "benchmark_1c_results.json"), "w") as f:
    json.dump(results, f, indent=2)

print("Benchmark complete. Summary saved to benchmark_1c_results.json")
