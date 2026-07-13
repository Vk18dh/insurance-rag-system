"""
phase2 — Agentic Intelligence Layer for the AI-Driven Insurance Knowledge Assessment System.

This package implements the Phase 2 Agent Layer that sits above the existing Phase 1
Hybrid RAG system. It provides:
    - Query Understanding Agent
    - Retrieval Agent
    - Verification Agent
    - Reasoning Agent
    - Risk Agent
    - Contradiction Detection Agent
    - Agent Orchestrator
    - Response Builder

All agents are coordinated exclusively through the Orchestrator.
No agent calls another agent directly.
"""

__version__ = "2.0.0"
__author__ = "Phase 2 Agentic RAG Team"
