import json
from collections import defaultdict
from llama_index.core.node_parser import SentenceSplitter

CHUNK_SIZE = 1024
CHUNK_OVERLAP = 100

with open("data/extracted/Final Policy Document LIC's Bima Jyoti V03_website.json", "r", encoding="utf-8") as fh:
    data = json.load(fh)
elements = data.get("elements", [])

docs_pages = defaultdict(list)
for elem in elements:
    doc = elem.get("source_document", "unknown")
    page = elem.get("page_number", 0)
    docs_pages[(doc, page)].append(elem)

splitter = SentenceSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    paragraph_separator="\n\n",
    secondary_chunking_regex="[^,.;。?!]+[,.;。?!]?",
)

found = False
for (doc, page), elems in docs_pages.items():
    page_text = "\n".join([e.get("text", "").strip() for e in elems if e.get("text", "").strip()])
    splits = splitter.split_text(page_text)
    for i, s in enumerate(splits):
        if "following benefits are payable" in s or "Sum Assured on Maturity" in s:
            print(f"FOUND IN SPLIT {i}, PAGE {page}:")
            print(s[:300])
            print("...")
            found = True

if not found:
    print("FAILED TO FIND MATURITY BENEFIT IN CHUNKS!")
