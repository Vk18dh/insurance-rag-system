from app import hybrid_search
import json

query = "What are the maturity benefits and conditions under the LIC Bima Jyoti policy?"
chunks = hybrid_search(query, top_k=5)

out = []
for c in chunks:
    out.append({
        'score': c['score'],
        'doc': c.get('source_document', ''),
        'text': c['text']
    })

with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
