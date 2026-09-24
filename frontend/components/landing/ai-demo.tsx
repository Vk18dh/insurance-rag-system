"use client"

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Sparkles, ArrowRight, User } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

const DEMO_CONVERSATION = [
  { role: "user", content: "What is the surrender value of my policy?" },
  { role: "assistant", content: "Based on the policy terms, the Guaranteed Surrender Value is available after you have paid premiums for at least two full years. It is calculated as a percentage of total premiums paid minus any extra premiums and rider premiums. For example, if you surrender in year 3, you will receive 30% of the total premiums paid." }
]

export function AiDemo() {
  const [messages, setMessages] = useState<typeof DEMO_CONVERSATION>([])
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    // Sequence the demo
    const timer1 = setTimeout(() => {
      setMessages([DEMO_CONVERSATION[0]])
      setIsTyping(true)
    }, 1000)

    const timer2 = setTimeout(() => {
      setIsTyping(false)
      setMessages(DEMO_CONVERSATION)
    }, 3500)

    return () => {
      clearTimeout(timer1)
      clearTimeout(timer2)
    }
  }, [])

  return (
    <section className="relative py-32 bg-background z-20">
      <div className="container max-w-5xl mx-auto px-4">
        <div className="flex flex-col lg:flex-row gap-16 items-center">
          
          {/* Left: Text Context */}
          <div className="w-full lg:w-1/2 space-y-8">
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight leading-tight">
              A smarter way to explore policies.
            </h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              Experience the AI Assistant designed specifically for insurance intelligence.
              It understands complex policy language, handles ambiguous questions, and provides clear, grounded answers instantly.
            </p>
            
            <div className="pt-4">
              <Link href="/chat">
                <Button size="lg" className="rounded-full px-8 shadow-lg shadow-primary/20 hover:-translate-y-1 transition-transform">
                  Try the Assistant
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Right: Interactive UI Demo */}
          <div className="w-full lg:w-1/2">
            <div className="glass rounded-3xl border border-border/50 shadow-2xl overflow-hidden bg-card/60 relative">
              {/* Fake UI Header */}
              <div className="flex items-center gap-3 p-4 border-b border-border/50 bg-background/50">
                <div className="size-3 rounded-full bg-destructive/80" />
                <div className="size-3 rounded-full bg-amber-500/80" />
                <div className="size-3 rounded-full bg-success/80" />
                <div className="ml-4 text-xs font-medium text-muted-foreground flex items-center gap-2">
                  <Sparkles className="size-3 text-primary" />
                  Aegis AI Assistant
                </div>
              </div>

              {/* Chat Area */}
              <div className="p-6 h-[350px] flex flex-col gap-6 overflow-hidden">
                <AnimatePresence>
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ type: "spring", stiffness: 400, damping: 25 }}
                      className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                      <div className={`shrink-0 size-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-secondary' : 'bg-primary/20 text-primary'}`}>
                        {msg.role === 'user' ? <User className="size-4" /> : <Sparkles className="size-4" />}
                      </div>
                      <div className={`p-4 rounded-2xl max-w-[80%] text-sm leading-relaxed ${
                        msg.role === 'user' 
                          ? 'bg-secondary text-secondary-foreground rounded-tr-sm' 
                          : 'bg-card border border-border/50 text-foreground rounded-tl-sm'
                      }`}>
                        {msg.content}
                      </div>
                    </motion.div>
                  ))}
                  
                  {isTyping && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      className="flex gap-4"
                    >
                      <div className="shrink-0 size-8 rounded-full bg-primary/20 text-primary flex items-center justify-center">
                        <Sparkles className="size-4" />
                      </div>
                      <div className="p-4 rounded-2xl bg-card border border-border/50 rounded-tl-sm flex items-center gap-2">
                        <div className="flex gap-1">
                          <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0 }} className="size-2 rounded-full bg-primary" />
                          <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="size-2 rounded-full bg-primary" />
                          <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="size-2 rounded-full bg-primary" />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Fake Input Area */}
              <div className="p-4 border-t border-border/50 bg-background/30">
                <div className="flex items-center gap-2 bg-background border border-border/50 rounded-full px-4 py-2">
                  <span className="text-sm text-muted-foreground">Ask follow-up question...</span>
                  <div className="ml-auto size-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <ArrowRight className="size-4 text-primary" />
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
