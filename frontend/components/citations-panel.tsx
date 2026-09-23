"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "motion/react"
import { FileText, Quote, FileSearch, ChevronDown } from "lucide-react"
import type { RetrievedSource as Source } from "@/lib/api-client"

function confidenceTone(confidence: number) {
  if (confidence >= 0.9) return "text-success bg-success/10 border-success/20"
  if (confidence >= 0.7) return "text-accent bg-accent/10 border-accent/20"
  return "text-muted-foreground bg-muted/10 border-border"
}

export function CitationsPanel({ sources }: { sources: Source[] }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!sources || sources.length === 0) return null

  return (
    <div className="glass rounded-2xl border border-white/5 bg-card/40 p-4 mt-2 shadow-sm backdrop-blur-xl">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between group"
      >
        <div className="flex items-center gap-2">
          <FileSearch className="size-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground tracking-wide">Sources ({sources.length})</h3>
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
            <div className="flex flex-col gap-3">
        {sources.map((source, i) => (
          <motion.div
            key={`${source.document}-${source.page}-${i}`}
            id={`citation-${i + 1}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.08 }}
            className="flex flex-col gap-2 rounded-xl border border-border/50 bg-secondary/20 p-3.5 transition-colors hover:bg-secondary/40"
          >
            <div className="flex items-center gap-3">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-primary/10 text-[10px] font-bold text-primary">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-4">
                <p className="truncate text-sm font-medium text-foreground/90" title={source.document}>
                  {source.document.replace(/\.[^/.]+$/, "").replace(/_/g, " - ")}
                </p>
                <div className="flex items-center gap-3 shrink-0">
                  {source.page > 0 && (
                    <span className="text-xs text-muted-foreground">Page {source.page}</span>
                  )}
                  <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold tabular-nums border ${confidenceTone(source.confidence)}`}>
                    {Math.round(source.confidence * 100)}%
                  </span>
                </div>
              </div>
            </div>
            
            <div className="ml-8 rounded-lg border-l-2 border-accent/40 bg-background/40 py-2 pl-3 pr-2">
              {source.content_snippet && source.content_snippet.length > 0 ? (
                <p className="text-[13px] leading-relaxed text-muted-foreground/90 italic">
                  "{source.content_snippet.trim()}"
                </p>
              ) : (
                <p className="text-[13px] text-muted-foreground/60 italic">
                  Source text unavailable.
                </p>
              )}
            </div>
          </motion.div>
        ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
