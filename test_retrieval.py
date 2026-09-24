from phase2.services.retrieval_service import RetrievalService
from phase2.config.settings import Phase2Settings
import json

settings = Phase2Settings()
service = RetrievalService(settings)
chunks = service.search_bm25("policy clause of lic", 2)
for i, c in enumerate(chunks):
    print(f"--- Chunk {i+1} ---")
    print(c.text)
