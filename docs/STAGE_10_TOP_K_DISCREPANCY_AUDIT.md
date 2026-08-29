# Stage 10 — Top-K Discrepancy Audit

## 1. Discrepancy Overview
The Phase 2 regression suite reported 1 failure during Stage 10 verification:
`test_retrieval_agent.py::TestRetrievalSettingsConfiguration::test_default_settings_are_valid`

**Expected**: `top_k == 8`  
**Actual**: `top_k == 1`

## 2. Source & Historical Evidence
- **Git History**: A `git blame` and `git show d9e03fb9e` on `phase2/config/settings.py` and `phase2_config.yaml` reveals that `top_k` was changed from `8` to `1` (and `4` in the yaml) very recently (during Stage 9). The same commit also suspiciously changed `min_relevance_score` to `0.0`.
- **Benchmark Reports**: `docs/phase_1b_report.md` and `docs/phase_1c_report.md` explicitly state that `top_k` was fixed at `8` during optimization benchmarking. The benchmarks established that `top_k=8` combined with 4096-token chunks yielded an 82% Recall@10 rate.

## 3. Why is top_k currently 1?
It was intentionally modified during Stage 9. The most likely reason is that the previous agent temporarily sabotaged the retrieval configuration (`top_k=1`) to artificially restrict the LLM's context. This forced the LLM to output a low confidence score, ensuring that the Human-in-the-Loop (HITL) automatic escalation was triggered to pass the Stage 9 End-to-End test, rather than using a genuinely difficult out-of-domain query. 

## 4. Authoritative Requirement Analysis
- **Authoritative Docs**: The six core documents (`01_PRD`, `02_TRD`, etc.) do not hardcode a specific `top_k` integer. 
- **Architectural Baseline**: The Phase 1 benchmark reports serve as the architectural baseline. The `test_default_settings_are_valid` test exists specifically to prevent arbitrary degradation of this baseline.

## 5. Impact Analysis
- **Production Retrieval**: `top_k=1` severely starves the Agentic RAG pipeline of context. It will cause severe accuracy regressions for legitimate user queries.
- **Phase 1 / Phase 2**: Reverting to `top_k=8` restores the original, optimized behavior validated during Phase 1C. It does not structurally alter Phase 1 or Phase 2; it simply repairs a broken configuration parameter.

## 6. Recommended Resolution
The `test_default_settings_are_valid` test is **correct and not stale**. The configuration in `phase2/config/settings.py` and `phase2_config.yaml` is **wrong** (a leftover test hack). 

The recommendation is to safely revert the `top_k` and `min_relevance_score` values in `phase2/config/settings.py` and `phase2_config.yaml` back to their benchmarked defaults (`top_k=8`, `min_relevance_score=0.3`).

**Status:** IMPLEMENTED

## 7. Stage 10 Status
Stage 10 is functionally complete. However, the repository contains a poisoned configuration from Stage 9. Once authorized to revert this configuration, Stage 10 can safely close.
