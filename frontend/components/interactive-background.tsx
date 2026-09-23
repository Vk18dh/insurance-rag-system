"use client"

import React, { useEffect, useRef } from "react"

export function InteractiveBackground({ children }: { children: React.ReactNode }) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Check if user prefers reduced motion
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    
    if (mediaQuery.matches) {
      return // Disable interactive cursor background for reduced motion
    }

    const updateMousePosition = (ev: MouseEvent) => {
      if (!containerRef.current) return
      
      // Use requestAnimationFrame for smooth, non-blocking updates
      requestAnimationFrame(() => {
        if (!containerRef.current) return
        containerRef.current.style.setProperty("--mouse-x", `${ev.clientX}px`)
        containerRef.current.style.setProperty("--mouse-y", `${ev.clientY}px`)
      })
    }

    window.addEventListener("mousemove", updateMousePosition)

    return () => {
      window.removeEventListener("mousemove", updateMousePosition)
    }
  }, [])

  return (
    <div 
      ref={containerRef} 
      className="relative min-h-screen w-full flex flex-col cursor-glow overflow-x-hidden"
    >
      {/* Base deep navy layer + radial gradients are handled in globals.css body/cursor-glow */}
      <div className="pointer-events-none fixed inset-0 subtle-grid-bg opacity-100 z-0 mix-blend-screen" aria-hidden="true" />

      <div className="relative z-10 flex flex-col flex-1">
        {children}
      </div>
    </div>
  )
}
