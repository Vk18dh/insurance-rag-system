# AI-Driven Insurance Knowledge Assessment System

RAG-based system for processing LIC Policy PDFs and IRDAI Annual Reports. Extracts text via OCR, chunks with clause awareness, indexes in both vector (ChromaDB) and keyword (BM25) stores, and answers queries with grounded, citation-backed responses.

## Architecture

```
PDF Files → [ingest.py] → JSON → [index.py] → ChromaDB + BM25 → [app.py] → Grounded Answer
```

| Module       | Purpose                                              |
|--------------|------------------------------------------------------|
| `config.py`  | Central configuration (paths, models, parameters)    |
| `ingest.py`  | Hi-res OCR extraction + post-processing → JSON       |
| `index.py`   | Clause-aware chunking + dual index build             |
| `app.py`     | Hybrid retrieval (50/50) + LLM QA + interactive CLI  |

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
copy .env.example .env
# Edit .env and add your Gemini API key
```

## Usage

### Step 1 — Place PDFs
Put your LIC policy PDFs and IRDAI reports into `data/pdfs/`.

### Step 2 — Ingest (OCR + JSON)
```bash
python ingest.py
```
Processed JSONs are saved to `data/extracted/` (won't re-process existing files).

### Step 3 — Build Indices
```bash
python index.py
```
Creates ChromaDB vector store in `data/chroma_db/` and BM25 index at `data/bm25_index.pkl`.

### Step 4 — Query
```bash
python app.py
```

Or run the full pipeline in one go:
```bash
python app.py --ingest --index
```

### Example
```
📋 Question: What is the death benefit under Jeevan Anand policy?

🔍 Searching...

──────────────────────────────────────────────────────────────
📝 ANSWER:

The death benefit under the Jeevan Anand policy includes...
(Source: LIC_Jeevan_Anand.pdf, Page: 5)

📚 SOURCES:
   • LIC_Jeevan_Anand.pdf — Page 5 (Benefits)
   • LIC_Jeevan_Anand.pdf — Page 6 (Death Benefit)
──────────────────────────────────────────────────────────────
```

## Project Structure

```
majorcode/
├── config.py            # Configuration constants
├── ingest.py            # Document ingestion & OCR
├── index.py             # Chunking & index building
├── app.py               # Retrieval & QA interface
├── requirements.txt     # Python dependencies
├── .env.example         # API key template
├── .env                 # Your API key (not committed)
└── data/
    ├── pdfs/            # Input PDF documents
    ├── extracted/       # Processed JSON files
    ├── chroma_db/       # ChromaDB vector store
    └── bm25_index.pkl   # BM25 keyword index
```

## Key Features

- **Hi-res OCR** via `unstructured` — handles scanned PDFs, tables, multi-column layouts
- **Clause-aware chunking** — preserves insurance clause boundaries (exclusions, benefits)
- **Hybrid retrieval** — BM25 (keyword) + ChromaDB (semantic) with 50/50 weighting
- **Grounded QA** — Insurance Auditor prompt ensures answers cite source document and page number
- **Incremental processing** — already-processed PDFs are skipped automatically
