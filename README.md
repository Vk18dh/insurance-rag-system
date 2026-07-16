# 🛡️ Production-Grade AI Insurance Knowledge System

A state-of-the-art, **Multi-Agent RAG (Retrieval-Augmented Generation)** platform designed exclusively for high-stakes insurance policy and regulatory compliance analysis (LIC & IRDAI). 

Built to eliminate AI hallucinations, this platform leverages a deterministic strict-evaluation architecture providing **Human-In-The-Loop safety bounds**, sophisticated regulatory risk assessment, and beautiful structural markdown outputs.

---

## 🚀 Key Features

* **Strict Safety Boundaries:** Automatically halts execution and triggers a Human-in-the-Loop review if contradictory policy evidence, legal hazards, or out-of-domain logic is detected.
* **Multi-Agent Orchestration:** 
  * 🧠 *Query Understanding Agent:* Evaluates domain limits and extracts critical policy entities.
  * ⚖️ *Reasoning Agent:* Traces explicit logical syllogisms mapped directly to chunked policy evidence.
  * 🛑 *Risk Assessment Agent:* Flags unverified regulatory or financial assertions preventing unauthorized financial advice.
  * 🔍 *Contradiction Agent:* Employs cross-policy validation to detect logic gaps.
* **Hybrid Retrieval System:** Merges semantic vector similarity (*ChromaDB*) with exacting keyword preservation (*BM25*) to never miss an obscure clause.
* **Beautiful Structural Responses:** Generates pristine, highly readable Gemini-style markdown summaries strictly detailing what is known (and what isn't) natively.
* **Dockerized Microservices:** Seamless deployment spanning a React UI, FastAPI Backend, and Vector Databases.

---

## 🏗️ Architecture

```text
majorcode/
├── backend/            # FastAPI orchestration endpoints and DI containers
├── frontend/           # React + Material UI dashboard with visual safety banners (Vite)
├── phase2/             # Multi-Agent logic, LLM Prompt adapters, and core services
├── data/               # Vector bounds (ChromaDB + BM25) and original PDF artifacts
└── docker-compose.yml  # Zero-configuration production scale orchestrator
```

### Tech Stack
* **Frontend:** React, TypeScript, Material-UI, Vite
* **Backend:** Python, FastAPI, Pydantic, Pydantic-Settings
* **AI & Data Layer:** OpenRouter (LLM Actuator), ChromaDB, BM25(Rank-BM25), BGE-Large (Embeddings)
* **DevOps:** Docker, Docker Compose

---

## ⚙️ Quick Start (Docker Run)

Launch the entire AI architecture effortlessly.

### 1. Configure the Environment
Copy the example environment configuration securely.
```bash
cp .env.phase2.example .env.phase2
```
Edit `.env.phase2` to inject your **OpenRouter API Key**. 

### 2. Boot the Platform
```bash
docker-compose up -d --build
```
*Note: Make sure Docker Desktop is actively running.*

### 3. Access the Dashboard
Navigate to your portal dynamically:
👉 **[http://localhost:5173](http://localhost:5173)**

---

## 🚨 Understanding Safety Constraints

The AI employs a visual traffic-light style boundary validation on the front end mapping to exact constraint thresholds natively:

| UI Alert | Description | Trigger Example |
| :--- | :--- | :--- |
| **Normal (No Banner)** | Fully verified policy insights | *"What is the minimum age for LIC Jeevan Shagun?"* |
| **🟠 REGULATORY RISK** | Financial advice limits, legal risks, or lack of explicit evidence. Routes to human expert. | *"If I lie about a pre-existing medical issue, can I still get the policy payout?"* |
| **🔴 LOW CONFIDENCE** | Out-of-Domain bounds. The AI could not find related evidence and actively refuses hallucination. | *"Who won the world cup in 2022?"* |

---

## 🧑‍💻 Contributing
This pipeline executes complex deterministic mappings. Please observe the rigid constraints outlined in `phase2/interfaces` if refactoring logical boundaries to prevent regressions against the orchestrator.
