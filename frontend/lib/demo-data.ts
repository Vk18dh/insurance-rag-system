import type { QueryResponse } from "@/lib/types"

/**
 * Deterministic-ish demo response used when the live FastAPI backend is
 * unreachable, so the interface stays fully explorable in previews.
 */
export function buildDemoResponse(query: string): QueryResponse {
  const q = query.trim().toLowerCase()
  const isWaiting = q.includes("wait")
  const isSafe = !q.includes("cancel") && !q.includes("fraud") && !q.includes("deny")

  const answer = isWaiting
    ? `Based on the reviewed policy documents, the **standard waiting period for basic health insurance is 30 days** from the policy effective date.\n\nKey points:\n\n- **General illnesses:** A 30-day initial waiting period applies before most claims can be filed.\n- **Pre-existing conditions:** Coverage begins after a **36-month** continuous coverage period.\n- **Accidental injury:** The waiting period is **waived** for hospitalization arising from an accident.\n\n> Insurers may not impose a waiting period longer than statutory limits defined by the regional regulator.`
    : `Here is a grounded summary based on the retrieved policy sections relevant to your query:\n\n1. **Scope** — The clause applies to all active policyholders under the standard tier.\n2. **Conditions** — Eligibility is subject to continuous premium payment and disclosure requirements.\n3. **Exclusions** — Claims arising from undisclosed material facts may be contested.\n\nAll figures above are cited directly from the source documents listed below.`

  return {
    query_id: crypto.randomUUID(),
    final_answer: answer,
    confidence_score: isWaiting ? 0.95 : 0.82,
    is_safe: isSafe,
    sources: [
      {
        document: "FS-CAN1282_NND",
        page: 12,
        content_snippet:
          "A waiting period of thirty (30) days shall apply from the effective date of the policy, during which no benefits are payable except in the event of accidental bodily injury requiring hospitalization.",
        confidence: 1.0,
      },
      {
        document: "REG-HLT-2024_Sec4",
        page: 47,
        content_snippet:
          "Pre-existing conditions are subject to a thirty-six (36) month continuous coverage requirement before any related claim becomes admissible under this contract.",
        confidence: 0.91,
      },
      {
        document: "POL-BASIC-T1_Schedule",
        page: 3,
        content_snippet:
          "The insurer shall not impose a waiting period exceeding the statutory maximum defined by the applicable regional insurance authority.",
        confidence: 0.78,
      },
    ],
    execution_time_ms: Math.round(900 + Math.random() * 700),
    demo: true,
  }
}
