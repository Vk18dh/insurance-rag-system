"use client"

import React from 'react'
import Link from 'next/link'
import { Shield } from 'lucide-react'
import { SiteHeader } from '@/components/site-header'
import { HeroSection } from '@/components/landing/hero-section'
import { InteractiveQuestion } from '@/components/landing/interactive-question'
import { RagStory } from '@/components/landing/rag-story'
import { EvidenceExplorer } from '@/components/landing/evidence-explorer'
import { AiDemo } from '@/components/landing/ai-demo'
import { ArchitectureStory } from '@/components/landing/architecture-story'
import { Button } from '@/components/ui/button'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-transparent flex flex-col selection:bg-primary/30 selection:text-primary-foreground">
      <SiteHeader />
      
      <main className="flex-1">
        <HeroSection />
        <InteractiveQuestion />
        <RagStory />
        <EvidenceExplorer />
        <AiDemo />
        <ArchitectureStory />
        
        {/* FINAL CTA */}
        <section className="py-32 relative z-20">
          <div className="container px-4">
            <div className="glass rounded-[3rem] p-12 md:p-24 text-center border border-primary/20 relative overflow-hidden max-w-5xl mx-auto shadow-2xl">
              <div className="absolute inset-0 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none" />
              <div className="relative z-10 max-w-2xl mx-auto space-y-8">
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight">Ready to get answers?</h2>
                <p className="text-xl text-muted-foreground">
                  Experience the next generation of grounded insurance intelligence.
                </p>
                <div className="pt-4">
                  <Link href="/chat">
                    <Button size="lg" className="rounded-full px-10 h-14 text-lg shadow-[0_0_20px_rgba(var(--primary),0.3)] hover:scale-105 transition-transform">
                      Ask the Insurance AI
                    </Button>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      
      {/* Footer */}
      <footer className="py-12 border-t border-border/50 bg-background/50 relative z-20">
        <div className="container max-w-7xl mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <span className="font-bold text-lg tracking-tight">Aegis <span className="text-primary font-normal">Audit</span></span>
          </div>
          <div className="flex gap-8 text-sm text-muted-foreground">
            <Link href="#product" className="hover:text-primary transition-colors">Product</Link>
            <Link href="#how-it-works" className="hover:text-primary transition-colors">How It Works</Link>
            <Link href="#sources" className="hover:text-primary transition-colors">Sources</Link>
          </div>
          <p className="text-sm text-muted-foreground/60">
            © {new Date().getFullYear()} Aegis Audit Intelligence Platform.
          </p>
        </div>
      </footer>
    </div>
  )
}
