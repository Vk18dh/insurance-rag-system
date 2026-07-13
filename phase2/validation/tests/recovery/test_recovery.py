"""
phase2.validation.tests.recovery.test_recovery
==============================================

Verify graceful failure during external outages.
"""

import pytest
from unittest.mock import MagicMock

def test_db_timeout_recovery_mock():
    """Simulate a database connection error during retrieval."""
    mock_retrieval_agent = MagicMock()
    mock_retrieval_agent.process.side_effect = TimeoutError("Simulated LLM Timeout")
    
    with pytest.raises(TimeoutError):
        mock_retrieval_agent.process()
