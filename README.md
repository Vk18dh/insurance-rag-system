# 🛡️ Production-Grade AI Insurance Knowledge System

A state-of-the-art, **Multi-Agent RAG (Retrieval-Augmented Generation)** platform designed exclusively for high-stakes insurance policy and regulatory compliance analysis (LIC & IRDAI). 

Built to eliminate AI hallucinations, this platform unifies an advanced offline **PDF Ingestion & Indexing Pipeline** (Phase 1) with a deterministic, **Multi-Agent Orchestration & React Dashboard** (Phase 2). It leverages a strict-evaluation architecture providing **Human-In-The-Loop safety bounds**, sophisticated regulatory risk assessment, and beautiful structural markdown outputs.

---

## 🚀 Key Features

* **High-Res OCR Processing:** Ingests complex multi-column LIC PDFs explicitly preserving structural insurance clauses through localized deduplication.
* **Hybrid Retrieval (50/50):** Merges semantic vector similarity (*ChromaDB*) with exacting keyword preservation (*BM25*) to never miss an obscure medical or financial clause.
* **Strict Out-of-Domain Denial:** Rigorously blocks code-generation, general trivia, and hallucinated mappings outside of the policy context via precise boundary NLP checks.
* **Strict Safety Boundaries:** Automatically halts execution and triggers a Human-in-the-Loop review if contradictory policy evidence, legal hazards, or out-of-domain logic is detected natively.
* **Multi-Agent Orchestration:** 
  * 🧠 *Query Understanding Agent:* Evaluates domain limits and extracts critical policy entities.
  * ⚖️ *Reasoning Agent:* Traces explicit logical syllogisms mapped directly to chunked policy evidence.
  * 🛑 *Risk Assessment Agent:* Flags unverified regulatory or financial assertions preventing unauthorized advice.
  * 🔍 *Contradiction Agent:* Employs cross-policy validation to detect logic gaps.
* **Beautiful Structural Responses:** Generates pristine, Gemini-style markdown summaries strictly detailing what is known (and what isn't) natively via OpenRouter configurations.

---

## 🏗️ Architecture Stack

### Core Tooling
* **Frontend:** React, TypeScript, Material-UI, Vite
* **Backend:** Python, FastAPI, Pydantic 
* **Data Processing:** OpenCV, Unstructured (OCR), Langchain
* **AI & Retrieval Level:** OpenRouter (LLM Actuation), ChromaDB, BM25 (Rank-BM25), BGE-Large
* **DevOps:** Docker, Docker Compose

### System Data Flow
```text
[Phase 1] PDF Documents → (OCR ingest.py) → JSON → (Chunking index.py) → BM25 & ChromaDB 
                                                                              ↓
[Phase 2] React Dashboard → FastAPI Router → Multi-Agent Orchestrator → Final Verified Markdown
```

---

## 📁 Repository Structure

```text
majorcode/
├── backend/            # FastAPI REST endpoints and dependency injections (Phase 2)
├── frontend/           # React + Material UI dashboard with visual safety banners (Phase 2)
├── phase2/             # Multi-Agent logic, LLM Prompt adapters, and safety constraint services
├── data/               
│   ├── pdfs/           # Input legacy PDF documents (LIC, IRDAI)
│   ├── chroma_db/      # Persistent Vector storage
│   └── bm25_index.pkl  # Compiled keyword index bounds
├── app.py              # Phase 1 CLI application for hybrid search
├── ingest.py           # Core OCR document extraction algorithms
├── index.py            # Phase 1 chunking and localized vector encoding
└── docker-compose.yml  # Production scale orchestrator for Phase 2 components
```

---

## ⚙️ Quick Start Guide

You can run this project via the CLI (Phase 1) or as a Full-Stack Web Application (Phase 2).

### Step 1: Document Processing (Phase 1)
Make sure your original PDFs reside inside `data/pdfs/`.

```bash
# 1. Create a virtual environment and install dependencies
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS / Linux
pip install -r requirements.txt

# 2. Extract PDFs using high-res OCR
python ingest.py 

# 3. Compile the Hybrid Indices (Chroma + BM25)
python index.py
```

*Optional: Test the embeddings securely using the CLI interactive loop:*
```bash
python app.py
```

### Step 2: Full-Stack Multi-Agent Launch (Phase 2)

Launch the entire AI architecture effortlessly leveraging Docker containers natively.

```bash
# 1. Configure the Environment
cp .env.phase2.example .env.phase2

# Edit your newly created .env.phase2 file to inject your OpenRouter API Key
```

```bash
# 2. Boot the Platform seamlessly
docker-compose up -d --build
```

Access the React Web Dashboard natively mapped at: **[http://localhost:3000](http://localhost:3000)**

---

## 🚨 Understanding Safety Constraints (UI Dashboard)

The Phase 2 frontend employs a visual traffic-light style boundary validation mapped to exact constraint thresholds natively:

| UI Alert | Description | Trigger Example |
| :--- | :--- | :--- |
| **Normal (No Banner)** | Fully verified policy insights | *"What is the minimum age for LIC Jeevan Shagun?"* |
| **🟠 REGULATORY RISK** | Financial advice limits, legal risks, or lack of explicit evidence. Routes to human expert. | *"If I lie about a pre-existing medical issue, can I still get the policy payout?"* |
| **🔴 LOW CONFIDENCE** | Out-of-Domain bounds. The AI could not find related evidence and actively refuses hallucination. | *"Who won the world cup in 2022?"* |

---

## 🧑‍💻 Contributing
This pipeline executes complex deterministic mappings ensuring insurance compliance securely. Please observe the rigid constraints outlined in `phase2/interfaces` if refactoring logical boundaries to prevent regressions against the primary Orchestrator.
