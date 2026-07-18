import type { HealthResponse, QueryResponse } from "@/lib/types"

export async function runQuery(query: string): Promise<QueryResponse> {
  const res = await fetch("/api/v1/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.error || `Request failed with status ${res.status}`)
  }

  return res.json()
}

export async function fetchHealth(): Promise<HealthResponse & { live: boolean }> {
  const res = await fetch("/api/v1/health")
  if (!res.ok) throw new Error("Health check failed")
  return res.json()
}
