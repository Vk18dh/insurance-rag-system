"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { Clock, ShieldAlert, ShieldCheck, Gauge, ChevronDown, Activity } from "lucide-react"
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
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="glass rounded-2xl border border-white/5 bg-card/40 p-4 shadow-sm backdrop-blur-xl">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between group"
      >
        <div className="flex items-center gap-2">
          <Activity className="size-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground tracking-wide">Assessment Metrics</h3>
        </div>
        <ChevronDown className={`size-4 text-muted-foreground transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0, marginTop: 0 }}
            animate={{ height: "auto", opacity: 1, marginTop: 16 }}
            exit={{ height: 0, opacity: 0, marginTop: 0 }}
            className="overflow-hidden"
          >
            <div className="flex items-center gap-5">
              <ConfidenceRing score={result.confidence_score} />

              <div className="flex flex-1 flex-col gap-3">
                <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-secondary/40 px-3 py-2">
                  <Clock className="size-4 text-accent" />
                  <div className="leading-tight">
                    <p className="text-sm font-medium tabular-nums">{(result.execution_time_ms / 1000).toFixed(2)} s</p>
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
          </motion.div>
        )}
      </AnimatePresence>
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
