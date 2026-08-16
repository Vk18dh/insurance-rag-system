import os
import sys
import json
import pickle
import random
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load chunks
bm25_path = "data/bm25_index.pkl"
with open(bm25_path, "rb") as f:
    data = pickle.load(f)
chunks = data["chunks"]

# Filter chunks to ensure they have substantive text
valid_chunks = [c for c in chunks if len(c['text']) > 200]

random.seed(42)
sampled_chunks = random.sample(valid_chunks, min(60, len(valid_chunks)))

dataset = []
print(f"Generating deterministic dataset from {len(sampled_chunks)} chunks...")

def extract_key_phrase(text):
    # Very simple heuristic: take the first 4-8 words of the first long sentence
    sentences = re.split(r'[.!?]', text)
    for s in sentences:
        words = s.strip().split()
        if len(words) > 5:
            # return a subset of words
            return " ".join(words[:min(7, len(words))])
    return text[:30]

count = 0
for i, chunk in enumerate(sampled_chunks):
    if count >= 50:
        break
        
    phrase = extract_key_phrase(chunk['text'])
    question = f"What does the policy state about '{phrase}'?"
    
    item = {
        "query_id": f"q_{count}",
        "question": question,
        "expected_source": chunk["source_document"],
        "expected_page": chunk["page_number"],
        "expected_text_snippet": chunk["text"][:200] + "..."
    }
    dataset.append(item)
    count += 1

# Save dataset
os.makedirs("scripts/evaluation/data", exist_ok=True)
with open("scripts/evaluation/data/retrieval_dataset.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"Saved {len(dataset)} evaluation items to scripts/evaluation/data/retrieval_dataset.json")
