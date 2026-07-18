export interface Source {
  document: string
  page: number
  content_snippet: string
  confidence: number
}

export interface QueryResponse {
  query_id: string
  final_answer: string
  confidence_score: number
  is_safe: boolean
  sources: Source[]
  execution_time_ms: number
  /** Set by the proxy when the live backend was unreachable and demo data was served. */
  demo?: boolean
}

export interface HealthResponse {
  status: string
  version: string
  components: Record<string, unknown>
}
