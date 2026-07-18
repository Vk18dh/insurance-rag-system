# Vercel AI Frontend Requirements: Insurance Agentic RAG System

## Overview
Generate a modern, premium Next.js frontend (React, Tailwind CSS, TypeScript, Shadcn UI, Framer Motion) for an AI Insurance Knowledge Assessment System. The user can query complex insurance policy questions, receive grounded LLM-generated answers, and review the source citations used by the AI.

## General Design Aesthetic
- **Premium, Trustworthy, Modern:** The application deals with insurance and compliance, it should look extremely professional, trustworthy, and sleek.
- **Color Palette:** Deep navy/slate blues mixed with vibrant accents for highlights (e.g., trust-inspiring blue, teal, or violet).
- **Glassmorphism & Micro-animations:** Apply subtle frosted glass effects on cards/panels. Use graceful load-in animations and hover states.
- **Dark Mode Support:** Built-in seamless dark/light mode toggle.

## Core Features & Pages

### 1. Dashboard / Query Page
- **Hero Section:** Title: "AI Insurance Auditor". Subtitle: "Query regulatory policies and insurance rules with guaranteed citations."
- **Search Component:**
  - A large, prominent, glass-morphic search input (like a command palette).
  - Needs a loading state indicating when the AI is "Auditing Documents" or "Formulating Response".
- **Response Section:**
  - Displays the AI's `final_answer` rendering markdown smoothly using `react-markdown`.
  - **Metrics Panel:** Displays the `confidence_score` (shown as a percentage or progress circle), `execution_time_ms`, and `is_safe` status.
    - If `is_safe` is false, show a UI warning alert about potential regulatory risk or bounds checking failure.
    - If `is_safe` is true, show a green check/shield icon.
- **Citations / Sources Panel:**
  - Iterates over the `sources` array.
  - For each source: display a sleek card with the document name, page number, and a foldable accordion to reveal the snippet.

### 2. Login Page (Optional / If Needed)
- Standard modern login form (Username/Password).
- Interacts via the OAuth2 token endpoint if authentication is active.

## API Integration Details

Your Next.js components should communicate with the existing FastAPI backend. Ensure you configure environment variables for the API URL (`NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`).

### Endpoint 1: Query the RAG Pipeline
* **Method:** `POST`
* **Path:** `/api/v1/query`
* **Request Body (JSON):**
  ```json
  {
    "query": "What is the waiting period for the basic health insurance?"
  }
  ```
* **Response (JSON):**
  ```json
  {
    "query_id": "uuid-string",
    "final_answer": "Markdown formatted multi-paragraph response.",
    "confidence_score": 0.95,
    "is_safe": true,
    "sources": [
      {
        "document": "FS-CAN1282_NND",
        "page": 12,
        "content_snippet": "Actual text from the document...",
        "confidence": 1.0
      }
    ],
    "execution_time_ms": 1205.4
  }
  ```

### Endpoint 2: System Health (Backend Status)
* **Method:** `GET`
* **Path:** `/api/v1/health`
* **Response (JSON):**
  ```json
  {
    "status": "ok",
    "version": "1.0",
    "components": {}
  }
  ```

### Endpoint 3: System Readiness
* **Method:** `GET`
* **Path:** `/api/v1/ready`
* **Response (JSON):**
  ```json
  {
    "status": "ready"
  }
  ```

### Endpoint 4: Authentication (If active)
* **Method:** `POST`
* **Path:** `/api/v1/auth/login`
* **Content-Type:** `application/x-www-form-urlencoded`
* **Body:** `username=...&password=...`
* **Response:**
  ```json
  {
    "access_token": "jwt-token-string",
    "token_type": "bearer"
  }
  ```

## State Management & Fetching
- Use `react-query` (TanStack Query) or SWR for API fetching and caching.
- Show clear loading skeletons while the `POST /api/v1/query` request resolves.

## Requirements Summary Checklist
- [ ] Initialize standard Next.js (App Router) + Tailwind CSS + Shadcn UI setup.
- [ ] Implement Hero & Search bar.
- [ ] Wire up `POST /api/v1/query` fetching.
- [ ] Build the Answer display with markdown support.
- [ ] Build the dynamic confidence & safety indicator components.
- [ ] Build the citations accordion/cards.
- [ ] Ensure the design looks highly premium with modern spacing and typography (e.g., `Inter` or `Geist` font).
