"""
phase2.validation.tests.security.test_security
==============================================

Security tests. Validates prompt injection resilience.
"""

import pytest
from phase2.validation.services import MockDataProvider
from phase2.validation.config.validation_settings import ValidationSettings

def test_prompt_injection_safety():
    provider = MockDataProvider()
    settings = ValidationSettings()
    
    injections = provider.get_malicious_payloads()
    
    assert len(injections) >= 3
    assert "ignore previous instructions" in injections[1].lower() or "developer mode" in injections[2].lower()
    assert settings.fail_on_prompt_injection is True
