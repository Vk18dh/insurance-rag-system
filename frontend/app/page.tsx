"use client"

import React from 'react'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { motion } from 'motion/react'
import { ArrowRight, Shield, Zap, Search, ShieldCheck, Database, BookOpen } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SiteHeader } from '@/components/site-header'

// Dynamically import the Earth component to avoid SSR issues with WebGL
const EarthScene = dynamic(() => import('@/components/3d/earth-scene'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center">
      {/* Fallback for when WebGL is loading or unavailable */}
      <div className="w-[300px] h-[300px] md:w-[500px] md:h-[500px] rounded-full bg-primary/5 blur-3xl" />
    </div>
  ),
})

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-transparent flex flex-col">
      <SiteHeader />
      
      <main className="flex-1">
        {/* HERO SECTION */}
        <section className="relative w-full h-[85vh] min-h-[650px] flex items-center pt-16">
          {/* Ambient Background Light */}
          <div className="pointer-events-none absolute -top-40 left-1/4 z-0 size-[640px] -translate-x-1/2 rounded-full bg-primary/20 blur-[140px]" aria-hidden="true" />
          
          <div className="container max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 flex flex-col md:flex-row items-center h-full">
            <div className="flex-1 flex flex-col justify-center space-y-6 max-w-2xl pt-10 md:pt-0 z-20 pr-4 md:pr-12">
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-sm text-primary w-fit backdrop-blur-md"
              >
                <Shield className="mr-2 h-4 w-4" />
                Enterprise Grade Intelligence
              </motion.div>
              
              <motion.h1 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.1, ease: "easeOut" }}
                className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground drop-shadow-sm leading-tight"
              >
                Trusted Knowledge. <br/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
                  Smarter Decisions.
                </span>
              </motion.h1>
              
              <motion.p 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
                className="text-lg md:text-xl text-muted-foreground leading-relaxed max-w-xl"
              >
                Ask questions about insurance policies and get answers grounded in trusted insurance documents with verifiable citations.
              </motion.p>
              
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
                className="flex flex-col sm:flex-row gap-4"
              >
                <Button size="lg" className="rounded-full px-8 text-base shadow-lg shadow-primary/25" render={<Link href="/chat" />} nativeButton={false}>
                  Ask AI Now
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
                <Button size="lg" variant="outline" className="rounded-full px-8 text-base glass hover:bg-white/5" render={<Link href="#how-it-works" />} nativeButton={false}>
                  Explore Knowledge
                </Button>
              </motion.div>
            </div>
            
            <div className="flex-1 w-full h-[50vh] md:h-[600px] absolute md:relative right-0 opacity-40 md:opacity-100 z-10 pointer-events-auto">
              <EarthScene />
            </div>
          </div>
        </section>

        {/* HOW IT WORKS SECTION */}
        <section id="how-it-works" className="py-24 bg-card relative z-20">
          <div className="container">
            <div className="text-center max-w-3xl mx-auto mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">How Insurance AI Works</h2>
              <p className="text-muted-foreground text-lg">A robust RAG (Retrieval-Augmented Generation) pipeline ensuring every answer is accurate and auditable.</p>
            </div>
            
            <div className="grid md:grid-cols-4 gap-8">
              {[
                { step: "1. Ask", icon: Search, title: "Query Intent", desc: "Your question is analyzed for intent and insurance context." },
                { step: "2. Retrieve", icon: Database, title: "Vector Search", desc: "We retrieve the most relevant official policy documents." },
                { step: "3. Verify", icon: ShieldCheck, title: "Fact Check", desc: "Information is verified against strict guardrails." },
                { step: "4. Answer", icon: Zap, title: "Grounded Response", desc: "You receive an accurate answer with exact document citations." }
              ].map((item, i) => (
                <div key={i} className="glass p-8 rounded-3xl border border-white/5 flex flex-col items-start relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                    <item.icon className="w-32 h-32" />
                  </div>
                  <div className="h-12 w-12 rounded-2xl bg-primary/20 text-primary flex items-center justify-center mb-6">
                    <item.icon className="h-6 w-6" />
                  </div>
                  <div className="text-sm font-semibold text-primary mb-2 tracking-wider uppercase">{item.step}</div>
                  <h3 className="text-xl font-bold mb-3">{item.title}</h3>
                  <p className="text-muted-foreground">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* TRUSTED SOURCES SECTION */}
        <section className="py-24 relative z-20 overflow-hidden">
          <div className="pointer-events-none absolute top-1/2 left-1/2 z-0 size-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent/5 blur-[120px]" aria-hidden="true" />
          <div className="container relative z-10">
            <div className="flex flex-col md:flex-row items-center gap-16">
              <div className="flex-1 space-y-6">
                <h2 className="text-3xl md:text-4xl font-bold">Grounded in Trusted Sources</h2>
                <p className="text-lg text-muted-foreground">
                  Our AI does not guess. Every answer provided includes exact citations linking back to the official policy documents, terms and conditions, and regulatory guidelines.
                </p>
                <ul className="space-y-4 pt-4">
                  {[
                    "Direct citations with page numbers",
                    "Confidence scoring for reliability",
                    "Immediate access to source excerpts",
                    "Safe refusals for unknown information"
                  ].map((feature, i) => (
                    <li key={i} className="flex items-center text-foreground">
                      <div className="mr-4 rounded-full bg-primary/20 p-1">
                        <ShieldCheck className="h-4 w-4 text-primary" />
                      </div>
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex-1 w-full max-w-md mx-auto">
                <div className="glass p-6 rounded-3xl border border-white/10 shadow-2xl relative">
                  <div className="absolute -top-4 -right-4 h-24 w-24 bg-primary/30 rounded-full blur-2xl" />
                  <div className="space-y-4">
                    <div className="h-4 w-1/3 bg-white/10 rounded" />
                    <div className="h-4 w-full bg-white/5 rounded" />
                    <div className="h-4 w-5/6 bg-white/5 rounded" />
                    <div className="h-4 w-4/6 bg-white/5 rounded" />
                    <div className="pt-4 border-t border-white/10 mt-4">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <BookOpen className="h-3 w-3" />
                        <span>Source: LIC Bima Jyoti, Page 12</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FINAL CTA */}
        <section className="py-24 relative z-20">
          <div className="container">
            <div className="glass rounded-4xl p-12 md:p-24 text-center border border-primary/20 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-primary/10 to-transparent" />
              <div className="relative z-10 max-w-2xl mx-auto space-y-8">
                <h2 className="text-4xl md:text-5xl font-bold">Ready to get answers?</h2>
                <p className="text-xl text-muted-foreground">
                  Experience the next generation of insurance intelligence.
                </p>
                <Button size="lg" className="rounded-full px-10 py-6 text-lg shadow-xl shadow-primary/20" render={<Link href="/chat" />} nativeButton={false}>
                  Ask the Insurance AI
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>
      
      {/* Footer */}
      <footer className="py-12 border-t border-border/50 bg-background/50 relative z-20">
        <div className="container flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            <span className="font-bold text-lg tracking-tight">Insurance<span className="text-primary">AI</span></span>
          </div>
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} Insurance AI Intelligence Platform.
          </p>
        </div>
      </footer>
    </div>
  )
}
