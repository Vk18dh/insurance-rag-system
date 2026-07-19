import sys
# Need to use Phase 1 retriever to see if it even finds the chunk locally now.
sys.path.append(".")
from app import vector_search, bm25_search
import json

query = "What are the maturity benefits and conditions under the LIC Bima Jyoti policy?"

print("--- BM25 SEARCH ---")
bm25_results = bm25_search(query, top_k=5)
for r in bm25_results:
    print(f"[{r.get('score', 0):.2f}] {r.get('text', '')[:100].replace(chr(10), ' ')}")

print("\n--- VECTOR SEARCH ---")
v_results = vector_search(query, top_k=5)
for r in v_results:
    print(f"[{r.get('score', 0):.2f}] {r.get('text', '')[:100].replace(chr(10), ' ')}")
