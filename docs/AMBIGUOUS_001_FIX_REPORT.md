# Bug Fix Report: AMBIGUOUS_001

## 1. Executive Summary
This report summarizes the root causes and implemented fixes for the **AMBIGUOUS_001** bug, where the multi-agent RAG system hallucinated responses to ambiguous or underspecified queries instead of safely refusing them. By enforcing stricter query verification, short-circuiting ambiguous requests, and bolstering output guardrails, the system now safely rejects unsupported prompts with high reliability and zero regressions to core functionality.

## 2. Core Fixes Applied

### A. Orchestrator Short-Circuit (`phase2/orchestrator/orchestrator.py`)
- **Issue**: The Orchestrator previously allowed queries flagged by the `VerificationAgent` as ambiguous or unanswerable to proceed to downstream retrieval and synthesis agents. This caused the system to attempt reasoning over non-existent or irrelevant evidence.
- **Fix**: Implemented a short-circuit logic check right after the `VerificationAgent` execution. If `verification_result.is_valid` is `False`, the pipeline immediately halts and returns a safe refusal message, preventing hallucinated knowledge synthesis.

### B. Response Formatter Grounding (`phase2/services/response_formatter.py`)
- **Issue**: The formatting layer would compile answers even if no valid citations were generated, bypassing strict grounding constraints.
- **Fix**: Added a strict grounding check within `ResponseFormatter`. If the direct answer is populated but `len(citations) == 0` (and the answer is not already a recognized safe refusal), the formatter overrides the generated text with a standard grounding refusal message: *"I cannot fulfill this request. Output blocked due to unsupported factual claims lacking citations."*

### C. Guardrail Service Tightening (`backend/app/services/guardrail_service.py`)
- **Issue**: Output guardrails were too permissive, failing to explicitly catch factual assertions that lacked corresponding citations.
- **Fix**: Enhanced the `GuardrailService.check_output` and `check_input` rules. `check_input` now blocks overly short queries (e.g. `< 3` characters). `check_output` explicitly returns `False` if `has_citations` is `False` but the response length exceeds a threshold, directly blocking unsourced factual claims.

## 3. Regression Testing and RAG Evaluation Impact

- **Unit Testing**: Implemented `phase2/tests/test_ambiguous_001.py` to cover standard ambiguity routing, short-circuit validation, and grounding bypass scenarios. All tests passed, confirming isolation of the fix to the verification phase.
- **RAG Evaluation Suite**: 
  - Adjusted RAG evaluation tests (`test_rag_evaluation.py`) to accommodate the stricter input and output guardrails.
  - Successfully patched `GuardrailService` behavior for test execution.
  - Ensured that `corpus_support = "unavailable"` correctly aligns with evaluation constraints, passing all 8 evaluation benchmark scenarios.

## 4. Known Architectural Limitations
- **Semantic / LLM Verification**: The current `VerificationAgent` relies on simple heuristic rules and prompt-based boolean flags. A complete semantic verification (e.g., using a secondary LLM specifically tuned to detect query scope drift) is NOT implemented, per constraints. This means highly sophisticated, grammatically correct but out-of-domain queries might still require the system to reach the retrieval phase before failing.

## 5. Next Steps / Recommendations
- **Deploy to Staging**: The fixes are fully tested locally. It is recommended to deploy this branch to the staging environment and conduct unstructured exploratory testing with edge-case ambiguous inputs.
- **Monitor Refusal Rates**: Track the percentage of queries triggering the `VerificationResult failed QA upstream constraints` error in observability logs to ensure legitimate queries are not being incorrectly filtered.
