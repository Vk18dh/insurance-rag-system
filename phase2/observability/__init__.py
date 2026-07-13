"""
phase2.observability
====================
Centralized, non-invasive Observability Layer for the Agentic RAG pipeline.

Public surface:
    ObservabilityFacade   – single entry-point used by the Orchestrator
    ObservabilityFactory  – constructs the facade from Phase2Settings

Nothing in this package modifies agent business logic.
"""

from phase2.observability.facade import ObservabilityFacade, ObservabilityFactory

__all__ = ["ObservabilityFacade", "ObservabilityFactory"]
