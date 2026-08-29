import pytest
import json
import time
import urllib.request
import urllib.error
from unittest.mock import patch, MagicMock

from phase2.config.settings import Phase2Settings, LLMSettings
from phase2.services.llm_provider_manager import LLMProviderManager
from phase2.exceptions.query_exception import QueryProcessingException

@pytest.fixture
def manager():
    settings = Phase2Settings()
    settings.llm = LLMSettings(
        openrouter_api_key="or_key",
        groq_api_key="g_key1",
        groq_api_key_2="g_key2",
        local_model="qwen2.5:3b",
        local_llm_base_url="http://mock-ollama:11434/api/chat",
        provider_cooldown_seconds=0.2, # short cooldown for tests
        max_retries=2,
        retry_backoff_seconds=0.01,
        failover_enabled=True
    )
    # Clear class-level health state before each test
    LLMProviderManager._provider_health = {}
    return LLMProviderManager(settings)

def build_mock_response(status=200, body=None):
    mock_resp = MagicMock()
    if body is None:
        body = {"choices": [{"message": {"content": '{"success": true}'}}]}
    mock_resp.read.return_value = json.dumps(body).encode("utf-8")
    mock_resp.status = status
    # Implement context manager methods
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None
    return mock_resp

def build_http_error(code, reason="Error"):
    fp = MagicMock()
    fp.read.return_value = b'{"error": "message"}'
    return urllib.error.HTTPError("url", code, reason, hdrs=None, fp=fp)

def mock_urlopen_side_effect(*responses):
    responses = list(responses)
    def side_effect(*args, **kwargs):
        if not responses:
            raise Exception("No more mocked responses provided!")
        resp = responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp
    return side_effect

@patch('urllib.request.urlopen')
def test_openrouter_success(mock_urlopen, manager):
    """1. OpenRouter success."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(build_mock_response(200))
    res = manager._execute_with_failover("prompt", 0.0, 10, "sys")
    assert "success" in res
    assert "openrouter" in mock_urlopen.call_args[0][0].full_url

@patch('urllib.request.urlopen')
def test_openrouter_402_to_groq_key1(mock_urlopen, manager):
    """2. OpenRouter 402 -> Groq Key 1."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(402), # OR fails with 402
        build_mock_response(200) # Groq 1 succeeds
    )
    res = manager._execute_with_failover("prompt", 0.0, 10, "sys")
    assert "success" in res
    assert mock_urlopen.call_count == 2
    assert "api.groq.com" in mock_urlopen.call_args_list[1][0][0].full_url

@patch('urllib.request.urlopen')
def test_openrouter_429_to_groq_key1(mock_urlopen, manager):
    """3. OpenRouter 429 -> Groq Key 1."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(429), # OR fails with 429
        build_mock_response(200) # Groq 1 succeeds
    )
    res = manager._execute_with_failover("prompt", 0.0, 10, "sys")
    assert "success" in res
    assert mock_urlopen.call_count == 2
    assert "api.groq.com" in mock_urlopen.call_args_list[1][0][0].full_url
    assert LLMProviderManager._provider_health["openrouter"]["status"] == "cooldown"

@patch('urllib.request.urlopen')
def test_groq_key1_429_to_groq_key2(mock_urlopen, manager):
    """4. Groq Key 1 429 -> Groq Key 2."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(404), # OR 404 (skip)
        build_http_error(429), # Groq 1 429
        build_mock_response(200) # Groq 2 succeeds
    )
    res = manager._execute_with_failover("prompt", 0.0, 10, "sys")
    assert "success" in res
    assert mock_urlopen.call_count == 3
    # Groq 1 in cooldown
    assert LLMProviderManager._provider_health["groq_key_1"]["status"] == "cooldown"
    # Ensure Groq 2 used the correct key (g_key2)
    req2 = mock_urlopen.call_args_list[2][0][0]
    assert req2.headers.get("Authorization") == "Bearer g_key2"

@patch('urllib.request.urlopen')
def test_groq_key1_failure_to_groq_key2(mock_urlopen, manager):
    """5. Groq Key 1 failure (5xx) -> Groq Key 2 success."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(404), # OR 404
        build_http_error(500), # Groq 1 attempt 1
        build_http_error(500), # Groq 1 attempt 2 (exhausts retries)
        build_mock_response(200) # Groq 2 succeeds
    )
    res = manager._execute_with_failover("prompt", 0.0, 10, "sys")
    assert mock_urlopen.call_count == 4

@patch('urllib.request.urlopen')
def test_all_cloud_fail_to_local(mock_urlopen, manager):
    """6. All cloud providers fail -> Local Ollama."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(401), # OR auth fail
        build_http_error(401), # Groq 1 auth fail
        build_http_error(401), # Groq 2 auth fail
        build_mock_response(200, body={"message": {"content": '{"local": true}'}}) # Local succeeds
    )
    res = manager._execute_with_failover("prompt", 0.0, 10, "sys")
    assert "local" in res
    assert mock_urlopen.call_count == 4
    # Ensure 4th call was to local ollama URL
    assert "11434" in mock_urlopen.call_args_list[3][0][0].full_url

@patch('urllib.request.urlopen')
def test_all_four_providers_fail(mock_urlopen, manager):
    """7. All four providers fail -> controlled provider-unavailable response."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(401),
        build_http_error(401),
        build_http_error(401),
        build_http_error(404) # Local missing model
    )
    with pytest.raises(QueryProcessingException) as exc:
        manager._execute_with_failover("prompt", 0.0, 10, "sys")
    
    assert exc.value.context["step"] == "api_call_exhausted"
    assert "exhausted" in str(exc.value)

@patch('urllib.request.urlopen')
def test_provider_cooldown(mock_urlopen, manager):
    """8. Provider cooldown prevents hammering."""
    # First call: OR gets 429, Groq1 gets 200
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(429),
        build_mock_response(200),
        # Second manager call: OR should be skipped instantly, goes straight to Groq1
        build_mock_response(200)
    )
    manager._execute_with_failover("prompt", 0.0, 10, "sys")
    
    # Fire another request immediately
    manager._execute_with_failover("prompt", 0.0, 10, "sys")
    
    # Total URL calls = 3 (OR 429, Groq1 200, Groq1 200)
    assert mock_urlopen.call_count == 3
    # Check that the last call was to Groq API
    assert "api.groq.com" in mock_urlopen.call_args_list[2][0][0].full_url

@patch('urllib.request.urlopen')
def test_cooldown_expiration(mock_urlopen, manager):
    """9. Cooldown expiration."""
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(429),
        build_mock_response(200),
        # Wait for cooldown, OR gets 200
        build_mock_response(200)
    )
    manager._execute_with_failover("prompt", 0.0, 10, "sys")
    
    time.sleep(0.25) # Exceed the 0.2s cooldown
    
    manager._execute_with_failover("prompt", 0.0, 10, "sys")
    assert mock_urlopen.call_count == 3
    # Last call should be back to OR since cooldown expired
    assert "openrouter" in mock_urlopen.call_args_list[2][0][0].full_url

@patch('urllib.request.urlopen')
def test_local_model_structured_output_validation(mock_urlopen, manager):
    """14. Local model structured-output validation (adapter logic)."""
    # Manager analyse() parses json from string. Local adapter extracts 'message.content'.
    mock_urlopen.side_effect = mock_urlopen_side_effect(
        build_http_error(401),
        build_http_error(401),
        build_http_error(401),
        build_mock_response(200, body={"message": {"content": '{"valid": "json"}'}})
    )
    res = manager.analyse("test")
    assert "valid" in res
