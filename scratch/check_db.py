import os
import sys
from pprint import pprint

# Set up paths for absolute imports
sys.path.insert(0, "/app")

import chromadb
import pickle

CHROMA_DIR = "/app/data/chroma_db"
CHROMA_COLLECTION_NAME = "insurance_docs"
BM25_INDEX_PATH = "/app/data/bm25_index.pkl"

def verify_chroma():
    print("=== CHROMADB VERIFICATION ===")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
    results = collection.get(where={"source_document": "LIC_Jeevan_Shagun_Policy_inside_r.pdf"})
    count = len(results['ids'])
    print(f"Total chunks in ChromaDB for new document: {count}")
    if count > 0:
        print("Sample metadata:")
        pprint(results['metadatas'][0])
    return count > 0

def verify_bm25():
    print("\n=== BM25 VERIFICATION ===")
    try:
        with open(BM25_INDEX_PATH, "rb") as fh:
            data = pickle.load(fh)
            bm25 = data["bm25"]
            chunks = data["chunks"]
        print(f"Total chunks in BM25 index: {len(chunks)}")
        
        # Searching for a keyword from LIC Jeevan Shagun 
        query = "death benefit maturity"
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        
        top_indices = scores.argsort()[::-1][:10]
        found = False
        for idx in top_indices:
            meta = chunks[idx]
            score = scores[idx]
            doc_name = meta.get('source_document', 'Unknown')
            if score > 0:
                print(f"Score: {score:.4f}, Doc: {doc_name}")
                if doc_name == "LIC_Jeevan_Shagun_Policy_inside_r.pdf":
                    found = True
        
        if found:
            print("BM25 SUCCESS: Newly uploaded document appears in BM25 results.")
        else:
            print("BM25 FAILURE: Newly uploaded document NOT FOUND in top 10 BM25 results.")
            # Let's count how many chunks exist for it in BM25 just in case
            c = sum(1 for ch in chunks if ch.get("source_document") == "LIC_Jeevan_Shagun_Policy_inside_r.pdf")
            print(f"Total chunks for new doc in BM25 overall: {c}")
            
    except Exception as e:
        print(f"BM25 Error: {e}")

if __name__ == "__main__":
    verify_chroma()
    verify_bm25()
