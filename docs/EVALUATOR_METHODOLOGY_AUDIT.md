# Evaluator Methodology Audit

## 1. Executive Finding
The current evaluation methodology is fundamentally flawed when handling unsupported questions that masquerade as "in-domain" queries. The LLM-as-a-judge (`qwen2.5:3b`) blindly assumes that the dataset's `Expected Behavior` is the absolute ground truth. Because it lacks awareness of the full corpus's contents, it penalizes the RAG system for executing a correct, grounded safe refusal whenever the dataset demands a factual answer that is absent from the indexed documents. The system is incorrectly being measured on string-agreement with the dataset rather than its adherence to safe RAG grounding principles.

## 2. Evaluation Pipeline
The evaluation pipeline flows as follows:
1. `evaluation_service.py` loads the query and `expected_behavior` from `rag_evaluation_dataset.json`.
2. The orchestrator executes the query against the vector store.
3. If the required information is missing from the corpus, the orchestrator retrieves either irrelevant chunks or nothing, and safely generates: "I could not find this information in the provided documents."
4. The service sends the Query, Expected Behavior, Generated Answer, Retrieved Sources, and Confidence to the local `qwen2.5:3b` judge.
5. The judge evaluates whether the `Generated Answer` fulfills the `Expected Behavior`.
6. If they do not align, the judge outputs `"pass": false` and assigns `0.0` to retrieval, relevance, and citation metrics, failing the case and tanking the overall score.

## 3. IN-DOMAIN-001 Trace
- **Dataset Entry:** `IN-DOMAIN-001` (Arogya Sanjeevani pre-existing conditions waiting period).
- **Expected Behavior:** "Must return 48 months with a citation."
- **Corpus Availability:** The specific policy (Arogya Sanjeevani) is entirely absent from the corpus.
- **Generated Answer:** "I could not find this information in the provided documents."
- **Judge Decision:** Evaluator execution timed out in the most recent run, but logically fails because the safe refusal directly contradicts the `Expected Behavior` constraint requiring "48 months". 
- **Why it fails:** The evaluator does not know the corpus lacks this policy. It only sees that the RAG system failed to provide "48 months" as commanded by the dataset.

## 4. POLICY-SPECIFIC-001 Trace
- **Dataset Entry:** `POLICY-SPECIFIC-001` (Maternity cover in basic health plan).
- **Expected Behavior:** "Must state that it is not included based on standard policy exclusions, with citation."
- **Corpus Availability:** The word "maternity" appears zero times in the 8-PDF corpus; no basic health plan document is present.
- **Generated Answer:** "I could not find this information in the provided documents."
- **Retrieval Metrics:** Evaluated as `0.0` (Failed to retrieve missing evidence).
- **Citation Metrics:** Evaluated as `0.0` (No citations provided for refusal).
- **Judge Decision:** `pass: false`.
- **Pass/Fail Reason:** The judge explicitly reasons: *"The Generated Answer does not address the query about maternity cover... which is not aligned with the Expected Behavior which states maternity cover is not included..."*

## 5. Safe Refusal Handling
The evaluator correctly handles safe refusals **only** when the `Expected Behavior` explicitly permits them (e.g., in `OOD-001` and `AMBIGUOUS-001`). For queries classified as `in_domain` or `policy_specific`, the dataset demands a factual answer. Consequently, the evaluator incorrectly treats a grounded, safe refusal as a hallucination or failure to answer, heavily penalizing the RAG system for obeying its safety constraints.

## 6. Corpus Availability Awareness
**Does the evaluator know whether the expected factual answer is actually present in the indexed corpus?**
No. The evaluator is "blind" to the underlying corpus. It receives only the *retrieved* chunks. When those chunks are irrelevant or empty, the evaluator cannot distinguish between a *retrieval failure* (the answer exists but wasn't found) and a *corpus limitation* (the answer simply doesn't exist). It assumes the dataset's `Expected Behavior` proves the answer must exist.

## 7. Judge Prompt Analysis
**Does the judge prompt contain contradictory instructions?**
Yes. 
- Rule 1 states: *If the Expected Behavior states the system must block, refuse... you MUST set "pass": true.*
- Rule 3 states: *If the Generated Answer correctly aligns with the Expected Behavior... you MUST set "pass": true.*

This creates a contradiction: The RAG system is instructed not to hallucinate unretrieved facts. However, for `IN-DOMAIN-001`, the `Expected Behavior` demands a fact ("48 months"). Because the RAG system refuses to hallucinate, it violates Rule 3 of the judge prompt, forcing a failure.

## 8. Metric Analysis
**Are the current metrics mathematically/semantically appropriate for corpus-missing cases?**
No. 
- **Retrieval Score = 0.0**: Treats returning zero irrelevant chunks as a failure, when it is the correct semantic behavior for absent data.
- **Citation Score = 0.0**: Penalizes the system for not citing sources in a safe refusal.
- **Faithfulness Score = 0.0**: Incorrectly assumes a safe refusal is unfaithful. A grounded safe refusal is actually 100% faithful to the missing context.
These 0.0 scores completely tank the `overall_score` average.

## 9. Genuine Failure Detection
**Would changing the evaluator risk hiding genuine retrieval or hallucination failures?**
Yes. If we instruct the judge to *always* pass a safe refusal, we create a massive blind spot. If a document *is* in the corpus but the retrieval engine fails to find it (a genuine retrieval failure), the RAG system will safely refuse. If the evaluator blindly passes all safe refusals, this critical retrieval failure will be reported as a `PASS`, hiding a severe system defect.

## 10. Required Changes
To achieve a highly accurate evaluation methodology:
1. **Dataset Alignment:** The `Expected Behavior` in the dataset must accurately reflect the contents of the *actual* corpus. If the corpus lacks "Arogya Sanjeevani", the `Expected Behavior` must be updated to expect a safe refusal.
2. **Metric Redefinition:** The scoring math in `evaluation_service.py` must treat `citation_score` and `retrieval_score` as `N/A` (omitted from the average) when a safe refusal is the *correct* expected behavior.
3. **Corpus Expansion:** Alternatively, upload the missing Health Insurance policy PDFs to the corpus so that the factual `Expected Behavior` can be met.

## 11. Changes That Must NOT Be Made
- **Do not relax grounding constraints:** Do not prompt the RAG agents to rely on parametric memory to bypass the corpus limitation and pass the test.
- **Do not blindly pass all refusals:** Do not alter the judge prompt to automatically approve all safe refusals, as this will mask genuine retrieval failures.
- **Do not alter timeouts or retrieval logic (Top-K=8):** The underlying RAG architecture is operating correctly.

## 12. Recommended Evaluation Model
For future evaluation scaling, consider upgrading the judge model from a localized 3B parameter model to a larger frontier model (e.g., Llama-3-70B, GPT-4o, or Gemini 1.5 Pro) if computation allows, as higher-parameter judges demonstrate better semantic reasoning when differentiating between justified safe refusals and retrieval failures (provided the dataset is corrected).

| Scenario | Corpus Evidence | System Behavior | Correct Evaluation |
|---|---|---|---|
| Supported question + correct grounded answer | Present | Answers with citation | PASS |
| Supported question + wrong answer | Present | Incorrect answer | FAIL |
| Supported question + unjustified refusal | Present | Refuses | FAIL |
| Unsupported question + safe refusal | Absent | Refuses | PASS |
| Unsupported question + hallucinated answer | Absent | Answers anyway | FAIL |
| Unsupported question + invented citation | Absent | Answers with citation | FAIL |
