"use client"

import React, { useState } from 'react'
import { motion } from 'motion/react'
import { Search, Sparkles, ArrowRight } from 'lucide-react'
import { useRouter } from 'next/navigation'

const SUGGESTED_QUERIES = [
  "Policy benefits",
  "Waiting periods",
  "Exclusions",
  "Eligibility criteria",
  "Claim documentation",
  "Policy conditions"
]

export function InteractiveQuestion() {
  const router = useRouter()
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)

  const handleQueryClick = (query: string) => {
    router.push(`/chat?q=${encodeURIComponent(query)}`)
  }

  return (
    <section id="explore" className="relative py-32 z-20 bg-background overflow-hidden">
      {/* Subtle grid background */}
      <div className="absolute inset-0 subtle-grid-bg opacity-30 pointer-events-none" />
      
      <div className="container relative z-10 max-w-5xl mx-auto px-4">
        <div className="text-center mb-16 space-y-4">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="text-4xl md:text-5xl font-bold tracking-tight text-foreground"
          >
            What do you need to know?
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            Ask any question about your policy. Our intelligence engine analyzes official documents to give you a grounded, accurate answer.
          </motion.p>
        </div>

        {/* Central Search Interface */}
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, delay: 0.2, type: "spring", stiffness: 100 }}
          className="relative max-w-3xl mx-auto mb-16"
        >
          <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-primary/30 via-accent/30 to-primary/30 blur-xl opacity-50" />
          <div className="relative flex items-center gap-4 bg-card/80 backdrop-blur-xl border border-border/50 rounded-2xl p-4 shadow-2xl transition-all duration-300 hover:border-primary/50">
            <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Search className="size-6" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-muted-foreground text-lg">Type your insurance question...</p>
            </div>
            <button 
              onClick={() => router.push('/chat')}
              className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md hover:scale-105 transition-transform"
            >
              <ArrowRight className="size-5" />
            </button>
          </div>
        </motion.div>

        {/* Suggested Queries - Interactive Layout */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 max-w-4xl mx-auto">
          {SUGGESTED_QUERIES.map((query, index) => (
            <motion.button
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
              onClick={() => handleQueryClick(`What are the ${query.toLowerCase()}?`)}
              className={`relative overflow-hidden rounded-2xl border p-6 text-left transition-all duration-300 ${
                hoveredIndex === index 
                  ? 'border-primary/50 bg-primary/5 -translate-y-1 shadow-lg shadow-primary/10' 
                  : 'border-border/40 bg-card/40 hover:bg-card/80'
              }`}
            >
              <div className="flex flex-col gap-3">
                <Sparkles className={`size-5 transition-colors ${hoveredIndex === index ? 'text-primary' : 'text-muted-foreground/50'}`} />
                <span className={`font-medium transition-colors ${hoveredIndex === index ? 'text-foreground' : 'text-muted-foreground'}`}>
                  {query}
                </span>
              </div>
              
              {/* Hover effect gradient */}
              <div 
                className={`absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-0 transition-opacity duration-300 pointer-events-none ${hoveredIndex === index ? 'opacity-100' : ''}`}
              />
            </motion.button>
          ))}
        </div>
      </div>
    </section>
  )
}
