"use client"

import React, { useRef } from 'react'
import { motion, useScroll, useTransform, useMotionValueEvent } from 'motion/react'
import { Search, Database, ShieldCheck, Zap } from 'lucide-react'

export function RagStory() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end center"]
  })

  // We want to map scrollYProgress (0 to 1) to active step (0 to 3)
  const activeStep = useTransform(scrollYProgress, (v) => {
    if (v < 0.25) return 0
    if (v < 0.5) return 1
    if (v < 0.75) return 2
    return 3
  })

  const steps = [
    {
      title: "Query Understanding",
      description: "Your question is analyzed for intent, extracting key insurance concepts to form a precise search strategy.",
      icon: Search,
      color: "text-primary"
    },
    {
      title: "Intelligent Retrieval",
      description: "The system scans the official policy documents using hybrid semantic and keyword search to find highly relevant evidence.",
      icon: Database,
      color: "text-accent"
    },
    {
      title: "Fact Verification",
      description: "Retrieved evidence is rigorously verified against your query to prevent hallucinations and ensure relevance.",
      icon: ShieldCheck,
      color: "text-success"
    },
    {
      title: "Grounded Response",
      description: "You receive a synthesized, accurate answer backed entirely by the provided source documents.",
      icon: Zap,
      color: "text-foreground"
    }
  ]

  const [activeIndex, setActiveIndex] = React.useState(0)

  useMotionValueEvent(activeStep, "change", (latest) => {
    setActiveIndex(latest)
  })
  
  const ActiveIcon = steps[activeIndex]?.icon || Search

  return (
    <section id="how-it-works" ref={containerRef} className="relative py-32 bg-card/30">
      <div className="container max-w-6xl mx-auto px-4">
        
        <div className="text-center mb-24 space-y-4">
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight">How Intelligence Works</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            A transparent agentic pipeline that prioritizes accuracy and verifiability over simple generation.
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-16 items-start">
          
          {/* Left: Sticky Visualization */}
          <div className="w-full lg:w-1/2 sticky top-32 h-[500px] flex items-center justify-center">
            <div className="relative w-full max-w-md aspect-square bg-card/50 border border-border/50 rounded-full flex items-center justify-center">
              {/* Central Core */}
              <div className="absolute inset-0 rounded-full border border-dashed border-border animate-[spin_60s_linear_infinite]" />
              <div className="absolute inset-10 rounded-full border border-primary/20 bg-primary/5 backdrop-blur-sm" />
              
              {/* Dynamic Center Node */}
              <motion.div 
                className="relative z-10 size-32 rounded-full glass border border-primary/30 flex items-center justify-center shadow-2xl transition-colors duration-500"
              >
                {/* Render the icon based on active step */}
                <motion.div
                  key={activeIndex}
                  initial={{ opacity: 0, scale: 0.5, rotate: -45 }}
                  animate={{ opacity: 1, scale: 1, rotate: 0 }}
                  transition={{ duration: 0.5, type: "spring", stiffness: 200 }}
                >
                  <ActiveIcon className={`size-12 ${steps[activeIndex]?.color}`} />
                </motion.div>
              </motion.div>
            </div>
          </div>

          {/* Right: Scrollable Steps */}
          <div className="w-full lg:w-1/2 flex flex-col gap-32 py-32">
            {steps.map((step, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0.3, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: false, margin: "-50% 0px -50% 0px" }}
                transition={{ duration: 0.5 }}
                className="relative flex gap-6"
              >
                <div className="flex flex-col items-center">
                  <div className={`flex size-14 shrink-0 items-center justify-center rounded-2xl border bg-card shadow-lg ${step.color}`}>
                    <step.icon className="size-6" />
                  </div>
                  {index !== steps.length - 1 && (
                    <div className="w-[1px] h-full min-h-[100px] bg-border mt-4" />
                  )}
                </div>
                
                <div className="pt-2 pb-12">
                  <span className="text-sm font-semibold tracking-widest text-muted-foreground uppercase mb-2 block">
                    Step 0{index + 1}
                  </span>
                  <h3 className="text-2xl font-bold mb-4">{step.title}</h3>
                  <p className="text-muted-foreground text-lg leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>

        </div>
      </div>
    </section>
  )
}
