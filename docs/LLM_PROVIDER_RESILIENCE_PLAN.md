# LLM Provider Resilience Plan

## 1. Audit Findings

### Configuration & Key Management
- **OpenRouter:** Configured via `OpenRouterProvider`, uses `PHASE2__LLM__OPENROUTER_API_KEY` (mapped from `OPENROUTER_API_KEY`). Model is `PHASE2__LLM__OPENROUTER_MODEL`.
- **Groq:** Configured via `GroqProvider`, uses `PHASE2__LLM__GROQ_API_KEY` (mapped from `GROQ_API_KEY`). Model is `PHASE2__LLM__GROQ_MODEL`.
- **API Key Loading:** Passed to backend via Docker's `env_file: - .env` and parsed by Pydantic's `SettingsConfigDict(env_prefix="PHASE2__")`.
- **Model Configuration:** Configured in `LLMSettings` as `openrouter_model` and `groq_model`.

### Retry & Failover Logic
- **Current Behavior:** The `LLMProviderManager._execute_with_failover()` function attempts the primary provider up to `max_retries` times. If it exhausts retries or hits an immediate failover, it loops through the secondary provider up to `max_retries` times.
- **Error Classification:**
  - 401/403/404 are classified as `immediate_failover` (`api_call_auth`, `api_call_not_found`).
  - 429/5xx/Timeout/Connection are classified as `retryable_failover` (`api_call_rate_limit`, `api_call_5xx`, `api_call_timeout`, `api_call_connection`).
- **Provider Cooldown:** **Does not exist.** The system immediately hammers the primary provider on the next user request, even if it just received a 429 Rate Limit.

### Local LLM
- **Ollama Status:** Not present in the repository, Docker configuration, or Python environment. No local model runtime currently exists.
- **Hardware/Environment:** Running via Docker Compose on Windows host.
- **Structured JSON Requirement:** All Phase 2 agents (Query, Retrieval, Verification, Reasoning, Risk, Contradiction) use `LLMProviderManager.analyse()` which strictly expects raw JSON output formatted accurately. The local model must therefore be highly capable of adhering to system instructions and JSON formats.

## 2. Proposed Implementation

### 2.1 Groq Multi-Key Support & Configuration
Extend `LLMSettings` in `phase2/config/settings.py` to add:
- `groq_api_key_2` (and an equivalent `GROQ_API_KEY_2` mapping)
- `local_model` (e.g., `llama3.2:3b` or `qwen2.5:3b`)
- `local_llm_base_url` (e.g., `http://ollama:11434/api/chat`)
- `provider_cooldown_seconds` (default: 60)

### 2.2 Provider Cooldown State
Implement a thread-safe `_provider_health` dictionary inside `LLMProviderManager`.
- Track `status` (AVAILABLE, RATE_LIMITED) and `cooldown_until` (timestamp).
- If a provider hits 429, update its state and skip it on subsequent requests until the cooldown expires.

### 2.3 Local LLM Adapter
Create `LocalLLMProvider` in `phase2/services/llm_adapters.py`.
- It will make HTTP requests to the Ollama API.
- It will adhere to the identical `BaseProviderAdapter` contract (`call_completions`).
- If it returns malformed output, it will raise `QueryProcessingException` matching the cloud providers.

### 2.4 Failover Chain
Update `LLMProviderManager` to manage a list of providers instead of hardcoded primary/secondary variables.
- Chain: `OpenRouter` → `Groq Key 1` → `Groq Key 2` → `Local LLM`
- The manager will iterate over the chain, checking health state, executing the prompt, and handling retries before moving to the next provider.
- If all fail, it raises a controlled `QueryProcessingException("Providers exhausted")`, bubbling up as a 503 error, explicitly avoiding arbitrary human-in-the-loop task creation.

### 2.5 Docker Integration
Add an `ollama` service to `docker-compose.yml`.
- Connect it to the backend.
- Create an entrypoint script to automatically pull the chosen local model on startup.
- The backend API will be decoupled from Ollama so it boots successfully even if Ollama is still initializing or fails to start.

### 2.6 Local Model Selection
Proposing **`llama3.2:3b`**:
- 3-Billion parameter models are lightweight enough to run performantly on standard developer machines (CPU or decent laptop GPU).
- The Llama 3.2 family is exceptionally good at following structured JSON instructions, which is a mandatory requirement for the agents.

### 2.7 Observability & Testing
- Ensure safe logging of the provider used (e.g., `groq_key_1`, `groq_key_2`, `local_llm`), latency, and error reasons without exposing secrets.
- Add robust unit tests (mocking HTTP requests) in `phase2/tests/test_llm_resilience.py` to cover: provider order, cooldown tracking, 401/429/500/timeout behaviors, and structured local responses.

## 3. Verification Plan
- Implement changes.
- Ensure 0% drift on Phase 1 features.
- Execute unit and integration tests (`pytest`).
- Validate Docker build & compose functionality.
- Generate `docs/LLM_PROVIDER_RESILIENCE_VERIFICATION.md` with full details of test cases, latencies, and architectural confirmation.
