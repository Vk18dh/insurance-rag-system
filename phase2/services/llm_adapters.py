"""
phase2.services.llm_adapters
============================

Contains adapter interfaces allowing Phase 1 and 2 to communicate with OpenRouter dynamically without needing extensive third-party SDK dependencies.
"""

import json
import logging
import urllib.request
import urllib.error
import re
from typing import Dict, Any

from phase2.interfaces.query_agent_interface import ILLMAnalyzer
from phase2.exceptions.query_exception import QueryProcessingException

logger = logging.getLogger(__name__)


def _call_openrouter(api_key: str, model: str, prompt: str, temperature: float, max_tokens: int, system_instruction: str = "You are a specialized AI system. You MUST return ONLY valid raw JSON output targeting exactly the JSON layout specified in the user prompt. DO NOT use markdown code blocks like ```json.") -> str:
    """Invokes OpenRouter chat completions via python's native urllib."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000/",
        "X-Title": "Phase2 AI RAG"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=45.0) as response:
            resp_body = response.read().decode("utf-8")
            resp_json = json.loads(resp_body)
            # Extract content directly
            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                return resp_json["choices"][0]["message"]["content"]
            else:
                raise QueryProcessingException("Invalid response format from OpenRouter", step="api_call")
    except Exception as e:
        logger.error(f"OpenRouter API call failed natively: {e}")
        raise QueryProcessingException(f"OpenRouter API execution failure: {e}", step="api_call")


def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Provides resilient JSON parsing, successfully cleaning markdown artifacts."""
    clean = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE).strip()
    # Handle possible leading trailing prefixes LLMs love to output
    if clean.find('{') >= 0 and clean.rfind('}') > clean.find('{'):
        clean = clean[clean.find('{') : clean.rfind('}') + 1]
    
    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise QueryProcessingException("Failed to natively decode OpenRouter JSON constraint.", step="json_parse") from exc


class OpenRouterQueryAnalyzer(ILLMAnalyzer):
    """
    OpenRouter Engine explicitly mapping queries toward the QueryUnderstanding Prompt.
    Used exclusively by the Front-End Query Understanding Agent.
    """
    def __init__(self, api_key: str, model_name: str, prompt_template: str, supported_intents: list):
        self.api_key = api_key
        self.model = model_name
        self.prompt_template = prompt_template
        self.supported_intents = supported_intents

    def analyse(self, normalized_query: str) -> Dict[str, Any]:
        prompt = self.prompt_template.format(
            query=normalized_query,
            supported_intents=", ".join(self.supported_intents)
        )
        raw = _call_openrouter(self.api_key, self.model, prompt, temperature=0.0, max_tokens=1024)
        return _parse_llm_json(raw)


class GenericOpenRouterExecutor(ILLMAnalyzer):
    """
    Universal OpenRouter Executor intended for downstream multi-agent executions.
    Bypasses wrapping templates entirely, serving raw fully-formatted payload mapping natively.
    """
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model = model_name

    def analyse(self, fully_formatted_prompt: str) -> Dict[str, Any]:
        raw = _call_openrouter(self.api_key, self.model, fully_formatted_prompt, temperature=0.0, max_tokens=1500)
        return _parse_llm_json(raw)

    def analyse_text(self, fully_formatted_prompt: str) -> str:
        sys_inst = "You are a specialized AI Knowledge Assistant. You will synthesize the provided logical deduction into a highly structured, fully detailed, and rich conversational response. Use graceful Markdown structure (bullet points, bold text). Emulate GPT-4 / Gemini detailed formatting."
        raw = _call_openrouter(self.api_key, self.model, fully_formatted_prompt, temperature=0.3, max_tokens=2048, system_instruction=sys_inst)
        return raw
