'use client'

import React, { useEffect, useState, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { Html, useProgress } from '@react-three/drei'
import Earth from './earth'

function Loader() {
  const { progress } = useProgress()
  return <Html center><div className="text-sm font-mono text-muted-foreground">{progress.toFixed(0)}% loaded</div></Html>
}

export default function EarthScene() {
  const [reducedMotion, setReducedMotion] = useState(false)
  
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReducedMotion(mediaQuery.matches)
    
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  return (
    <div className="w-full h-full relative cursor-grab active:cursor-grabbing">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 45 }}
        gl={{ alpha: true, antialias: true }}
        dpr={[1, 2]} // Optimize for mobile retina
      >
        <Suspense fallback={<Loader />}>
          <Earth reducedMotion={reducedMotion} />
        </Suspense>
      </Canvas>
    </div>
  )
}
