import chromadb
import json

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection("insurance_docs")
docs = collection.get()

results = []
for i, text in enumerate(docs["documents"]):
    meta = docs["metadatas"][i]
    if "Bima Jyoti" in meta.get("source_document", "") or "Bima Jyoti" in text:
        if "Maturity" in text or "maturity" in text or "payable" in text:
            results.append(f"--- CHUNK {docs['ids'][i]} ---\n{text}\n")

with open("data/bima_jyoti_chunks.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
print(f"Dumped {len(results)} chunks to data/bima_jyoti_chunks.txt")
