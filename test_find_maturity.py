import chromadb

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_collection("insurance_docs")

docs = collection.get()

found = 0
for text in docs["documents"]:
    if "following benefits are payable" in text or "Sum Assured on Maturity" in text:
        print("FOUND EXACT MATCHING PARAGRAPH:")
        print(text[:1000])
        print("------")
        found += 1
print(f"Total found matching chunks: {found}")
