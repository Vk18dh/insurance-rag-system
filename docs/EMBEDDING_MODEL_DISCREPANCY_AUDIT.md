# Embedding Model Discrepancy Audit

This focused audit investigates the discrepancy between the current embedding model (`all-MiniLM-L6-v2`) and the model specified in recent prompts and evaluation scripts (`BGE-small`). 

As requested, this audit has been performed **without** modifying production code, rebuilding ChromaDB/BM25, or changing the Phase 1 baseline.

---

## 1. Current Model Configuration
The current embedding model is explicitly defined in `config.py` (Line 22):
```python
EMBEDDING_MODEL = os.environ.get("OVERRIDE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
```
Because neither `.env` nor `docker-compose.yml` provides an `OVERRIDE_EMBEDDING_MODEL` value, the system actively uses **`all-MiniLM-L6-v2`** at runtime.

## 2. Authoritative Document Specification
A comprehensive search across the six authoritative documents (`01_PRD.md`, `02_TRD.md`, `03_APP_FLOW.md`, `04_UI_UX_DESIGN_BRIEF.md`, `05_BACKEND_SCHEMA.md`, `06_IMPLEMENTATION_PLAN_FINAL.md`) reveals that **`BGE-small` is NEVER mentioned**. 

The `02_TRD.md` (Line 110) simply states:
> "Use the embedding implementation already established by the repository, such as Sentence-BERT where applicable."

Therefore, the active model (`all-MiniLM-L6-v2`) fully satisfies the written authoritative requirements.

## 3. Evidence from the Repository
While `BGE-small` is absent from the core project requirements, it **is** referenced heavily in the repository's evaluation and benchmarking scripts:
- `scripts/evaluation/benchmark_chunking.py` (Line 16): `MODEL_NAME = "BAAI/bge-small-en-v1.5"`
- `scripts/evaluation/evaluate_pipeline.py` (Line 119): `HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")`
- `scripts/evaluation/benchmark_embeddings.py` (Line 12): explicitly compares `"minilm": "all-MiniLM-L6-v2"` against `"bge_small": "BAAI/bge-small-en-v1.5"`.

This indicates that BGE-small was evaluated (and likely preferred in tests), but the production default in `config.py` was never updated to reflect it.

## 4. ChromaDB Compatibility Impact
**Incompatible.** 
Although both models output 384-dimensional vectors, they map semantic meaning to completely different vector spaces. 
If the system changes to `BGE-small` without clearing ChromaDB, a user query embedded by `BGE-small` will be compared against policy chunks embedded by `all-MiniLM-L6-v2`, resulting in nonsensical cosine distances and total retrieval failure.

## 5. BM25 Impact
**None.** 
BM25 is a sparse, keyword-based statistical index (`rank_bm25`). It relies on text tokenization (words/frequencies) and is entirely independent of the dense neural embedding model. Changing to BGE-small has absolutely zero effect on BM25.

## 6. Test Impact
- **Evaluation Scripts**: Would align with `bge-small-en-v1.5` which they already hardcode.
- **Runtime Tests**: A file like `rag_test_output.json` shows successful end-to-end execution (confidence `0.95`). If the model is changed, these runtime tests will fail until ChromaDB is completely rebuilt.

## 7. Migration / Re-Index Impact
Changing the embedding model requires a **complete, destructive re-index** of ChromaDB.
Every PDF in `data/pdfs/` would need to be re-run through `index.py` so that all historical chunks are embedded with `BGE-small` and inserted into a freshly wiped ChromaDB collection.

## 8. Freeze / Change-Control Rules
Changing the embedding model **violates the Phase 1 freeze rule**.
`06_IMPLEMENTATION_PLAN_FINAL.md` explicitly dictates:
> "Do not move Phase 1/Phase 2 without a verified critical reason."
> "Treat working code as the baseline. Do not rebuild completed functionality."

Because `all-MiniLM-L6-v2` is currently working and satisfies all authoritative documents, changing it constitutes a major architectural shift that contradicts the freeze mandate.

---

## 9. Recommendation

**DEFER the model change.**

1. **Proceed** with the Policy Document Management Implementation using the currently active `all-MiniLM-L6-v2` model. This honors the Phase 1 freeze and avoids a destructive database wipe.
2. The dynamic ingestion API being built will use `config.EMBEDDING_MODEL` natively.
3. If `BGE-small` is officially approved later, it can be seamlessly activated by changing the `.env` variable (`OVERRIDE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`) and running a one-time batch re-index using the existing CLI tool (`index.py`).

No action regarding `BGE-small` should be taken during this feature implementation.
