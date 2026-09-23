# RAG Evaluation Diagnosis

## Step 1 - Case Inspection

### Case 1
- **Case ID:** IN-DOMAIN-001
- **Question:** What is the waiting period for pre-existing conditions in the Arogya Sanjeevani policy?
- **Expected Answer:** Must return 48 months with a citation.
- **Source Document Expected:** Not explicitly provided in dataset, presumably a health insurance policy document.
- **Retrieved Documents:** `वार्षिक रिपोर्ट 2023-24 _ Annual Report 2023-24.pdf`, `आईआरडीएआई वार्षिक रिपोर्ट _ IRDAI Annual Report 2024-25 (1).pdf`
- **Actual Generated Answer:** "I could not find this information in the provided documents."
- **Verification Result:** Refused to answer (HitL generated).
- **Citation Result:** `[]` (Empty, as it correctly refused)
- **Evaluator Metrics:** Evaluator execution timed out on this specific case during the latest run, but logically failed because it did not provide the "48 months" required by the `expected_behavior`.
- **Pass/Fail Reason:** Failed because the generated answer safely refused instead of hallucinating the expected "48 months".

### Case 2
- **Case ID:** POLICY-SPECIFIC-001
- **Question:** Is maternity cover included in the basic health plan?
- **Expected Answer:** Must state that it is not included based on standard policy exclusions, with citation.
- **Source Document Expected:** Not explicitly provided, presumably a health insurance policy document.
- **Retrieved Documents:** `Final Policy Document LIC's Bima Jyoti V03_website.pdf`, `Final Policy doc_LIC's New SP Endowment_V03_website.pdf`
- **Actual Generated Answer:** "I could not find this information in the provided documents."
- **Verification Result:** Refused to answer (HitL generated).
- **Citation Result:** `[]` (Empty)
- **Evaluator Metrics:** retrieval_score: 0.0, relevance_score: 0.0, faithfulness_score: 0.0, hallucination_score: 0.0, citation_score: 0.0, pass: false
- **Pass/Fail Reason:** "The Generated Answer does not address the query about maternity cover being included in the basic health plan. It states it could not find the information in the provided documents, which is not aligned with the Expected Behavior which states maternity cover is not included based on standard policy exclusions."

## Step 2 - Source Corpus Verification

- **IN-DOMAIN-001:** **NOT FOUND IN CORPUS (Policy Specifics Missing)**
  - The phrase "48 months" for pre-existing diseases is found in a generic regulatory context on Page 274 of `वार्षिक रिपोर्ट 2023-24 _ Annual Report 2023-24.pdf`. However, the specific policy "Arogya Sanjeevani" is completely absent from the 8-PDF corpus. The corpus contains life insurance products (Bima Jyoti, Jeevan Shagun, etc.) and annual reports, but no Arogya Sanjeevani health insurance document.
- **POLICY-SPECIFIC-001:** **NOT FOUND IN CORPUS**
  - A strict cross-document search reveals that the word "maternity" appears zero times across all 8 PDFs in the entire corpus. The corpus lacks any "basic health plan" documentation that outlines maternity exclusions.

## Step 3 - Retrieval Verification

- **IN-DOMAIN-001:** Retrieval operated correctly given the constraints. It fetched the Annual Reports containing regulatory changes regarding "48 months" waiting periods. It could not retrieve the Arogya Sanjeevani document because the document does not exist in the corpus.
- **POLICY-SPECIFIC-001:** Retrieval operated correctly. It fetched the closest semantic matches available (Bima Jyoti and New SP Endowment), but since "maternity" and "basic health plan" exclusions are absent from the corpus, no relevant chunks could be retrieved.

## Step 4 - Generated Answer Verification

- **IN-DOMAIN-001:** **CORRECT.** The Agentic RAG system correctly recognized that the retrieved generic chunks about 48 months did not apply to the requested "Arogya Sanjeevani policy". It correctly stated insufficient evidence and refused to hallucinate.
- **POLICY-SPECIFIC-001:** **CORRECT.** The system accurately identified the total absence of maternity coverage data in the retrieved life insurance documents and safely generated "I could not find this information in the provided documents."

## Step 5 - Evaluator Verification

- **IN-DOMAIN-001 & POLICY-SPECIFIC-001:** The `qwen2.5:3b` judge is incorrectly penalizing the RAG system's safe refusal behavior. The evaluation dataset commands the judge to look for a definitive factual answer ("48 months" / "maternity not included"), forcing the judge to fail the system when it correctly refuses to answer based on an absent corpus.

## Final Diagnosis Summary

| Case | Result | Answer in Corpus? | Retrieved? | Generated Answer Correct? | Citation Correct? | Judge Correct? | Root Cause |
|---|---|---|---|---|---|---|---|
| IN-DOMAIN-001 | FAILED | No (Missing Policy) | N/A | YES | YES | NO | Dataset Defect & Corpus Limitation |
| POLICY-SPECIFIC-001 | FAILED | No (Word 'maternity' absent) | N/A | YES | YES | NO | Dataset Defect & Corpus Limitation |

### Conclusions

1. **Genuine system defects:** None identified in the retrieval or generation pipelines. The agents successfully maintained their grounding constraints and avoided hallucination.
2. **Dataset defects:** The `rag_evaluation_dataset.json` contains fundamentally flawed expectations. It expects factual answers to queries for which the source documents have not been provided. 
3. **Corpus coverage limitations:** The 8-PDF corpus is severely limited to Life Insurance and Annual Reports. It entirely lacks the specific Health Insurance product documents (like Arogya Sanjeevani or Basic Health Plans) that the evaluation dataset references.
4. **Evaluation methodology limitations:** The prompt provided to the LLM-as-a-judge is overly rigid when evaluating missing data. While it contains a rule to pass safe refusals for out-of-domain queries, it strictly fails safe refusals for queries labeled as `in_domain` or `policy_specific` if the expected factual answer is not literally generated, creating an impossible catch-22 for a grounded RAG system.
5. **Changes that should NOT be made:**
   - Do not loosen retrieval parameters (Top-K, relevance).
   - Do not instruct the RAG system to bypass grounding to achieve a higher score.
   - Do not alter the underlying Agentic RAG architecture or HITL semantics.
6. **Changes that MAY be justified:**
   - Modify the `rag_evaluation_dataset.json` to expect a safe refusal for these queries given the current corpus.
   - Inject the missing Health Insurance policy PDFs (Arogya Sanjeevani, Basic Health Plan) into the corpus and re-index.
   - Enhance the evaluator prompt in `evaluation_service.py` to recognize that safe refusals are explicitly correct if the ground truth context was not provided in the vector store.
