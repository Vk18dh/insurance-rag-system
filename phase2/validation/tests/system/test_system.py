"""
phase2.validation.tests.system.test_system
==========================================

End-to-end system testing simulating real external clients.
"""

import pytest
from unittest.mock import MagicMock
from phase2.validation.services import MockDataProvider

def test_system_standard_flow():
    """Ensure standard query workflow can be mapped via mock inputs."""
    provider = MockDataProvider()
    queries = provider.get_mock_queries("standard")
    assert len(queries) > 0
    assert "Jeevan Anand" in queries[0]
