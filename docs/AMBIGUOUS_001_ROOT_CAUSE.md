# Execution Trace

1. **Query Input:** The user asks `"What about the accident?"`
2. **QueryProcessing:** The `QueryUnderstandingAgent` successfully analyzes the query and flags it as `ambiguous=True` (Type: `vague_term`) with an intent of `policy_information`. However, the orchestrator ignores this flag and continues execution.
3. **Retrieval:** The `RetrievalAgent` executes a hybrid search. Driven by keyword matching (BM25) on the word "accident", it retrieves chunks from `Annual Report 2023-24.pdf`.
4. **Verification:** The `VerificationAgent` (via `RelevanceChecker`) checks if the chunk's `combined_score >= 0.3`. Because the keyword match pushes the score above this low threshold, the chunk is blindly marked as `is_valid_for_reasoning = True` without any semantic verification of whether it actually answers the query.
5. **Reasoning:** The `ReasoningAgent` receives the valid but irrelevant chunk. Its strict prompt instructions mandate it to output "I could not find this information" if the evidence lacks information. However, because it sees a document about "accident insurance", it fails this boundary and outputs a weak, generic deduction (e.g., "The document mentions accident insurance").
6. **Response Generation:** The `ResponseBuilder` (specifically `ResponseFormatter`) takes the raw deduction and passes it to an LLM with the prompt: *"Convert the following logical deduction into a comprehensive... response. Expand upon the raw deduction by explaining the surrounding context..."*. This explicit instruction to "expand" triggers the LLM to use parametric memory, generating a 4-paragraph hallucination.
7. **Guardrails:** The `GuardrailService.check_output` evaluates the generated text. Since it lacks citations, the guardrail checks for unsupported claims. However, it only looks for hardcoded absolute phrases (e.g., "according to the policy", "guaranteed"). The hallucination evades this weak substring check and is passed to the user.

# Retrieved Evidence

The retrieval layer returned:
`[{"doc": "वार्षिक रिपोर्ट 2023-24 _ Annual Report 2023-24.pdf", "page": "None"}]`

A thorough scan of the corpus confirms that this document does **not** contain the specific numbers ("₹7,788 crore", "165.05 crore", "67% claim ratio") generated in the final response. The document was retrieved solely because it contains general references to "accident" insurance.

# Verification Result

The `VerificationAgent` completely failed to block the unsupported chunk. 

**Why:** The `RelevanceChecker` implementation operates as a purely statistical gatekeeper (`max(0.0, min(1.0, chunk.combined_score))`). It verifies evidence by checking if the retrieval rank score is `>= 0.3`. Since BM25 artificially inflated the score for the keyword "accident", the chunk sailed past the threshold. No LLM-based semantic QA validation was performed to verify if the chunk actually contained an answer to the specific query.

# First Unsupported Claim

The first unsupported factual content was introduced by the **ResponseFormatter** inside the `ResponseBuilder` agent. 

While the `ReasoningAgent` failed to strictly refuse the query, the 4-paragraph essay with fabricated metrics (e.g., "collected ₹7,788 crore in gross premiums") was generated because the `ResponseFormatter`'s prompt explicitly instructs the LLM to:
> *"Expand upon the raw deduction by explaining the surrounding context based on the provided sources and internal logic trace."*

This literal instruction to "expand" actively solicits parametric hallucination when the provided source text is sparse or irrelevant.

# Root Cause

The hallucination is a systemic failure spanning multiple architectural layers:

1. **Ignored Signals:** `is_ambiguous=True` is accurately detected but completely ignored by the orchestrator routing logic.
2. **Statistical vs. Semantic Verification:** `VerificationAgent` relies on a naive statistical threshold (`score >= 0.3`) rather than semantically verifying if the chunk answers the user's intent.
3. **Prompt Engineering Defect:** `ResponseFormatter` explicitly instructs the LLM to "expand upon" the raw deduction, forcing parametric generation of external facts.
4. **Weak Output Guardrails:** `GuardrailService` uses fragile, hardcoded substring matching (`"according to the policy"`, `"must be paid"`) to detect unsupported claims, allowing eloquent hallucinations to bypass security.

# Guardrail Failure Analysis

The `GuardrailService.check_output` method successfully detected that the response lacked citations (`has_citations = False`). However, its fallback validation logic is fundamentally flawed. It attempts to detect unsupported claims by checking if the answer contains specific absolute phrases:
```python
absolute_phrases = ["according to the policy", "the rules state", "must be paid", "guaranteed"]
if any(p in answer_lower for p in absolute_phrases):
    # Block output
```
Because the LLM generated a highly professional, conversational essay that did not happen to use these exact substrings, the guardrail incorrectly marked the 4-paragraph hallucination as safe.

# Recommended Fix

1. **Short-Circuit on Ambiguity:** Update `AgentOrchestrator` to immediately abort and prompt the user for clarification if `QueryContext.is_ambiguous` is True.
2. **Semantic Verification:** Upgrade `VerificationAgent` / `RelevanceChecker` to use a lightweight LLM call to semantically verify that the retrieved chunk actually contains an answer to the query, rather than relying solely on the hybrid retrieval score.
3. **Fix Prompt Engineering:** Remove the *"Expand upon the raw deduction by explaining the surrounding context"* instruction from `ResponseFormatter`. Enforce strict adherence to the raw deduction.
4. **Robust Guardrails:** Replace the hardcoded substring matching in `GuardrailService` with a semantic entailment model (NLI) that verifies if the generated text is fully supported by the citations.

# Regression Test 

```python
def test_ambiguous_query_is_rejected_early():
    # 1. Provide an ambiguous query
    query = "What about the accident?"
    
    # 2. Execute Orchestrator
    result = orchestrator.orchestrate(query)
    
    # 3. Assert query processing flagged it
    assert result.shared_context.ambiguity.is_ambiguous is True
    
    # 4. Assert early termination occurred (No retrieval/reasoning)
    assert "RetrievalAgent" not in result.execution_history
    
    # 5. Assert the final response is a polite request for clarification
    assert "Could you please clarify" in result.shared_context.final_response.direct_answer
    
def test_response_formatter_does_not_expand_parametrically():
    # 1. Mock a sparse reasoning deduction
    mock_deduction = "The document mentions accident insurance."
    
    # 2. Run ResponseFormatter
    formatted_answer = response_formatter.format_answer(
        reasoning_result=ReasoningResult(conclusion=mock_deduction), 
        citations=[]
    )
    
    # 3. Assert no parametric numbers/facts were introduced
    assert "7,788" not in formatted_answer
    assert len(formatted_answer) < len(mock_deduction) * 2 # Prevent massive expansion
```
