"use client"

import { motion } from "motion/react"
import { FileText, Quote } from "lucide-react"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import type { Source } from "@/lib/types"

function confidenceTone(confidence: number) {
  if (confidence >= 0.9) return "text-success"
  if (confidence >= 0.7) return "text-accent"
  return "text-muted-foreground"
}

export function CitationsPanel({ sources }: { sources: Source[] }) {
  return (
    <div className="glass rounded-2xl border border-border/60 p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-mono text-xs uppercase tracking-widest text-muted-foreground">Source Citations</h3>
        <span className="font-mono text-xs text-muted-foreground">{sources.length}</span>
      </div>

      <Accordion className="flex flex-col gap-2.5">
        {sources.map((source, i) => (
          <motion.div
            key={`${source.document}-${source.page}-${i}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: i * 0.08 }}
          >
            <AccordionItem
              value={`${source.document}-${i}`}
              className="rounded-xl border border-border/60 bg-secondary/30 px-3.5 not-last:border-b"
            >
              <AccordionTrigger className="hover:no-underline">
                <div className="flex flex-1 items-center gap-3 pr-2">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <FileText className="size-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-mono text-sm font-medium">{source.document}</p>
                    <p className="text-xs text-muted-foreground">Page {source.page}</p>
                  </div>
                  <span className={`shrink-0 font-mono text-xs font-medium tabular-nums ${confidenceTone(source.confidence)}`}>
                    {Math.round(source.confidence * 100)}%
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex gap-2.5 rounded-lg border border-border/50 bg-background/60 p-3">
                  <Quote className="size-4 shrink-0 text-accent" />
                  <p className="text-sm leading-relaxed text-muted-foreground">{source.content_snippet}</p>
                </div>
              </AccordionContent>
            </AccordionItem>
          </motion.div>
        ))}
      </Accordion>
    </div>
  )
}
