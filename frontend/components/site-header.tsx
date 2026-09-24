"use client"

import { ShieldCheck, User } from "lucide-react"
import { BackendStatus } from "@/components/backend-status"
import Link from "next/link"
import { motion, useScroll, useTransform } from "motion/react"
import { Button } from "@/components/ui/button"

export function SiteHeader() {
  const { scrollY } = useScroll()
  const headerBackground = useTransform(scrollY, [0, 50], ["rgba(0, 0, 0, 0)", "var(--card)"])
  const headerBorder = useTransform(scrollY, [0, 50], ["rgba(255, 255, 255, 0)", "var(--border)"])
  const headerBackdrop = useTransform(scrollY, [0, 50], ["blur(0px)", "blur(16px)"])
  const padding = useTransform(scrollY, [0, 50], ["1.5rem", "0.75rem"])

  return (
    <motion.header 
      style={{
        backgroundColor: headerBackground,
        borderBottomColor: headerBorder,
        backdropFilter: headerBackdrop,
        WebkitBackdropFilter: headerBackdrop,
        paddingTop: padding,
        paddingBottom: padding,
        borderBottomWidth: "1px"
      }}
      className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Left: Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <img src="/logo.png" alt="InsuraLens" className="h-8 md:h-10 w-auto object-contain transition-transform group-hover:scale-105" />
        </Link>

        {/* Center: Navigation (Desktop only) */}
        <nav className="hidden md:flex items-center gap-8 rounded-full border border-border/50 bg-background/30 px-6 py-2 backdrop-blur-md">
          <Link href="#product" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Product</Link>
          <Link href="#how-it-works" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">How It Works</Link>
          <Link href="#sources" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Sources</Link>
          <Link href="/chat" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">AI Assistant</Link>
        </nav>

        {/* Right: Controls & CTA */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:block">
            <BackendStatus />
          </div>
          <div className="h-4 w-[1px] bg-border mx-1 hidden sm:block" />
          <Link href="/chat">
            <Button size="sm" className="hidden sm:flex rounded-full shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all hover:-translate-y-0.5">
              Ask AI
            </Button>
          </Link>
          <Link href="/login" className="hidden sm:flex h-9 w-9 items-center justify-center rounded-full border border-border bg-background/50 hover:bg-muted transition-colors">
            <User className="size-4 text-muted-foreground" />
          </Link>
        </div>
      </div>
    </motion.header>
  )
}
