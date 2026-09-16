import pytest
from unittest.mock import Mock, patch
import urllib.error
from phase2.config.settings import Phase2Settings
from phase2.services.llm_provider_manager import LLMProviderManager
from phase2.exceptions.query_exception import QueryProcessingException

@pytest.fixture
def mock_settings():
    settings = Phase2Settings()
    settings.llm.primary_provider = "openrouter"
    settings.llm.secondary_provider = "groq"
    settings.llm.openrouter_api_key = "MOCK_OPENROUTER_API_KEY_PLACEHOLDER"
    settings.llm.groq_api_key = "MOCK_GROQ_API_KEY_PLACEHOLDER"
    settings.llm.failover_enabled = True
    settings.llm.retry_backoff_seconds = 0.01
    settings.llm.max_retries = 3
    # Clear class-level cooldown state to prevent cross-test contamination
    LLMProviderManager._provider_health.clear()
    return settings

# TEST 1: OpenRouter success -> OpenRouter response returned
def test_1_openrouter_success(mock_settings):
    manager = LLMProviderManager(mock_settings)
    with patch.object(manager.providers["openrouter"], "call_completions", return_value="{'res': 'OR'}") as mock_or:
        with patch.object(manager.providers["groq"], "call_completions") as mock_groq:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'res': 'OR'}"
            mock_or.assert_called_once()
            mock_groq.assert_not_called()

# TEST 2: OpenRouter 404 -> Groq success -> Groq response returned
def test_2_openrouter_404_fallback(mock_settings):
    manager = LLMProviderManager(mock_settings)
    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("404", step="api_call_not_found")) as mock_or:
        with patch.object(manager.providers["groq"], "call_completions", return_value="{'res': 'Groq'}") as mock_groq:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'res': 'Groq'}"
            mock_or.assert_called_once() # Immediate failover, no retries
            mock_groq.assert_called_once()

# TEST 3: OpenRouter timeout -> Groq success -> Groq response returned
def test_3_openrouter_timeout_fallback(mock_settings):
    manager = LLMProviderManager(mock_settings)
    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("Timeout", step="api_call_timeout")) as mock_or:
        with patch.object(manager.providers["groq"], "call_completions", return_value="{'res': 'Groq'}") as mock_groq:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'res': 'Groq'}"
            assert mock_or.call_count == 3 # Retried 3 times
            mock_groq.assert_called_once()

# TEST 4: OpenRouter 429 -> retries -> Groq success
def test_4_openrouter_429_fallback(mock_settings):
    manager = LLMProviderManager(mock_settings)
    
    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("429", step="api_call_rate_limit")) as mock_or:
        with patch.object(manager.providers["groq"], "call_completions", return_value="{'res': 'Groq'}") as mock_groq:
            res = manager._execute_with_failover("prompt", 0.0, 100, "system")
            assert res == "{'res': 'Groq'}"
            assert mock_or.call_count == 1 # Cooldown skips immediately, no retries
            mock_groq.assert_called_once()

# TEST 5: Groq 1 404 -> Groq 2 success
def test_5_groq_404_fallback(mock_settings):
    # We need to test that if openrouter fails and groq fails, and local fails, it raises an exception
    manager = LLMProviderManager(mock_settings)

    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("OR 404", step="api_call_not_found")) as mock_or:
        with patch.object(manager.providers["groq"], "call_completions", side_effect=QueryProcessingException("Groq 404", step="api_call_not_found")) as mock_groq:
            with patch.object(manager.providers["local"], "call_completions", side_effect=QueryProcessingException("Local fail", step="api_call_failed")) as mock_local:
                with pytest.raises(QueryProcessingException) as exc:
                    manager._execute_with_failover("prompt", 0.0, 100, "system")
                assert exc.value.step == "api_call_failed" # Should be the last one's error

def test_6_groq_timeout_fallback(mock_settings):
    manager = LLMProviderManager(mock_settings)

    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("OR 404", step="api_call_not_found")) as mock_or:
        with patch.object(manager.providers["groq"], "call_completions", side_effect=QueryProcessingException("Timeout", step="api_call_timeout")) as mock_groq:
            with patch.object(manager.providers["local"], "call_completions", side_effect=QueryProcessingException("Local fail", step="api_call_timeout")) as mock_local:
                with pytest.raises(QueryProcessingException) as exc:
                    manager._execute_with_failover("prompt", 0.0, 100, "system")
                assert exc.value.step == "api_call_timeout"

def test_7_both_providers_fail(mock_settings):
    manager = LLMProviderManager(mock_settings)

    with patch.object(manager.providers["openrouter"], "call_completions", side_effect=QueryProcessingException("OR 404", step="api_call_not_found")) as mock_or:
        with patch.object(manager.providers["groq"], "call_completions", side_effect=QueryProcessingException("Groq 404", step="api_call_not_found")) as mock_groq:
            with patch.object(manager.providers["local"], "call_completions", side_effect=QueryProcessingException("Local fail", step="api_call_not_found")) as mock_local:
                with pytest.raises(QueryProcessingException) as exc:
                    manager._execute_with_failover("prompt", 0.0, 100, "system")
                assert "api_call_not_found" in str(exc.value.step)
        mock_or.assert_called_once()
        mock_groq.assert_called_once()
