import { SiteHeader } from "@/components/site-header"
import { QueryConsole } from "@/components/query-console"

export default function Page() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-60" aria-hidden="true" />
      <div
        className="animate-aurora pointer-events-none absolute -top-40 left-1/2 -z-0 size-[640px] -translate-x-1/2 rounded-full bg-primary/20 blur-[140px]"
        aria-hidden="true"
      />
      <div
        className="animate-aurora pointer-events-none absolute top-1/3 -right-32 -z-0 size-[420px] rounded-full bg-accent/15 blur-[130px]"
        aria-hidden="true"
      />

      <div className="relative z-10">
        <SiteHeader />
        <QueryConsole />
      </div>
    </main>
  )
}
