import { ShieldCheck } from "lucide-react"
import { ThemeToggle } from "@/components/theme-toggle"
import { BackendStatus } from "@/components/backend-status"

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/50">
      <div className="glass">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <ShieldCheck className="size-5" />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold tracking-tight">Aegis Audit</p>
              <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                Insurance Intelligence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="hidden sm:block">
              <BackendStatus />
            </div>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  )
}
