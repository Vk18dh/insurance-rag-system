"use client"

import React from 'react'
import { motion } from 'motion/react'
import { Layers, Search, ShieldCheck, FileText, Bot } from 'lucide-react'

export function ArchitectureStory() {
  return (
    <section className="relative py-32 bg-card/30 border-y border-border/50 overflow-hidden">
      <div className="container max-w-6xl mx-auto px-4">
        
        <div className="text-center mb-24">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Under the Hood</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            A sophisticated architecture combining semantic vector search and exact keyword matching, validated by an agentic workflow.
          </p>
        </div>

        {/* System Diagram */}
        <div className="relative max-w-4xl mx-auto">
          {/* Connecting Line */}
          <div className="absolute top-1/2 left-0 right-0 h-1 bg-gradient-to-r from-primary/10 via-primary to-primary/10 -translate-y-1/2 opacity-30 hidden md:block" />
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative z-10">
            {[
              { title: "User Query", icon: Bot, desc: "Intent analysis" },
              { title: "Hybrid Retrieval", icon: Search, desc: "BM25 + Semantic" },
              { title: "Agent Verification", icon: ShieldCheck, desc: "Guardrails & QA" },
              { title: "Grounded Output", icon: FileText, desc: "Answer + Citations" }
            ].map((node, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: idx * 0.15 }}
                className="flex flex-col items-center text-center group"
              >
                <div className="relative mb-6">
                  <div className="absolute inset-0 bg-primary/20 rounded-2xl blur-xl transition-opacity opacity-0 group-hover:opacity-100" />
                  <div className="size-20 glass rounded-2xl border border-border/50 flex items-center justify-center relative z-10 transition-transform group-hover:-translate-y-2">
                    <node.icon className="size-8 text-primary" />
                  </div>
                </div>
                <h4 className="font-semibold text-foreground mb-1">{node.title}</h4>
                <p className="text-sm text-muted-foreground">{node.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>

      </div>
    </section>
  )
}
