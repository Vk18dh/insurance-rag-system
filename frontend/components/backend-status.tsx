"use client"

import useSWR from "swr"
import { fetchHealth } from "@/lib/api"
import { cn } from "@/lib/utils"

export function BackendStatus() {
  const { data, isLoading } = useSWR("health", fetchHealth, {
    refreshInterval: 30_000,
    revalidateOnFocus: false,
  })

  const live = data?.live === true
  const label = isLoading ? "Connecting" : live ? "Backend live" : "Demo mode"

  return (
    <div className="glass flex items-center gap-2 rounded-full border border-border/60 px-3 py-1.5">
      <span className="relative flex size-2">
        <span
          className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-75",
            isLoading ? "bg-muted-foreground" : live ? "animate-ping bg-success" : "bg-accent",
          )}
        />
        <span
          className={cn(
            "relative inline-flex size-2 rounded-full",
            isLoading ? "bg-muted-foreground" : live ? "bg-success" : "bg-accent",
          )}
        />
      </span>
      <span className="font-mono text-xs tracking-wide text-muted-foreground">{label}</span>
    </div>
  )
}
