import React from "react"
import { SiteHeader } from "@/components/site-header"
import { Sidebar } from "@/components/chat/sidebar"

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden relative">
        {/* Ambient background */}
        <div className="pointer-events-none absolute inset-0 grid-bg opacity-60 z-0" aria-hidden="true" />
        <div
          className="animate-aurora pointer-events-none absolute -top-40 left-1/2 z-0 size-[640px] -translate-x-1/2 rounded-full bg-primary/20 blur-[140px]"
          aria-hidden="true"
        />
        <div
          className="animate-aurora pointer-events-none absolute top-1/3 -right-32 z-0 size-[420px] rounded-full bg-accent/15 blur-[130px]"
          aria-hidden="true"
        />
        <div className="relative z-10 flex flex-col flex-1 overflow-hidden">
          <SiteHeader />
          <main className="flex-1 overflow-hidden flex flex-col">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
