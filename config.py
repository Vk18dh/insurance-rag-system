"""
config.py — Central configuration for the Insurance Knowledge Assessment System.
All paths, model names, and tuneable parameters live here.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────── Directory Paths ────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
JSON_DIR = os.path.join(BASE_DIR, "data", "extracted")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma_db")
BM25_INDEX_PATH = os.path.join(BASE_DIR, "data", "bm25_index.pkl")

# ──────────────────────────── Model Settings ─────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gemma-3-27b-it"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# ──────────────────────────── Chunking Parameters ────────────────────────
CHUNK_SIZE = 4096
CHUNK_OVERLAP = 512

# ──────────────────────────── Retrieval Parameters ───────────────────────
TOP_K = 8
BM25_WEIGHT = 0.5
VECTOR_WEIGHT = 0.5

# ──────────────────────────── ChromaDB ───────────────────────────────────
CHROMA_COLLECTION_NAME = "insurance_docs"

# ──────────────────────────── Logging Configuration ──────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_LEVEL = logging.INFO


def setup_logging():
    """Initialise project-wide logging."""
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
    return logging.getLogger("insurance_rag")


def ensure_directories():
    """Create required data directories if they don't exist."""
    for directory in [PDF_DIR, JSON_DIR, CHROMA_DIR]:
        os.makedirs(directory, exist_ok=True)
