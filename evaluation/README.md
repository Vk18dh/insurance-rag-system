# Insurance RAG Evaluation & Benchmark Suite

This directory contains the complete, reproducible, evidence-based evaluation framework for the Insurance RAG system ([Vk18dh/insurance-rag-system](https://github.com/Vk18dh/insurance-rag-system)).

---

## 1. Directory Structure

```text
evaluation/
├── README.md                      # Replication guide and CLI instructions
├── REPORT.md                      # Comprehensive empirical evaluation report
├── summary.json                   # Machine-readable summary of metrics, counts, and run state
├── corpus_manifest.csv            # Manifest of the 8 accessible PDFs and chunk counts
├── questions_for_review.csv       # 100 corpus-aligned evaluation queries across 10 categories
├── reviewer_guide.md              # Reviewer instructions, scoring rubric, and adjudication rules
├── metric_tables.csv              # Controlled retrieval baseline comparison table
├── raw_run_records.jsonl          # Raw query-by-query retrieval records (100 cases * 4 baselines)
├── software_test_report.md        # Detailed software test execution breakdown
├── inspect_corpus.py              # Script to inspect documents, compute SHA-256 and chunk overlap
├── build_evaluation_dataset.py    # Script generating questions_for_review.csv and reviewer_guide.md
├── run_retrieval_benchmarks.py    # Script executing the controlled retrieval experiments
└── raw/                           # Raw pytest logs and execution reports
    ├── pytest_phase2_tests.log
    ├── pytest_backend_tests.log
    ├── pytest_observability_tests.log
    ├── pytest_validation_tests.log
    ├── phase2_validation_runner.log
    ├── validation_report_20261011_055657.md
    └── validation_report_20261011_055657.json
```

---

## 2. Environment & Prerequisites

- **OS:** Windows 11 (or Linux/macOS with equivalent Python 3.11–3.13)
- **Python Version:** Python 3.13.7
- **Key Dependencies:**
  - `chromadb >= 1.5.0`
  - `sentence-transformers >= 5.0.0`
  - `rank-bm25 >= 0.2.2`
  - `pypdf >= 6.0.0`
  - `pytest >= 9.0.0`
  - `fastapi >= 0.130.0`

---

## 3. Step-by-Step Reproduction Instructions

### Step 1: Software Test Suite Execution
Execute the automated test suites and capture raw logs:

```powershell
# Phase 2 Agent & Service Tests
pytest phase2/tests/ -v | Out-File -FilePath evaluation/raw/pytest_phase2_tests.log -Encoding utf8

# Backend & API Tests
$env:PYTHONPATH="."
pytest backend/app/tests/ -v | Out-File -FilePath evaluation/raw/pytest_backend_tests.log -Encoding utf8

# Observability Tests
pytest phase2/observability/tests/ -v | Out-File -FilePath evaluation/raw/pytest_observability_tests.log -Encoding utf8

# Validation Runner & Tests
pytest phase2/validation/tests/ -v | Out-File -FilePath evaluation/raw/pytest_validation_tests.log -Encoding utf8
python -m phase2.validation
```

### Step 2: Corpus Inspection & Manifest Generation
Audit accessible PDF documents, verify SHA-256 hashes, page counts, and chunk index synchronization between ChromaDB and BM25:

```powershell
python evaluation/inspect_corpus.py
```

### Step 3: Dataset Generation
Build the 100-case evaluation set across 10 balanced categories:

```powershell
python evaluation/build_evaluation_dataset.py
```

### Step 4: Controlled Retrieval Benchmarks
Run all 100 questions through the 4 controlled retrieval baselines (BM25, Dense, Hybrid, Hybrid+Verification):

```powershell
python evaluation/run_retrieval_benchmarks.py
```

All raw outputs will be written to `evaluation/raw_run_records.jsonl`, `evaluation/metric_tables.csv`, and `evaluation/summary.json`.
