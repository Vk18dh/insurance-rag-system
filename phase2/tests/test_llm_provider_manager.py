import pytest
from unittest.mock import Mock, patch
from phase2.config.settings import Phase2Settings
from phase2.services.llm_provider_manager import LLMProviderManager, QueryProcessingException
import urllib.error

@pytest.fixture
def mock_settings():
    settings = Phase2Settings()
    settings.llm.primary_provider = "openrouter"
    settings.llm.secondary_provider = "groq"
    settings.llm.openrouter_api_key = "test-or-key"
    settings.llm.groq_api_key = "test-groq-key"
    settings.llm.failover_enabled = True
    settings.llm.retry_backoff_seconds = 0.01
    settings.llm.max_retries = 2
    return settings

def test_primary_success(mock_settings):
    manager = LLMProviderManager(mock_settings)
    
    with patch.object(manager.providers["openrouter"], "call_completions", return_value="{'result': 'primary'}") as mock_primary:
        with patch.object(manager.providers["groq"], "call_completions") as mock_secondary:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'result': 'primary'}"
            mock_primary.assert_called_once()
            mock_secondary.assert_not_called()

def test_primary_timeout_fallback(mock_settings):
    manager = LLMProviderManager(mock_settings)
    
    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("Timeout", step="api_call_timeout")) as mock_primary:
        with patch.object(manager.providers["groq"], "call_completions", return_value="{'result': 'secondary'}") as mock_secondary:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'result': 'secondary'}"
            mock_primary.assert_called_once()  # Fails immediately on timeout
            mock_secondary.assert_called_once()

def test_primary_429_fallback(mock_settings):
    manager = LLMProviderManager(mock_settings)
    
    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("Rate Limit", step="api_call_rate_limit")) as mock_primary:
        with patch.object(manager.providers["groq"], "call_completions", return_value="{'result': 'secondary'}") as mock_secondary:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'result': 'secondary'}"
            mock_primary.assert_called_once()
            mock_secondary.assert_called_once()

def test_primary_transient_retry_then_fallback(mock_settings):
    manager = LLMProviderManager(mock_settings)
    
    # E.g. simple api_call error retries max_retries times, then falls back
    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("Some Error", step="api_call")) as mock_primary:
        with patch.object(manager.providers["groq"], "call_completions", return_value="{'result': 'secondary'}") as mock_secondary:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'result': 'secondary'}"
            assert mock_primary.call_count == mock_settings.llm.max_retries
            mock_secondary.assert_called_once()

def test_both_providers_fail(mock_settings):
    manager = LLMProviderManager(mock_settings)
    
    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("Primary Error", step="api_call_5xx")) as mock_primary:
        with patch.object(manager.providers["groq"], "call_completions", side_effect=QueryProcessingException("Secondary Error", step="api_call_5xx")) as mock_secondary:
            with pytest.raises(QueryProcessingException) as exc:
                manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert "Secondary Error" in str(exc.value)
            assert mock_primary.call_count == 1
            assert mock_secondary.call_count == mock_settings.llm.max_retries

def test_configuration_validation_failover_without_keys():
    # If failover is enabled but no keys are present, settings validator should catch it
    # However we're testing the manager here directly if it gets weird settings
    settings = Phase2Settings()
    settings.llm.openrouter_api_key = None
    settings.llm.groq_api_key = None
    settings.llm.primary_provider = "openrouter"
    settings.llm.secondary_provider = "groq"
    
    manager = LLMProviderManager(settings)
    assert "openrouter" not in manager.providers
    assert "groq" not in manager.providers
    
    with pytest.raises(QueryProcessingException, match="No providers configured"):
        manager._execute_with_failover("prompt", 0.0, 100, "system")
