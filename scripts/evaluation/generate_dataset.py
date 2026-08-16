import os
import sys
import json
import pickle
import random
import requests
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

load_dotenv()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("Error: OPENROUTER_API_KEY not found in .env")
    sys.exit(1)

# Load chunks
bm25_path = "data/bm25_index.pkl"
with open(bm25_path, "rb") as f:
    data = pickle.load(f)
chunks = data["chunks"]

# Filter chunks to ensure they have substantive text (e.g., > 200 chars)
valid_chunks = [c for c in chunks if len(c['text']) > 200]

# Sample chunks across different policies
random.seed(42)
sampled_chunks = random.sample(valid_chunks, min(60, len(valid_chunks)))

dataset = []
print(f"Generating dataset from {len(sampled_chunks)} chunks using OpenRouter...")

count = 0
for i, chunk in enumerate(sampled_chunks):
    if count >= 50:
        break
        
    prompt = f"""
    You are an expert insurance analyst. Read the following text from an insurance policy document.
    Generate a SINGLE, natural, specific question that a user would ask, which can be answered ENTIRELY and DIRECTLY by this text.
    Make the question sound like a real user asking about their policy (e.g., "What is the grace period?", "Are suicides covered?").
    Do NOT include the answer, just the question. Output ONLY the question.
    
    TEXT:
    {chunk['text']}
    """
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )
        
        result = response.json()
        question = result["choices"][0]["message"]["content"].strip().replace('"', '')
        
        # Ground truth is the exact source document and page number, plus the chunk text itself
        item = {
            "query_id": f"q_{count}",
            "question": question,
            "expected_source": chunk["source_document"],
            "expected_page": chunk["page_number"],
            "expected_text_snippet": chunk["text"][:200] + "..."
        }
        dataset.append(item)
        print(f"[{count+1}/50] Generated: {question}")
        count += 1
    except Exception as e:
        print(f"Error generating for chunk {i}: {e}")

# Save dataset
os.makedirs("scripts/evaluation/data", exist_ok=True)
with open("scripts/evaluation/data/retrieval_dataset.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2)

print(f"Saved {len(dataset)} evaluation items to scripts/evaluation/data/retrieval_dataset.json")
