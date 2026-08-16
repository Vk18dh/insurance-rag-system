import json
import logging
import urllib.request
import urllib.error
from phase2.exceptions.query_exception import QueryProcessingException

logger = logging.getLogger(__name__)

class BaseProviderAdapter:
    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def call_completions(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str) -> str:
        raise NotImplementedError

class OpenRouterProvider(BaseProviderAdapter):
    def call_completions(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000/",
            "X-Title": "Phase2 AI RAG"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                resp_body = response.read().decode("utf-8")
                resp_json = json.loads(resp_body)
                if "choices" in resp_json and len(resp_json["choices"]) > 0:
                    return resp_json["choices"][0]["message"]["content"]
                else:
                    raise QueryProcessingException("Invalid response format from OpenRouter", step="api_call")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise QueryProcessingException("OpenRouter Rate Limit Exceeded", step="api_call_rate_limit")
            elif e.code >= 500:
                raise QueryProcessingException(f"OpenRouter Server Error: {e.code}", step="api_call_5xx")
            raise QueryProcessingException(f"OpenRouter HTTP Error: {e.code}", step="api_call")
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise QueryProcessingException("OpenRouter Timeout", step="api_call_timeout")
            raise QueryProcessingException(f"OpenRouter Connection Error: {e.reason}", step="api_call_connection")
        except TimeoutError:
            raise QueryProcessingException("OpenRouter Timeout", step="api_call_timeout")
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise QueryProcessingException(f"OpenRouter API execution failure: {e}", step="api_call")

class GroqProvider(BaseProviderAdapter):
    def call_completions(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                resp_body = response.read().decode("utf-8")
                resp_json = json.loads(resp_body)
                if "choices" in resp_json and len(resp_json["choices"]) > 0:
                    return resp_json["choices"][0]["message"]["content"]
                else:
                    raise QueryProcessingException("Invalid response format from Groq", step="api_call")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise QueryProcessingException("Groq Rate Limit Exceeded", step="api_call_rate_limit")
            elif e.code >= 500:
                raise QueryProcessingException(f"Groq Server Error: {e.code}", step="api_call_5xx")
            raise QueryProcessingException(f"Groq HTTP Error: {e.code}", step="api_call")
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise QueryProcessingException("Groq Timeout", step="api_call_timeout")
            raise QueryProcessingException(f"Groq Connection Error: {e.reason}", step="api_call_connection")
        except TimeoutError:
            raise QueryProcessingException("Groq Timeout", step="api_call_timeout")
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise QueryProcessingException(f"Groq API execution failure: {e}", step="api_call")
