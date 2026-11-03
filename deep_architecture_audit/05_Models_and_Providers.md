# PART 15 — LLM ARCHITECTURE
It is critical to distinguish between the Model, the Provider, and the Runtime.

| Model | Provider | Runtime | Purpose | Location |
|---|---|---|---|---|
| `qwen2.5:3b` | Local Machine | Ollama | The actual AI brain that reasons and generates text. | Your laptop/server |
| `qwen/qwen3.8-27b` | Groq | Groq Cloud API | A much smarter version of the brain running on high-speed hardware. | Cloud API |
| `openai/gpt-4o-mini`| OpenRouter | Cloud API | A fallback cloud model. | Cloud API |

**Cloud vs Local Inference:**
- **Local Inference (Ollama + Qwen 3B):** Slow (uses CPU/GPU). Completely private (no data leaves the laptop). Free.
- **Cloud Inference (Groq + Qwen 27B):** Extremely fast (uses Groq's custom LPUs). Smarter (27B parameters). Requires internet. Data leaves the network.

# PART 16 — MODEL COMPARISON
**Why Qwen 2.5 3B? (Local)**
- *Alternatives:* Llama 3.2 (3B), Mistral (7B).
- *Trade-off:* Mistral 7B is smarter but requires >8GB of VRAM, making it too slow or impossible to run on standard university laptops. Qwen 2.5 3B is highly optimized for instruction following and fits comfortably in 4GB of RAM. It was chosen because it represents the best balance of reasoning capability and hardware compatibility for this project's local constraints.

**Why Qwen 3.8 27B? (Cloud)**
- *Alternatives:* Llama 3.3 70B, GPT-4o.
- *Trade-off:* Llama 70B was removed from the user's specific Groq API tier (resulting in a 404 Model Not Found error). Qwen 27B was verified to be active, fast, and highly capable on the Groq tier available to the project.

# PART 17 — LLM PROVIDER FALLBACK
**Code Path:** `phase2/services/llm_provider_manager.py`
**Manager Class:** `LLMProviderManager`
**Logic:**
1. Manager receives a generation request.
2. It loops through the `provider_chain` list (OpenRouter -> Groq -> Local).
3. If Groq throws `urllib.error.HTTPError (e.g. 429 Rate Limit or 404 Not Found)`, the exception block catches it.
4. It calls `_set_provider_cooldown()` to temporarily ban Groq from the chain.
5. The `break` or `continue` logic moves to the next provider in the chain (Local Ollama).
6. Local Ollama processes the query.

**Crucial Distinction:** A 404/429 error from Groq is an *infrastructure* failure. It does NOT create a Human-in-the-Loop `ReviewTask`. It simply falls back silently. A `ReviewTask` is only created if the AI *successfully* answers, but the answer has low verification confidence (a *knowledge* failure).
