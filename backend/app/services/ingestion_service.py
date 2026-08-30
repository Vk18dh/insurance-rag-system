import os
import pickle
import logging
from datetime import datetime, timezone
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from config import (
    CHROMA_DIR,
    CHROMA_COLLECTION_NAME,
    BM25_INDEX_PATH,
    EMBEDDING_MODEL
)
from ingest import process_pdf, post_process_elements
from index import chunk_elements, _tokenize
from backend.app.models.document import Document, DocumentStatus
from backend.app.db.database import SessionLocal

logger = logging.getLogger(__name__)

# File-based lock for BM25 updates
import threading
bm25_lock = threading.Lock()

def process_document_background(document_id: str, file_path: str):
    """
    Background task to process a single uploaded PDF.
    Extracts text, chunks, embeds, and updates ChromaDB and BM25.
    """
    logger.info(f"Starting background processing for document: {document_id}")
    
    # Use a new session for background processing
    with SessionLocal() as db_session:
        document = db_session.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found in DB.")
            return

        try:
            # 1. Update Status to PROCESSING
            document.status = DocumentStatus.PROCESSING
            db_session.commit()

            # 2. Extract Elements (ingest.py logic)
            elements = process_pdf(file_path)
            structured_elements = post_process_elements(elements, document.document_name)
            
            if not structured_elements:
                raise ValueError("No usable text content could be extracted from the PDF.")

            # 3. Chunk Elements (index.py logic)
            # Note: chunk_elements expects 'source_document' which we populated in post_process_elements
            # We need to make sure chunk_elements sets the correct source_document.
            # Actually post_process_elements sets "source_document": filename.
            chunks = chunk_elements(structured_elements)

            if not chunks:
                raise ValueError("Chunking produced zero chunks.")

            # 4. Append to ChromaDB (dense retrieval)
            logger.info(f"Appending {len(chunks)} chunks to ChromaDB for document {document_id}")
            _append_to_chromadb(chunks, document_id)

            # 5. Append/Rebuild BM25 (sparse retrieval)
            logger.info(f"Appending {len(chunks)} chunks to BM25 for document {document_id}")
            _append_to_bm25(chunks)

            # 6. Update Status to COMPLETED
            document.status = DocumentStatus.COMPLETED
            document.ingestion_timestamp = datetime.now(timezone.utc)
            db_session.commit()
            logger.info(f"Successfully processed document {document_id}")

        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}", exc_info=True)
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            db_session.commit()


def _append_to_chromadb(chunks: list[dict], document_id: str):
    """
    Appends chunks to the existing ChromaDB collection.
    """
    model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    BATCH_SIZE = 100
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        
        metadatas = []
        for c in batch:
            # Must ensure correct metadata mapping as expected by Phase 2 RetrievalAgent
            metadata = {
                "source_document": c.get("source_document", "Unknown"),
                "page_number": str(c.get("page_number", "N/A")),
                "section_title": c.get("section_title", "Unknown"),
                "element_type": c.get("element_type", "text"),
                "document_id": document_id
            }
            metadatas.append(metadata)

        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

def _append_to_bm25(new_chunks: list[dict]):
    """
    Rebuilds the BM25 index safely by appending new chunks to the existing ones.
    Uses a threading lock to prevent corruption if concurrent uploads happen.
    """
    with bm25_lock:
        existing_chunks = []
        
        # Load existing chunks if the BM25 pickle exists
        if os.path.exists(BM25_INDEX_PATH):
            try:
                with open(BM25_INDEX_PATH, "rb") as fh:
                    data = pickle.load(fh)
                    existing_chunks = data.get("chunks", [])
            except Exception as e:
                logger.error(f"Failed to read existing BM25 index. Will rebuild from scratch. {e}")

        # Combine chunks
        all_chunks = existing_chunks + new_chunks
        
        # Re-tokenize everything
        tokenized = [_tokenize(c["text"]) for c in all_chunks]
        bm25 = BM25Okapi(tokenized)

        # Save back to pickle
        os.makedirs(os.path.dirname(BM25_INDEX_PATH), exist_ok=True)
        with open(BM25_INDEX_PATH, "wb") as fh:
            pickle.dump({"bm25": bm25, "chunks": all_chunks}, fh)
