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

    def call_completions(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str, response_format: str = None) -> str:
        raise NotImplementedError

class OpenRouterProvider(BaseProviderAdapter):
    def call_completions(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str, response_format: str = None) -> str:
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
            print("OPENROUTER CALLING:", url)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                resp_body = response.read().decode("utf-8")
                print("OPENROUTER SUCCESS:", resp_body[:100])
                resp_json = json.loads(resp_body)
                if "choices" in resp_json and len(resp_json["choices"]) > 0:
                    return resp_json["choices"][0]["message"]["content"]
                else:
                    raise QueryProcessingException("Invalid response format from OpenRouter", step="api_call")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            print("OPENROUTER HTTP ERROR:", e.code, err_body)
            if e.code in (401, 403):
                raise QueryProcessingException(f"OpenRouter Authentication Error: {e.code}", step="api_call_auth")
            elif e.code == 402:
                raise QueryProcessingException(f"OpenRouter Insufficient Credits: {e.code}", step="api_call_payment")
            elif e.code == 404:
                raise QueryProcessingException("OpenRouter Model Not Found", step="api_call_not_found")
            elif e.code == 429:
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
    def call_completions(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str, response_format: str = None) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Phase2/1.0"
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
            err_body = e.read().decode("utf-8")
            print("GROQ HTTP ERROR:", e.code, err_body)
            if e.code in (401, 403):
                raise QueryProcessingException(f"Groq Authentication Error: {e.code}", step="api_call_auth")
            elif e.code == 402:
                raise QueryProcessingException(f"Groq Insufficient Credits: {e.code}", step="api_call_payment")
            elif e.code == 404:
                raise QueryProcessingException("Groq Model Not Found", step="api_call_not_found")
            elif e.code == 429:
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

class LocalLLMProvider(BaseProviderAdapter):
    def __init__(self, base_url: str, model: str, timeout: float):
        # Local LLM uses base_url instead of api_key
        super().__init__(api_key="", model=model, timeout=timeout)
        self.base_url = base_url

    def call_completions(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str, response_format: str = None) -> str:
        url = self.base_url
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        if response_format == "json":
            data["format"] = "json" # Force structured json for local models
        
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            print("LOCAL LLM CALLING:", url)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                resp_body = response.read().decode("utf-8")
                resp_json = json.loads(resp_body)
                if "message" in resp_json and "content" in resp_json["message"]:
                    return resp_json["message"]["content"]
                else:
                    raise QueryProcessingException("Invalid response format from Local LLM", step="api_call")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            print("LOCAL LLM HTTP ERROR:", e.code, err_body)
            if e.code == 404:
                raise QueryProcessingException("Local Model Not Found", step="api_call_not_found")
            elif e.code >= 500:
                raise QueryProcessingException(f"Local Server Error: {e.code}", step="api_call_5xx")
            raise QueryProcessingException(f"Local HTTP Error: {e.code}", step="api_call")
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise QueryProcessingException("Local LLM Timeout", step="api_call_timeout")
            raise QueryProcessingException(f"Local LLM Connection Error: {e.reason}", step="api_call_connection")
        except TimeoutError:
            raise QueryProcessingException("Local LLM Timeout", step="api_call_timeout")
        except Exception as e:
            logger.error(f"Local LLM call failed: {e}")
            raise QueryProcessingException(f"Local LLM execution failure: {e}", step="api_call")
