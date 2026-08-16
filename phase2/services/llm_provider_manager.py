import json
import logging
import re
import time
from typing import Dict, Any, Optional

from phase2.interfaces.query_agent_interface import ILLMAnalyzer
from phase2.exceptions.query_exception import QueryProcessingException
from phase2.config.settings import Phase2Settings
from phase2.services.llm_adapters import OpenRouterProvider, GroqProvider

logger = logging.getLogger(__name__)

def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
    """Provides resilient JSON parsing, successfully cleaning markdown artifacts."""
    clean = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean, flags=re.MULTILINE).strip()
    if clean.find('{') >= 0 and clean.rfind('}') > clean.find('{'):
        clean = clean[clean.find('{') : clean.rfind('}') + 1]
    
    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        raise QueryProcessingException("Failed to decode provider JSON constraint.", step="json_parse") from exc

class LLMProviderManager(ILLMAnalyzer):
    """
    Manages primary and secondary LLM providers, executing failover and retries.
    Optionally acts as the QueryAnalyzer if prompt_template is provided.
    """
    def __init__(self, settings: Phase2Settings, prompt_template: Optional[str] = None, supported_intents: Optional[list] = None):
        self.settings = settings
        self.prompt_template = prompt_template
        self.supported_intents = supported_intents
        
        self.primary_name = self.settings.llm.primary_provider.lower()
        self.secondary_name = self.settings.llm.secondary_provider.lower()
        
        self.providers = {}
        
        if self.settings.llm.openrouter_api_key:
            self.providers["openrouter"] = OpenRouterProvider(
                api_key=self.settings.llm.openrouter_api_key,
                model=self.settings.llm.openrouter_model,
                timeout=self.settings.llm.timeout_seconds
            )
        
        if self.settings.llm.groq_api_key:
            self.providers["groq"] = GroqProvider(
                api_key=self.settings.llm.groq_api_key,
                model=self.settings.llm.groq_model,
                timeout=self.settings.llm.timeout_seconds
            )

    def _execute_with_failover(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str) -> str:
        primary = self.providers.get(self.primary_name)
        secondary = self.providers.get(self.secondary_name)
        
        if not primary:
            if not secondary:
                raise QueryProcessingException("No providers configured properly.", step="api_call")
            primary = secondary
            secondary = None
            self.primary_name = self.secondary_name
        
        last_exception = None
        for attempt in range(self.settings.llm.max_retries):
            try:
                # Log provider attempt
                logger.debug(f"LLMProviderManager: Attempt {attempt+1} via {self.primary_name}")
                return primary.call_completions(prompt, temperature, max_tokens, system_instruction)
            except QueryProcessingException as e:
                last_exception = e
                # Failover immediately on 429, 5xx, timeout, or connection error if failover enabled
                if self.settings.llm.failover_enabled and e.context.get("step") in ["api_call_rate_limit", "api_call_5xx", "api_call_timeout", "api_call_connection"]:
                    logger.warning(f"Primary provider ({self.primary_name}) failed: {e}. Attempting failover...")
                    break
                else:
                    time.sleep(self.settings.llm.retry_backoff_seconds)
        
        if self.settings.llm.failover_enabled and secondary:
            logger.info(f"LLMProviderManager: Failing over to secondary provider ({self.secondary_name})")
            for attempt in range(self.settings.llm.max_retries):
                try:
                    return secondary.call_completions(prompt, temperature, max_tokens, system_instruction)
                except Exception as e:
                    last_exception = e
                    time.sleep(self.settings.llm.retry_backoff_seconds)
                    
        logger.error("LLMProviderManager: All providers failed.")
        if last_exception:
            raise last_exception
        raise QueryProcessingException("Providers exhausted", step="api_call")

    def analyse(self, normalized_query: str) -> Dict[str, Any]:
        if self.prompt_template and self.supported_intents:
            prompt = self.prompt_template.format(
                query=normalized_query,
                supported_intents=", ".join(self.supported_intents)
            )
        else:
            prompt = normalized_query
            
        sys_inst = "You are a specialized AI system. You MUST return ONLY valid raw JSON output targeting exactly the JSON layout specified in the user prompt. DO NOT use markdown code blocks like ```json."
        raw = self._execute_with_failover(prompt, temperature=0.0, max_tokens=self.settings.llm.max_output_tokens, system_instruction=sys_inst)
        return _parse_llm_json(raw)

    def analyse_text(self, fully_formatted_prompt: str) -> str:
        sys_inst = "You are a specialized AI Knowledge Assistant. You will synthesize the provided logical deduction into a highly structured, fully detailed, and rich conversational response. Use graceful Markdown structure (bullet points, bold text). Emulate GPT-4 / Gemini detailed formatting."
        raw = self._execute_with_failover(fully_formatted_prompt, temperature=self.settings.llm.temperature, max_tokens=2048, system_instruction=sys_inst)
        return raw
