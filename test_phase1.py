from app import hybrid_search
import json

query = "What are the maturity benefits and conditions under the LIC Bima Jyoti policy?"
chunks = hybrid_search(query, top_k=5)

for i, c in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print("Score:", c['score'])
    print("Norm Score:", c.get('norm_score', 'N/A'))
    print("Combined:", c.get('combined_score', 'N/A'))
    print("Doc:", c.get('source_document', ''))
    print("Text:", c['text'][:300])

