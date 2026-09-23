"use client"

import React, { useRef, useState, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import AIBot from './ai-bot'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'motion/react'

export default function AIBotScene() {
  const router = useRouter()
  const [reducedMotion, setReducedMotion] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReducedMotion(mediaQuery.matches)
    
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  return (
    <div 
      className="fixed bottom-6 right-6 z-50 flex flex-col items-end pointer-events-none"
    >
      <AnimatePresence>
        {isHovered && (
          <motion.div 
            initial={{ opacity: 0, y: 10, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.9 }}
            className="mb-2 mr-4 px-4 py-2 bg-card border border-border rounded-2xl rounded-br-sm shadow-xl glass pointer-events-auto cursor-pointer"
            onClick={() => router.push('/chat')}
          >
            <p className="text-sm font-medium text-foreground">Need help?</p>
          </motion.div>
        )}
      </AnimatePresence>

      <div 
        className="w-24 h-24 md:w-32 md:h-32 pointer-events-auto cursor-pointer transition-transform hover:scale-110"
        onPointerEnter={() => setIsHovered(true)}
        onPointerLeave={() => setIsHovered(false)}
        onClick={() => router.push('/chat')}
      >
        <Canvas
          camera={{ position: [0, 0, 4], fov: 45 }}
          gl={{ alpha: true, antialias: true }}
          dpr={[1, 2]}
        >
          <AIBot reducedMotion={reducedMotion} isHovered={isHovered} />
        </Canvas>
      </div>
    </div>
  )
}
