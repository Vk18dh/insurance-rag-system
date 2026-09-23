# Timeout Configuration Verification Report

## 1. Root Cause
The `Execution bound forcefully terminated securely after 90000.0ms` error was caused by a configuration wiring bug in `backend/app/dependencies/agents.py`. The dependency injector was incorrectly passing the global workflow timeout (`settings.orchestrator.max_workflow_timeout_ms` = 90000.0) into the `ExecutionManager.timeout_ms` field. Since `ExecutionManager` enforces timeouts on *individual agents*, this effectively gave each agent a 90-second timeout. When the Reasoning Agent ran on local CPU with a heavy context, it exceeded 90 seconds, triggering this individual agent timeout. Additionally, the global workflow timeout was fundamentally not enforced at the orchestrator level.

## 2. Exact Code Change
**1. Dependency Injection Fix (`backend/app/dependencies/agents.py`)**
- Corrected the `ExecutionManager` initialization to use `settings.orchestrator.agent_timeout_ms` (30 seconds).
- Passed the `max_workflow_timeout_ms` (90 seconds) directly into the `AgentOrchestrator` constructor.

**2. Workflow Timeout Enforcement (`phase2/orchestrator/orchestrator.py`)**
- Added `_workflow_timeout_ms` to `AgentOrchestrator.__init__`.
- Captured `_workflow_start_ms` before the sequential loop.
- Added a conditional check at the end of each agent's execution to verify if `elapsed_time > _workflow_timeout_ms`. If exceeded, the workflow forcibly breaks the sequence with a `ExecutionStatus.FAILURE`.

**3. HITL Classification Fix (`backend/app/routers/query.py`)**
- Added `"Execution bound forcefully"` to the catastrophic provider failure keyword check. This ensures a raw timeout raises a clean `503 Service Unavailable` instead of silently triggering an unwarranted `ReviewTask` due to a forced `is_safe=False` state.

## 3. Individual Agent Timeout Behavior
Individual agents are wrapped via `TimeoutManager` (using `ThreadPoolExecutor`). With the fix applied, any agent (e.g. `ReasoningAgent`) taking longer than 30 seconds will be securely terminated, raising a `TimeoutException`. 

## 4. Global Workflow Timeout Behavior
The global workflow timeout acts as a cumulative guard. After an individual agent finishes (either successfully or by throwing an exception), the orchestrator calculates the total time since the workflow began. If the total time exceeds 90 seconds, the orchestrator immediately halts execution, logs a fatal error, and aborts before launching the next agent.

## 5. Test Results
- **Phase 2 Test Suite**: Ran successfully (227 passing tests), including 3 new deterministic tests specifically verifying the timeout boundary logic.
- **Backend Test Suite**: Ran successfully (40 passing tests) with `PYTHONPATH="."`.

## 6. Ollama Controlled E2E Result
A controlled E2E Python script was executed locally targeting the orchestrator directly to isolate authentication/networking noise. 
- **Execution Time**: The script terminated in `34.14s`.
- **Agent Timeout**: The orchestrator printed `Execution exceeded timeout limit natively: 30.0s`. 
- **Result Status**: `ExecutionStatus.FAILURE`
- **Verification**: The `agent_timeout_ms` threshold (30 seconds) was successfully applied and accurately terminated an agent (in this case, the `RetrievalAgent` hanging on local model weight loading) well before the 90-second global workflow threshold was reached.

## 7. HITL/ReviewTask Behavior
A pure infrastructure timeout no longer creates a false "low confidence" ReviewTask. By adding the timeout signature to the REST router's catastrophic failure list, the FastAPI layer explicitly responds with `503 LLM Provider Service Unavailable or Timed Out`. This preserves strict HITL semantics where human reviews are reserved for genuine, domain-level uncertainty or boundary violations.

## 8. Remaining Performance Limitation
While the configuration is now strictly correct, the fundamental underlying bottleneck remains: the sequential 6-agent LLM pipeline running entirely on local CPU inference takes approximately 90–150 seconds to complete. Because we enforce a strict 30-second individual agent timeout and a 90-second global timeout, **the pipeline is guaranteed to fail under local CPU conditions** when processing heavy retrieval contexts.

## 9. Recommended Next Step
Do not increase timeouts or redesign the Agentic RAG architecture. Instead, address provider availability:
1. Restore OpenRouter API credits.
2. Rotate Groq keys to resolve the `429 Rate Limit Exceeded` error.
3. Test E2E again on cloud inference, which is well within the 30s/90s operational limits.
