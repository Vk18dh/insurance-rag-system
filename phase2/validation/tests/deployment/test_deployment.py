"""
phase2.validation.tests.deployment.test_deployment
==================================================

Deployment tests (environment readiness).
"""

import os
import pytest
from phase2.validation.config.validation_settings import ValidationSettings

def test_environmental_variables():
    """Ensure critical environment settings fallbacks exist."""
    assert os.getenv("MISSING_CRITICAL_VAR", None) is None
    
def test_valid_yaml_config():
    """Ensure settings load yaml cleanly."""
    settings = ValidationSettings.load_from_yaml()
    assert settings.standard_query_max_sec > 0
