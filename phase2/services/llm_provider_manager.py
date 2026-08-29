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
    print("RAW TEXT FOR JSON PARSING:", repr(raw_text))
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
    Manages a chain of LLM providers with automatic failover and cooldown tracking.
    Order: OpenRouter -> Groq Key 1 -> Groq Key 2 -> Local LLM
    """
    
    # Thread-safe class-level state for cooldowns across all manager instances
    _provider_health: Dict[str, Dict[str, Any]] = {}

    def __init__(self, settings: Phase2Settings, prompt_template: Optional[str] = None, supported_intents: Optional[list] = None):
        self.settings = settings
        self.prompt_template = prompt_template
        self.supported_intents = supported_intents
        
        # Build the provider chain explicitly
        self.provider_chain = []
        
        if self.settings.llm.openrouter_api_key:
            self.provider_chain.append({
                "id": "openrouter",
                "instance": OpenRouterProvider(
                    api_key=self.settings.llm.openrouter_api_key,
                    model=self.settings.llm.openrouter_model,
                    timeout=self.settings.llm.timeout_seconds
                )
            })
            
        if self.settings.llm.groq_api_key:
            self.provider_chain.append({
                "id": "groq_key_1",
                "instance": GroqProvider(
                    api_key=self.settings.llm.groq_api_key,
                    model=self.settings.llm.groq_model,
                    timeout=self.settings.llm.timeout_seconds
                )
            })
            
        if self.settings.llm.groq_api_key_2:
            self.provider_chain.append({
                "id": "groq_key_2",
                "instance": GroqProvider(
                    api_key=self.settings.llm.groq_api_key_2,
                    model=self.settings.llm.groq_model,
                    timeout=self.settings.llm.timeout_seconds
                )
            })
            
        if self.settings.llm.local_llm_base_url:
            from phase2.services.llm_adapters import LocalLLMProvider
            self.provider_chain.append({
                "id": "local",
                "instance": LocalLLMProvider(
                    base_url=self.settings.llm.local_llm_base_url,
                    model=self.settings.llm.local_model,
                    timeout=self.settings.llm.timeout_seconds
                )
            })
            
        # Backward compatibility for existing tests
        self.providers = {p["id"]: p["instance"] for p in self.provider_chain}
        # Also alias for tests expecting "groq" instead of "groq_key_1"
        if "groq_key_1" in self.providers:
            self.providers["groq"] = self.providers["groq_key_1"]

    def _is_provider_available(self, provider_id: str) -> bool:
        health = self.__class__._provider_health.get(provider_id, {"status": "available", "cooldown_until": 0.0})
        if health["status"] == "cooldown":
            if time.time() > health["cooldown_until"]:
                self.__class__._provider_health[provider_id] = {"status": "available", "cooldown_until": 0.0}
                return True
            return False
        return True

    def _set_provider_cooldown(self, provider_id: str):
        cooldown_duration = self.settings.llm.provider_cooldown_seconds
        self.__class__._provider_health[provider_id] = {
            "status": "cooldown",
            "cooldown_until": time.time() + cooldown_duration
        }
        logger.warning(f"Provider {provider_id} placed into cooldown for {cooldown_duration} seconds.")

    def _execute_with_failover(self, prompt: str, temperature: float, max_tokens: int, system_instruction: str, response_format: str = None) -> str:
        if not self.provider_chain:
            raise QueryProcessingException("No providers configured properly.", step="api_call")
        
        # 401/403/404/402 -> skip provider
        skip_errors = ["api_call_auth", "api_call_not_found", "api_call_payment"]
        # 429 -> cooldown provider, then skip
        cooldown_errors = ["api_call_rate_limit"]
        # 5xx/Timeout/Connection -> retry, then skip
        retryable_errors = ["api_call_5xx", "api_call_timeout", "api_call_connection"]

        last_exception = None

        for p in self.provider_chain:
            provider_id = p["id"]
            provider_instance = p["instance"]
            
            if not self._is_provider_available(provider_id):
                logger.info(f"Skipping provider {provider_id} (in cooldown)")
                continue
                
            for attempt in range(self.settings.llm.max_retries):
                try:
                    logger.debug(f"LLMProviderManager: Attempt {attempt+1} via {provider_id}")
                    return provider_instance.call_completions(prompt, temperature, max_tokens, system_instruction, response_format)
                except QueryProcessingException as e:
                    last_exception = e
                    step = e.context.get("step")
                    
                    if not self.settings.llm.failover_enabled:
                        if attempt < self.settings.llm.max_retries - 1:
                            time.sleep(self.settings.llm.retry_backoff_seconds)
                            continue
                        else:
                            break
                            
                    if step in skip_errors:
                        logger.warning(f"Provider {provider_id} unavailable ({step}): {e}. Skipping to next provider.")
                        break # move to next provider
                    elif step in cooldown_errors:
                        logger.warning(f"Provider {provider_id} rate limited: {e}. Applying cooldown.")
                        self._set_provider_cooldown(provider_id)
                        break # move to next provider
                    elif step in retryable_errors:
                        if attempt == self.settings.llm.max_retries - 1:
                            logger.warning(f"Provider {provider_id} retries exhausted: {e}. Skipping to next provider.")
                            break # move to next provider
                        time.sleep(self.settings.llm.retry_backoff_seconds)
                    else:
                        if attempt == self.settings.llm.max_retries - 1:
                            break
                        time.sleep(self.settings.llm.retry_backoff_seconds)
                except Exception as e:
                    last_exception = e
                    if attempt == self.settings.llm.max_retries - 1:
                        break
                    time.sleep(self.settings.llm.retry_backoff_seconds)
                    
        # Exits loop only if all available providers in the chain failed
        logger.error("LLMProviderManager: All providers failed or exhausted.")
        if last_exception:
            raise QueryProcessingException("Providers exhausted", step="api_call_exhausted") from last_exception
        raise QueryProcessingException("Providers exhausted", step="api_call_exhausted")

    def analyse(self, normalized_query: str) -> Dict[str, Any]:
        if self.prompt_template and self.supported_intents:
            prompt = self.prompt_template.format(
                query=normalized_query,
                supported_intents=", ".join(self.supported_intents)
            )
        else:
            prompt = normalized_query
            
        sys_inst = "You are a specialized AI system. You MUST return ONLY valid raw JSON output targeting exactly the JSON layout specified in the user prompt. DO NOT use markdown code blocks like ```json."
        raw = self._execute_with_failover(prompt, temperature=0.0, max_tokens=self.settings.llm.max_output_tokens, system_instruction=sys_inst, response_format="json")
        return _parse_llm_json(raw)

    def analyse_text(self, fully_formatted_prompt: str) -> str:
        sys_inst = "You are a specialized AI Knowledge Assistant. You will synthesize the provided logical deduction into a highly structured, fully detailed, and rich conversational response. Use graceful Markdown structure (bullet points, bold text). Emulate GPT-4 / Gemini detailed formatting."
        raw = self._execute_with_failover(fully_formatted_prompt, temperature=self.settings.llm.temperature, max_tokens=2048, system_instruction=sys_inst, response_format="text")
        return raw
