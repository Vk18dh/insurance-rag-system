"use client"

import React from 'react'
import Link from 'next/link'
import dynamic from 'next/dynamic'
import { motion, useScroll, useTransform } from 'motion/react'
import { ArrowRight, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'

const EarthScene = dynamic(() => import('@/components/3d/earth-scene'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center">
      <div className="w-[300px] h-[300px] md:w-[600px] md:h-[600px] rounded-full bg-primary/5 blur-[100px]" />
    </div>
  ),
})

export function HeroSection() {
  const { scrollY } = useScroll()
  const y = useTransform(scrollY, [0, 1000], [0, 300])
  const opacity = useTransform(scrollY, [0, 500], [1, 0])
  const scale = useTransform(scrollY, [0, 500], [1, 0.9])

  return (
    <section className="relative w-full h-[100vh] min-h-[700px] flex items-center justify-center overflow-hidden">
      {/* Dynamic Background Atmosphere */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] mix-blend-screen animate-aurora" />
        <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-accent/5 rounded-full blur-[150px] mix-blend-screen" />
      </div>

      {/* Earth Visualization (Background Layer) */}
      <motion.div 
        style={{ y, opacity, scale }}
        className="absolute inset-0 z-10 flex items-center justify-center opacity-80 pointer-events-auto"
      >
        <div className="w-full max-w-[1200px] aspect-square translate-y-[20%] md:translate-y-[15%]">
          <EarthScene />
        </div>
      </motion.div>

      {/* Typography and Content (Foreground Layer) */}
      <div className="container relative z-20 flex flex-col items-center justify-center text-center pt-20 px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 backdrop-blur-md"
        >
          <ShieldCheck className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium tracking-wide text-primary uppercase">Insurance Intelligence</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="max-w-4xl text-5xl font-bold tracking-tight text-foreground sm:text-6xl md:text-7xl lg:text-8xl leading-[1.1]"
        >
          Trusted Knowledge.
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-b from-foreground to-foreground/50">
            Smarter Decisions.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto mt-8 max-w-2xl text-lg md:text-xl text-muted-foreground leading-relaxed"
        >
          Ask questions about insurance policies and receive answers grounded in the available insurance knowledge base with traceable source references.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link href="/chat">
            <Button size="lg" className="rounded-full px-8 h-12 text-base font-medium shadow-[0_0_20px_rgba(var(--primary),0.3)] hover:shadow-[0_0_30px_rgba(var(--primary),0.5)] transition-all hover:scale-105">
              Ask AI
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="#explore">
            <Button size="lg" variant="outline" className="rounded-full px-8 h-12 text-base font-medium glass border-border/50 hover:bg-white/5 transition-colors">
              Explore how it works
            </Button>
          </Link>
        </motion.div>
      </div>

      {/* Scroll Indicator */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 1 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-2"
      >
        <span className="text-xs uppercase tracking-widest text-muted-foreground font-mono">Scroll</span>
        <div className="w-[1px] h-12 bg-gradient-to-b from-muted-foreground/50 to-transparent" />
      </motion.div>
    </section>
  )
}
