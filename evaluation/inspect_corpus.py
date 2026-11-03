import os
import hashlib
import json
import pickle
import csv
import pypdf
import chromadb
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
JSON_DIR = os.path.join(BASE_DIR, "data", "extracted")
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma_db")
BM25_PATH = os.path.join(BASE_DIR, "data", "bm25_index.pkl")
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "corpus_manifest.csv")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_pdf_page_count(filepath):
    try:
        reader = pypdf.PdfReader(filepath)
        return len(reader.pages)
    except Exception as e:
        return f"Error: {e}"

def inspect():
    print("=== Inspecting Accessible Corpus ===")
    
    # 1. Load BM25 Index
    bm25_chunks = []
    if os.path.exists(BM25_PATH):
        with open(BM25_PATH, "rb") as f:
            data = pickle.load(f)
            bm25_chunks = data.get("chunks", [])
        print(f"BM25 Index Loaded: {len(bm25_chunks)} chunks from {BM25_PATH}")
    else:
        print(f"BM25 Index NOT found at {BM25_PATH}")

    # 2. Load ChromaDB Index
    chroma_chunks_count = 0
    chroma_docs_counter = Counter()
    chroma_ids = set()
    if os.path.exists(CHROMA_DIR):
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        try:
            coll = client.get_collection("insurance_docs")
            chroma_chunks_count = coll.count()
            # Fetch all metadata to count docs
            all_meta = coll.get(include=["metadatas"])
            for m in all_meta.get("metadatas", []):
                chroma_docs_counter[m.get("source_document", "unknown")] += 1
            chroma_ids = set(all_meta.get("ids", []))
            print(f"ChromaDB Collection 'insurance_docs' Loaded: {chroma_chunks_count} chunks")
        except Exception as e:
            print(f"Error accessing ChromaDB collection: {e}")
    else:
        print(f"ChromaDB directory NOT found at {CHROMA_DIR}")

    # BM25 breakdown
    bm25_docs_counter = Counter()
    bm25_ids = set()
    for c in bm25_chunks:
        bm25_docs_counter[c.get("source_document", "unknown")] += 1
        bm25_ids.add(c.get("chunk_id"))

    # Compare ID overlap
    id_overlap = len(chroma_ids.intersection(bm25_ids))
    print(f"Chunk ID Overlap between Dense and BM25: {id_overlap} / max({len(chroma_ids)}, {len(bm25_ids)})")

    # 3. PDF Files
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")] if os.path.exists(PDF_DIR) else []
    print(f"Found {len(pdf_files)} PDF files in {PDF_DIR}")

    manifest_rows = []
    total_pages = 0
    total_extracted_elements = 0

    titles = {
        "Final Policy Document LIC's Bima Jyoti V03_website.pdf": "LIC's Bima Jyoti (UIN: 512N339V03) Policy Document",
        "Final Policy doc_LIC's New SP Endowment_V03_website.pdf": "LIC's New Single Premium Endowment (UIN: 512N311V03)",
        "LIC_Jeevan_Shagun_Policy_inside_r.pdf": "LIC's Jeevan Shagun (Policy Conditions Inside)",
        "LIC_Jeevan_Shagun_front_r.pdf": "LIC's Jeevan Shagun (Front Schedule)",
        "Policy Document_Digi Credit Life_CC.pdf": "LIC's Digi Credit Life (Credit Linked Term Insurance)",
        "Policy Document_LIC's_Digi Term_V02.pdf": "LIC's Digi Term (UIN: 512N356V02)",
        "आईआरडीएआई वार्षिक रिपोर्ट _ IRDAI Annual Report 2024-25 (1).pdf": "IRDAI Annual Report 2024-25 (Bilingual Hindi/English)",
        "वार्षिक रिपोर्ट 2023-24 _ Annual Report 2023-24.pdf": "IRDAI Annual Report 2023-24 (Bilingual Hindi/English)"
    }

    limitations = {
        "Final Policy Document LIC's Bima Jyoti V03_website.pdf": "Tables converted to linear text blocks; complex multi-column clauses require contextual reconstruction.",
        "Final Policy doc_LIC's New SP Endowment_V03_website.pdf": "Tables converted to row-wise text; tabular benefit illustrations may lose column headers.",
        "LIC_Jeevan_Shagun_Policy_inside_r.pdf": "Compact scanned/typeset text; OCR strategy auto applied.",
        "LIC_Jeevan_Shagun_front_r.pdf": "Short schedule document (1 page), contains blank schedule placeholders.",
        "Policy Document_Digi Credit Life_CC.pdf": "Standard policy text; tables flattened.",
        "Policy Document_LIC's_Digi Term_V02.pdf": "Standard policy text; structured clauses.",
        "आईआरडीएआई वार्षिक रिपोर्ट _ IRDAI Annual Report 2024-25 (1).pdf": "Large bilingual regulatory report (Hindi + English). Large tables and complex statistical charts.",
        "वार्षिक रिपोर्ट 2023-24 _ Annual Report 2023-24.pdf": "Large bilingual regulatory report (Hindi + English). Complex nested financial statements."
    }

    doc_counter = 1
    for pdf_name in sorted(pdf_files):
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        sha = sha256_file(pdf_path)
        pages = get_pdf_page_count(pdf_path)
        if isinstance(pages, int):
            total_pages += pages
        
        # Check extraction
        json_name = os.path.splitext(pdf_name)[0] + ".json"
        json_path = os.path.join(JSON_DIR, json_name)
        extraction_status = "EXTRACTED" if os.path.exists(json_path) else "NOT_EXTRACTED"
        elem_count = 0
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    jdata = json.load(jf)
                    elems = jdata.get("elements", [])
                    elem_count = len(elems)
                    total_extracted_elements += elem_count
            except Exception as e:
                extraction_status = f"CORRUPT_JSON ({e})"

        bm25_count = bm25_docs_counter.get(pdf_name, 0)
        chroma_count = chroma_docs_counter.get(pdf_name, 0)
        
        if bm25_count > 0 and chroma_count > 0:
            index_status = f"INDEXED (Dense={chroma_count}, BM25={bm25_count})"
        elif bm25_count > 0:
            index_status = f"BM25_ONLY ({bm25_count})"
        elif chroma_count > 0:
            index_status = f"CHROMA_ONLY ({chroma_count})"
        else:
            index_status = "NOT_INDEXED"

        doc_id = f"DOC-{doc_counter:03d}"
        doc_counter += 1

        title = titles.get(pdf_name, os.path.splitext(pdf_name)[0])
        lim = limitations.get(pdf_name, "Standard extraction")

        manifest_rows.append({
            "document_id": doc_id,
            "file_name": pdf_name,
            "sha256": sha,
            "title": title,
            "page_count": pages,
            "extraction_method": "unstructured_hi_res_ocr (auto strategy, eng)",
            "extraction_status": extraction_status,
            "extracted_elements": elem_count,
            "dense_indexed_chunks": chroma_count,
            "bm25_indexed_chunks": bm25_count,
            "index_status": index_status,
            "table_ocr_limitations": lim
        })

    # Write CSV
    with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "document_id", "file_name", "sha256", "title", "page_count",
            "extraction_method", "extraction_status", "extracted_elements",
            "dense_indexed_chunks", "bm25_indexed_chunks", "index_status",
            "table_ocr_limitations"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in manifest_rows:
            writer.writerow(r)

    print(f"Manifest written to {MANIFEST_PATH}")
    print(f"Summary: {len(pdf_files)} PDFs, {total_pages} total pages, {total_extracted_elements} extracted elements.")
    print(f"Total Dense Chunks: {chroma_chunks_count}, Total BM25 Chunks: {len(bm25_chunks)}")

    # Return summary dict
    return {
        "pdf_count": len(pdf_files),
        "total_pages": total_pages,
        "total_extracted_elements": total_extracted_elements,
        "dense_chunks": chroma_chunks_count,
        "bm25_chunks": len(bm25_chunks),
        "chunk_id_overlap": id_overlap,
        "manifest_rows": manifest_rows
    }

if __name__ == "__main__":
    inspect()
