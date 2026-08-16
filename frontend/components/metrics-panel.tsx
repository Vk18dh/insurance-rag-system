"use client"

import { motion } from "motion/react"
import { Clock, ShieldAlert, ShieldCheck, Gauge } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { cn } from "@/lib/utils"
import type { QueryResponse } from "@/lib/api-client"

function ConfidenceRing({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const radius = 34
  const circumference = 2 * Math.PI * radius
  const tone = pct >= 85 ? "text-success" : pct >= 60 ? "text-accent" : "text-destructive"

  return (
    <div className="relative flex size-24 items-center justify-center">
      <svg className="size-24 -rotate-90" viewBox="0 0 80 80" aria-hidden="true">
        <circle cx="40" cy="40" r={radius} fill="none" stroke="currentColor" strokeWidth="6" className="text-border" />
        <motion.circle
          cx="40"
          cy="40"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="6"
          strokeLinecap="round"
          className={tone}
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - (pct / 100) * circumference }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xl font-semibold tabular-nums">{pct}%</span>
        <span className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">Confidence</span>
      </div>
    </div>
  )
}

export function MetricsPanel({ result }: { result: QueryResponse }) {
  return (
    <div className="glass rounded-2xl border border-border/60 p-5">
      <h3 className="mb-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">Assessment Metrics</h3>

      <div className="flex items-center gap-5">
        <ConfidenceRing score={result.confidence_score} />

        <div className="flex flex-1 flex-col gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-secondary/40 px-3 py-2">
            <Clock className="size-4 text-accent" />
            <div className="leading-tight">
              <p className="text-sm font-medium tabular-nums">{result.execution_time_ms.toFixed(1)} ms</p>
              <p className="text-xs text-muted-foreground">Execution time</p>
            </div>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-secondary/40 px-3 py-2">
            <Gauge className="size-4 text-accent" />
            <div className="leading-tight">
              <p className="text-sm font-medium tabular-nums">{result.sources.length} sources</p>
              <p className="text-xs text-muted-foreground">Documents cited</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4">
        {result.confidence_score === 0.0 ? (
          <Alert variant="destructive" className="border-destructive/40 bg-destructive/10">
            <ShieldAlert />
            <AlertTitle>Low Confidence</AlertTitle>
            <AlertDescription>
              Out-of-Domain bounds. The AI could not find related evidence and actively refuses hallucination.
            </AlertDescription>
          </Alert>
        ) : result.is_safe ? (
          <Alert className="border-success/40 bg-success/10">
            <ShieldCheck className="text-success!" />
            <AlertTitle className="text-success">Bounds check passed</AlertTitle>
            <AlertDescription className="text-success/80">
              Response validated against regulatory guardrails and grounded in cited sources.
            </AlertDescription>
          </Alert>
        ) : (
          <Alert variant="destructive" className="border-destructive/40 bg-destructive/10">
            <ShieldAlert />
            <AlertTitle>Potential regulatory risk</AlertTitle>
            <AlertDescription>
              This response failed the safety bounds check. Review with a compliance officer before relying on it.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  )
}

export function SafetyPill({ isSafe }: { isSafe: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider",
        isSafe ? "border-success/40 bg-success/10 text-success" : "border-destructive/40 bg-destructive/10 text-destructive",
      )}
    >
      {isSafe ? <ShieldCheck className="size-3" /> : <ShieldAlert className="size-3" />}
      {isSafe ? "Safe" : "Flagged"}
    </span>
  )
}
