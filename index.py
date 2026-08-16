"""
index.py — Clause-Aware Chunking & Hybrid Index Builder.

1.  Loads extracted JSON files from the ingestion phase.
2.  Chunks text with LlamaIndex SentenceSplitter (preserving clause boundaries).
3.  Builds a ChromaDB vector index (Sentence-BERT embeddings).
4.  Builds a BM25 keyword index (rank_bm25).
"""

import json
import os
import pickle
import re
import uuid

import nltk
from nltk.corpus import stopwords

from config import (
    BM25_INDEX_PATH,
    CHROMA_COLLECTION_NAME,
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    JSON_DIR,
    ensure_directories,
    setup_logging,
)

logger = setup_logging()

# Download NLTK stopwords if not already present
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

STOP_WORDS = set(stopwords.words("english"))


# ═══════════════════════════════════════════════════════════════════════════
#  Loading Extracted JSON
# ═══════════════════════════════════════════════════════════════════════════

def load_extracted_jsons() -> list[dict]:
    """
    Load all JSON files produced by ingest.py.

    Returns:
        Flat list of element dicts with mandatory metadata.
    """
    elements: list[dict] = []
    if not os.path.isdir(JSON_DIR):
        logger.warning("JSON directory not found: %s", JSON_DIR)
        return elements

    json_files = [f for f in os.listdir(JSON_DIR) if f.endswith(".json")]
    if not json_files:
        logger.warning("No JSON files found in %s", JSON_DIR)
        return elements

    for jf in json_files:
        path = os.path.join(JSON_DIR, jf)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            elems = data.get("elements", [])
            elements.extend(elems)
            logger.info("Loaded %d elements from %s", len(elems), jf)
        except Exception as exc:
            logger.error("Failed to load %s: %s", jf, exc)

    logger.info("Total elements loaded: %d", len(elements))
    return elements


# ═══════════════════════════════════════════════════════════════════════════
#  Clause-Aware Chunking
# ═══════════════════════════════════════════════════════════════════════════

def chunk_elements(elements: list[dict]) -> list[dict]:
    """
    Split extracted elements into overlapping chunks using SentenceSplitter.

    Each chunk inherits metadata from its source element and receives a
    unique chunk_id.

    Returns:
        List of chunk dicts with keys:
          chunk_id, text, source_document, page_number, section_title
    """
    from collections import defaultdict
    from llama_index.core.node_parser import SentenceSplitter

    splitter = SentenceSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        paragraph_separator="\n\n",
        secondary_chunking_regex="[^,.;。?!]+[,.;。?!]?",
    )

    chunks: list[dict] = []
    
    # Group elements securely by document and page to securely reconstruct paragraphs
    docs_pages = defaultdict(list)
    for elem in elements:
        doc = elem.get("source_document", "unknown")
        page = elem.get("page_number", 0)
        docs_pages[(doc, page)].append(elem)

    for (doc, page), elems in docs_pages.items():
        # Reconstruct the page text cleanly
        page_text = "\n".join([e.get("text", "").strip() for e in elems if e.get("text", "").strip()])
        if not page_text:
            continue

        splits = splitter.split_text(page_text)

        for split_text in splits:
            if not split_text.strip():
                continue

            chunk = {
                "chunk_id": str(uuid.uuid4()),
                "text": split_text.strip(),
                "source_document": doc,
                "page_number": page,
                "section_title": elems[0].get("section_title", "Unknown") if elems else "Unknown",
                "element_type": "text",
            }
            chunks.append(chunk)

    logger.info("Created %d chunks from %d elements.", len(chunks), len(elements))
    return chunks


# ═══════════════════════════════════════════════════════════════════════════
#  Vector Index — ChromaDB
# ═══════════════════════════════════════════════════════════════════════════

def build_vector_index(chunks: list[dict]) -> None:
    """
    Embed chunks with Sentence-BERT and store in ChromaDB (persistent).
    """
    import chromadb
    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection to rebuild cleanly
    try:
        client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Batch insert for efficiency
    BATCH_SIZE = 100
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [
            {
                "source_document": c["source_document"],
                "page_number": str(c["page_number"]) if c["page_number"] else "N/A",
                "section_title": c["section_title"],
                "element_type": c["element_type"],
            }
            for c in batch
        ]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(
            "Indexed batch %d–%d into ChromaDB.", i + 1, min(i + BATCH_SIZE, len(chunks))
        )

    logger.info(
        "ChromaDB vector index built: %d chunks in collection '%s'.",
        collection.count(), CHROMA_COLLECTION_NAME,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Keyword Index — BM25
# ═══════════════════════════════════════════════════════════════════════════

def _tokenize(text: str) -> list[str]:
    """Lowercase, remove stopwords, tokenize."""
    tokens = re.findall(r"\b[a-z0-9]+\b", text.lower())
    return [t for t in tokens if t not in STOP_WORDS]


def build_bm25_index(chunks: list[dict]) -> None:
    """
    Build a BM25 keyword index from chunk texts and persist to disk.
    Stores (bm25_instance, chunk_list) so retrieval can map scores → chunks.
    """
    from rank_bm25 import BM25Okapi

    tokenized = [_tokenize(c["text"]) for c in chunks]
    bm25 = BM25Okapi(tokenized)

    os.makedirs(os.path.dirname(BM25_INDEX_PATH), exist_ok=True)
    with open(BM25_INDEX_PATH, "wb") as fh:
        pickle.dump({"bm25": bm25, "chunks": chunks}, fh)

    logger.info("BM25 index built and saved → %s (%d chunks).", BM25_INDEX_PATH, len(chunks))


# ═══════════════════════════════════════════════════════════════════════════
#  Main Build Pipeline
# ═══════════════════════════════════════════════════════════════════════════

def build_index() -> None:
    """
    Full indexing pipeline:
      1. Load extracted JSONs
      2. Chunk elements
      3. Build ChromaDB vector index
      4. Build BM25 keyword index
    """
    ensure_directories()

    elements = load_extracted_jsons()
    if not elements:
        logger.error("No elements to index. Run ingest.py first.")
        return

    chunks = chunk_elements(elements)
    if not chunks:
        logger.error("Chunking produced no results.")
        return

    build_vector_index(chunks)
    build_bm25_index(chunks)

    logger.info("═══ Index build complete. ═══")


if __name__ == "__main__":
    build_index()
