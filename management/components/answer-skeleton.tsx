"use client"

import { useEffect, useState } from "react"
import { motion } from "motion/react"
import { Loader2 } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

const STAGES = ["Retrieving policy documents", "Auditing documents", "Formulating response", "Verifying citations"]

export function AnswerSkeleton() {
  const [stage, setStage] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setStage((s) => (s + 1) % STAGES.length), 1400)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
      <div className="glass rounded-2xl border border-border/60 p-6">
        <div className="mb-5 flex items-center gap-2.5">
          <Loader2 className="size-4 animate-spin text-primary" />
          <motion.span
            key={stage}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="font-mono text-sm text-muted-foreground"
          >
            {STAGES[stage]}…
          </motion.span>
        </div>
        <div className="flex flex-col gap-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-[92%]" />
          <Skeleton className="h-4 w-[97%]" />
          <Skeleton className="h-4 w-[70%]" />
          <div className="h-2" />
          <Skeleton className="h-4 w-[85%]" />
          <Skeleton className="h-4 w-[60%]" />
        </div>
      </div>
      <div className="flex flex-col gap-5">
        <div className="glass rounded-2xl border border-border/60 p-5">
          <Skeleton className="mb-4 h-3 w-28" />
          <div className="flex items-center gap-5">
            <Skeleton className="size-24 rounded-full" />
            <div className="flex flex-1 flex-col gap-3">
              <Skeleton className="h-11 w-full rounded-lg" />
              <Skeleton className="h-11 w-full rounded-lg" />
            </div>
          </div>
        </div>
        <div className="glass rounded-2xl border border-border/60 p-5">
          <Skeleton className="mb-3 h-3 w-24" />
          <div className="flex flex-col gap-2.5">
            <Skeleton className="h-14 w-full rounded-xl" />
            <Skeleton className="h-14 w-full rounded-xl" />
            <Skeleton className="h-14 w-full rounded-xl" />
          </div>
        </div>
      </div>
    </div>
  )
}
