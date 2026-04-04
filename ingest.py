"""
ingest.py — Document Ingestion & High-Resolution OCR Pipeline.

Processes LIC Policy PDFs and IRDAI Annual Reports:
  1.  Extracts elements (text, tables, titles) via unstructured hi_res OCR.
  2.  Post-processes: removes headers/footers, normalises whitespace,
      merges broken sentences, converts tables to row-wise text.
  3.  Attaches mandatory metadata per element.
  4.  Saves structured JSON per document to avoid reprocessing.
"""

import json
import os
import re
import sys
import traceback

from config import PDF_DIR, JSON_DIR, setup_logging, ensure_directories

logger = setup_logging()


# ═══════════════════════════════════════════════════════════════════════════
#  PDF Processing
# ═══════════════════════════════════════════════════════════════════════════

def process_pdf(filepath: str) -> list:
    """
    Extract elements from a single PDF using unstructured hi_res strategy.

    Args:
        filepath: Absolute or relative path to the PDF file.

    Returns:
        List of unstructured Element objects.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If OCR / parsing fails entirely.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"PDF not found: {filepath}")

    try:
        from unstructured.partition.pdf import partition_pdf

        elements = partition_pdf(
            filename=filepath,
            strategy="auto",
            languages=["eng"],
        )

        if not elements:
            raise ValueError(f"No content extracted from: {filepath}")

        logger.info("Extracted %d elements from %s", len(elements), filepath)
        return elements

    except ImportError:
        logger.error(
            "The 'unstructured' library is not installed. "
            "Run: pip install 'unstructured[all-docs]'"
        )
        raise
    except Exception as exc:
        logger.error("Failed to process %s: %s", filepath, exc)
        raise ValueError(f"OCR/parsing failure for {filepath}") from exc


# ═══════════════════════════════════════════════════════════════════════════
#  Post-Processing Utilities
# ═══════════════════════════════════════════════════════════════════════════

_HEADER_FOOTER_PATTERNS = [
    re.compile(r"^page\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"^\d+\s*$"),                       # bare page numbers
    re.compile(r"^(confidential|draft|internal)", re.IGNORECASE),
    re.compile(r"(all\s*rights\s*reserved)", re.IGNORECASE),
]


def _is_header_or_footer(text: str) -> bool:
    """Return True if the text looks like a header or footer."""
    stripped = text.strip()
    if len(stripped) < 5:
        return True
    return any(pat.search(stripped) for pat in _HEADER_FOOTER_PATTERNS)


def _normalise_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def _merge_broken_sentences(texts: list[str]) -> list[str]:
    """
    Merge lines that appear to be broken mid-sentence.
    A line that does not end with sentence-ending punctuation is merged
    with the following line.
    """
    if not texts:
        return texts

    merged: list[str] = []
    buffer = texts[0]

    for line in texts[1:]:
        # If the buffer doesn't end with sentence-ending punctuation, merge.
        if buffer and not re.search(r"[.!?;:]\s*$", buffer):
            buffer = buffer + " " + line
        else:
            merged.append(buffer)
            buffer = line

    merged.append(buffer)
    return merged


def _table_to_text(html_table: str) -> str:
    """
    Convert an HTML table string into readable row-wise text.
    Falls back to the raw string if parsing fails.
    """
    try:
        from html.parser import HTMLParser

        class _TableParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.rows: list[list[str]] = []
                self._current_row: list[str] = []
                self._current_cell: str = ""
                self._in_cell = False

            def handle_starttag(self, tag, attrs):
                if tag in ("td", "th"):
                    self._in_cell = True
                    self._current_cell = ""
                elif tag == "tr":
                    self._current_row = []

            def handle_endtag(self, tag):
                if tag in ("td", "th"):
                    self._in_cell = False
                    self._current_row.append(self._current_cell.strip())
                elif tag == "tr":
                    if self._current_row:
                        self.rows.append(self._current_row)

            def handle_data(self, data):
                if self._in_cell:
                    self._current_cell += data

        parser = _TableParser()
        parser.feed(html_table)

        if not parser.rows:
            return html_table

        lines = []
        for i, row in enumerate(parser.rows):
            lines.append(f"Row {i + 1}: " + " | ".join(row))
        return "\n".join(lines)

    except Exception:
        return html_table


# ═══════════════════════════════════════════════════════════════════════════
#  Element → Structured Dict
# ═══════════════════════════════════════════════════════════════════════════

def _classify_element(element) -> str:
    """Return a normalised element_type string."""
    category = str(getattr(element, "category", "")).lower()
    if "table" in category:
        return "table"
    if "title" in category or "header" in category:
        return "title"
    return "text"


def _detect_section_title(element, previous_titles: list[str]) -> str:
    """
    Attempt to detect the section title for a given element.
    Uses the element's own title metadata or the most recent title element.
    """
    # Some unstructured elements carry a parent title in metadata
    meta = getattr(element, "metadata", None)
    if meta:
        parent = getattr(meta, "parent_id", None)
        if parent and previous_titles:
            return previous_titles[-1]

    if _classify_element(element) == "title":
        return str(element).strip()

    return previous_titles[-1] if previous_titles else "Unknown"


def post_process_elements(elements: list, filename: str) -> list[dict]:
    """
    Clean, enrich, and structure raw unstructured elements.

    Returns:
        List of dicts, each with keys:
          text, element_type, page_number, section_title, source_document
    """
    results: list[dict] = []
    recent_titles: list[str] = []

    for elem in elements:
        raw_text = str(elem).strip()
        if not raw_text:
            continue

        elem_type = _classify_element(elem)

        # Skip headers / footers
        if _is_header_or_footer(raw_text) and elem_type == "text":
            continue

        # Normalise whitespace
        clean_text = _normalise_whitespace(raw_text)

        # Convert tables to readable text
        if elem_type == "table":
            html = getattr(getattr(elem, "metadata", None), "text_as_html", None)
            if html:
                clean_text = _table_to_text(html)

        # Track titles for section detection
        section = _detect_section_title(elem, recent_titles)
        if elem_type == "title":
            recent_titles.append(clean_text)

        # Page number
        meta = getattr(elem, "metadata", None)
        page = getattr(meta, "page_number", None) if meta else None

        results.append({
            "text": clean_text,
            "element_type": elem_type,
            "page_number": page,
            "section_title": section,
            "source_document": filename,
        })

    # Merge broken sentences within text elements
    text_items = [r for r in results if r["element_type"] == "text"]
    if text_items:
        merged_texts = _merge_broken_sentences([t["text"] for t in text_items])
        idx = 0
        for r in results:
            if r["element_type"] == "text" and idx < len(merged_texts):
                r["text"] = merged_texts[idx]
                idx += 1

    logger.info(
        "Post-processed %d elements → %d structured entries for %s",
        len(elements), len(results), filename,
    )
    return results


# ═══════════════════════════════════════════════════════════════════════════
#  JSON Persistence
# ═══════════════════════════════════════════════════════════════════════════

def save_json(data: list[dict], output_path: str) -> None:
    """Write structured element data to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump({"elements": data, "source_document": data[0]["source_document"]}, fh, indent=2, ensure_ascii=False)
    logger.info("Saved JSON → %s", output_path)


# ═══════════════════════════════════════════════════════════════════════════
#  Main Ingestion Loop
# ═══════════════════════════════════════════════════════════════════════════

def run_ingestion() -> list[str]:
    """
    Process all PDFs in PDF_DIR, save structured JSON to JSON_DIR.

    Returns:
        List of JSON file paths that were created or already existed.
    """
    ensure_directories()

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.warning("No PDF files found in %s", PDF_DIR)
        return []

    logger.info("Found %d PDF(s) in %s", len(pdf_files), PDF_DIR)
    json_paths: list[str] = []

    for pdf_name in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        json_name = os.path.splitext(pdf_name)[0] + ".json"
        json_path = os.path.join(JSON_DIR, json_name)

        # Skip already-processed files
        if os.path.isfile(json_path):
            logger.info("Skipping (already processed): %s", pdf_name)
            json_paths.append(json_path)
            continue

        try:
            elements = process_pdf(pdf_path)
            structured = post_process_elements(elements, pdf_name)

            if not structured:
                logger.warning("No usable content from %s — skipping.", pdf_name)
                continue

            save_json(structured, json_path)
            json_paths.append(json_path)

        except FileNotFoundError:
            logger.error("File disappeared during processing: %s", pdf_name)
        except ValueError as ve:
            logger.error("Content error for %s: %s", pdf_name, ve)
        except Exception:
            logger.error(
                "Unexpected error processing %s:\n%s",
                pdf_name, traceback.format_exc(),
            )

    logger.info("Ingestion complete. %d JSON file(s) ready.", len(json_paths))
    return json_paths


# ═══════════════════════════════════════════════════════════════════════════
#  CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_ingestion()
