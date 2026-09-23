'use client'

import React, { useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import AssistantOrb, { AssistantState } from './assistant-orb'

export default function AssistantScene({ state }: { state: AssistantState }) {
  const [reducedMotion, setReducedMotion] = useState(false)
  
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReducedMotion(mediaQuery.matches)
    
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  return (
    <div className="w-full h-full relative">
      <Canvas
        camera={{ position: [0, 0, 3], fov: 45 }}
        gl={{ alpha: true, antialias: true }}
      >
        <AssistantOrb state={state} reducedMotion={reducedMotion} />
      </Canvas>
    </div>
  )
}
