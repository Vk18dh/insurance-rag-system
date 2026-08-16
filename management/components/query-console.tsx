"use client"

import { useState, type FormEvent, type KeyboardEvent } from "react"
import { AnimatePresence, motion } from "motion/react"
import { ArrowUp, CornerDownLeft, Search, TriangleAlert } from "lucide-react"
import { runQuery } from "@/lib/api"
import type { QueryResponse } from "@/lib/types"
import { AnswerDisplay } from "@/components/answer-display"
import { AnswerSkeleton } from "@/components/answer-skeleton"
import { MetricsPanel } from "@/components/metrics-panel"
import { CitationsPanel } from "@/components/citations-panel"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

const EXAMPLES = [
  "What is the waiting period for the basic health insurance?",
  "Are pre-existing conditions covered under the standard tier?",
  "What documentation is required to file an accidental injury claim?",
]

export function QueryConsole() {
  const [query, setQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function submit(value: string) {
    const q = value.trim()
    if (!q || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await runQuery(q)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    submit(query)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      if (e.nativeEvent.isComposing || e.keyCode === 229) return
      e.preventDefault()
      submit(query)
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col px-4 sm:px-6">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="mx-auto flex max-w-3xl flex-col items-center pt-16 text-center sm:pt-24"
      >
        <span className="glass mb-5 inline-flex items-center gap-2 rounded-full border border-border/60 px-3 py-1 font-mono text-xs text-muted-foreground">
          <span className="size-1.5 rounded-full bg-accent" />
          Agentic RAG · Grounded Citations
        </span>
        <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-6xl">AI Insurance Auditor</h1>
        <p className="mt-4 max-w-xl text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
          Query regulatory policies and insurance rules with guaranteed citations.
        </p>
      </motion.div>

      {/* Search */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mx-auto mt-10 w-full max-w-3xl"
      >
        <form onSubmit={handleSubmit}>
          <div className="glass group rounded-2xl border border-border/70 p-2 shadow-xl shadow-primary/5 transition-colors focus-within:border-primary/60">
            <div className="flex items-start gap-3 px-3 pt-2.5">
              <Search className="mt-1 size-5 shrink-0 text-muted-foreground" />
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
                placeholder="Ask about policy clauses, waiting periods, exclusions, or compliance rules…"
                className="max-h-40 min-h-11 w-full resize-none bg-transparent text-[15px] leading-relaxed outline-none placeholder:text-muted-foreground"
                aria-label="Insurance policy query"
              />
            </div>
            <div className="flex items-center justify-between px-3 pb-1.5 pt-1">
              <span className="hidden items-center gap-1.5 font-mono text-[11px] text-muted-foreground sm:flex">
                <CornerDownLeft className="size-3" />
                Enter to audit · Shift + Enter for newline
              </span>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="ml-auto inline-flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? "Auditing…" : "Audit"}
                <ArrowUp className="size-4" />
              </button>
            </div>
          </div>
        </form>

        {/* Example chips */}
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                setQuery(ex)
                submit(ex)
              }}
              disabled={loading}
              className="glass rounded-full border border-border/60 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground disabled:opacity-50"
            >
              {ex}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Results */}
      <div className="mx-auto mt-12 w-full max-w-6xl pb-24">
        <AnimatePresence mode="wait">
          {loading && (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <AnswerSkeleton />
            </motion.div>
          )}

          {!loading && error && (
            <motion.div key="error" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
              <Alert variant="destructive" className="glass mx-auto max-w-3xl border-destructive/40">
                <TriangleAlert />
                <AlertTitle>Unable to complete audit</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </motion.div>
          )}

          {!loading && result && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="flex flex-col gap-5"
            >
              {result.demo && (
                <p className="mx-auto text-center font-mono text-[11px] text-muted-foreground">
                  Live backend unreachable — showing a grounded demo response.
                </p>
              )}
              <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
                <AnswerDisplay result={result} />
                <div className="flex flex-col gap-5">
                  <MetricsPanel result={result} />
                  <CitationsPanel sources={result.sources} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
