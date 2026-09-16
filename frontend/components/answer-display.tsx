"use client"

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Sparkles, ShieldAlert } from "lucide-react"
import { SafetyPill } from "@/components/metrics-panel"
import type { QueryResponse } from "@/lib/api-client"

    export function AnswerDisplay({ result }: { result: QueryResponse }) {
  // Pre-process citations [1] into markdown links targeting citations
  const formattedAnswer = result.final_answer.replace(/\[(\d+)\]/g, '[$1](#citation-$1)')

  return (
    <div className="glass rounded-2xl border border-border/60 p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="size-4" />
          </div>
          <h2 className="text-sm font-semibold">Auditor Response</h2>
        </div>
        {result.confidence_score === 0.0 ? (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-destructive/40 bg-destructive/10 px-2.5 py-1 font-mono text-[10px] uppercase tracking-wider text-destructive">
            <ShieldAlert className="size-3" />
            Low Confidence
          </span>
        ) : (
          <SafetyPill isSafe={result.is_safe} />
        )}
      </div>

      <div className="prose-answer max-w-none text-[15px] leading-relaxed text-foreground/90 tracking-wide">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <p className="mb-5 last:mb-0 leading-relaxed text-foreground/90">{children}</p>,
            strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
            ul: ({ children }) => <ul className="mb-5 ml-2 flex flex-col gap-2">{children}</ul>,
            ol: ({ children }) => <ol className="mb-5 ml-6 flex list-decimal flex-col gap-2">{children}</ol>,
            li: ({ children }) => (
              <li className="relative pl-5 leading-relaxed marker:text-accent before:absolute before:left-0 before:top-2.5 before:size-1.5 before:rounded-full before:bg-accent">
                {children}
              </li>
            ),
            blockquote: ({ children }) => (
              <blockquote className="my-5 rounded-r-lg border-l-2 border-accent bg-accent/5 py-3 pl-5 pr-4 text-muted-foreground italic">
                {children}
              </blockquote>
            ),
            h1: ({ children }) => <h1 className="mb-4 text-lg font-semibold">{children}</h1>,
            h2: ({ children }) => <h2 className="mb-3 mt-5 text-base font-semibold">{children}</h2>,
            code: ({ children }) => (
              <code className="rounded bg-secondary/80 px-1.5 py-0.5 font-mono text-sm">{children}</code>
            ),
            a: ({ children, href }) => {
              if (href?.startsWith("#citation-")) {
                const id = href.replace("#citation-", "")
                return (
                  <sup className="inline-flex cursor-pointer select-none items-center justify-center rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold text-primary transition-colors hover:bg-primary/20 mx-0.5 relative -top-1">
                    {id}
                  </sup>
                )
              }
              return (
                <a href={href} className="text-primary underline underline-offset-2 hover:text-primary/80 transition-colors">
                  {children}
                </a>
              )
            },
          }}
        >
          {formattedAnswer}
        </ReactMarkdown>
      </div>

      <div className="mt-5 flex items-center gap-2 border-t border-border/50 pt-3">
        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">Query ID</span>
        <span className="truncate font-mono text-xs text-muted-foreground/80">{result.query_id}</span>
      </div>
    </div>
  )
}
