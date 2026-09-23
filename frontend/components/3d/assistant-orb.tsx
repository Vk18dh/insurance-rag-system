'use client'

import React, { useRef, useMemo } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Sphere, MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'

export type AssistantState = 'IDLE' | 'SUBMITTING' | 'PROCESSING' | 'ANSWER_RECEIVED' | 'SAFE_REFUSAL' | 'AMBIGUOUS' | 'GUARDRAIL_BLOCKED' | 'PROVIDER_FAILURE' | 'NETWORK_ERROR' | 'TIMEOUT'

interface AssistantOrbProps {
  state: AssistantState
  reducedMotion?: boolean
}

export default function AssistantOrb({ state, reducedMotion = false }: AssistantOrbProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  // Define visual properties based on state
  const visualConfig = useMemo(() => {
    switch (state) {
      case 'PROCESSING':
      case 'SUBMITTING':
        return { color: '#38bdf8', distort: 0.6, speed: 4, scale: 1.2 }
      case 'ANSWER_RECEIVED':
        return { color: '#4ade80', distort: 0.2, speed: 2, scale: 1.1 }
      case 'SAFE_REFUSAL':
      case 'AMBIGUOUS':
        return { color: '#fbbf24', distort: 0.3, speed: 1.5, scale: 1 }
      case 'GUARDRAIL_BLOCKED':
      case 'PROVIDER_FAILURE':
      case 'NETWORK_ERROR':
      case 'TIMEOUT':
        return { color: '#ef4444', distort: 0.1, speed: 1, scale: 0.9 }
      case 'IDLE':
      default:
        return { color: '#0ea5e9', distort: 0.3, speed: 1.5, scale: 1 }
    }
  }, [state])

  const targetScale = useRef(visualConfig.scale)
  const currentScale = useRef(visualConfig.scale)

  useFrame((state, delta) => {
    if (!meshRef.current) return
    
    // Smoothly animate scale transitions
    if (!reducedMotion) {
      targetScale.current = visualConfig.scale
      currentScale.current = THREE.MathUtils.lerp(currentScale.current, targetScale.current, 0.1)
      meshRef.current.scale.setScalar(currentScale.current)
      
      // Idle slow rotation
      meshRef.current.rotation.y += delta * 0.2
      meshRef.current.rotation.x += delta * 0.1
    } else {
      meshRef.current.scale.setScalar(visualConfig.scale)
    }
  })

  return (
    <group scale={1.2}>
      <ambientLight intensity={1.5} />
      <directionalLight position={[5, 5, 5]} intensity={3} color={visualConfig.color} />
      <directionalLight position={[-5, -5, -5]} intensity={1} color="#ffffff" />
      
      <group ref={meshRef}>
        {/* Core */}
        <Sphere args={[0.8, 64, 64]}>
          <MeshDistortMaterial
            color={visualConfig.color}
            envMapIntensity={2}
            clearcoat={1}
            clearcoatRoughness={0.1}
            metalness={0.9}
            roughness={0.1}
            distort={reducedMotion ? 0 : visualConfig.distort * 1.5}
            speed={reducedMotion ? 0 : visualConfig.speed * 1.2}
          />
        </Sphere>

        {/* Wireframe Shell */}
        <Sphere args={[1.05, 32, 32]}>
          <meshBasicMaterial 
            color={visualConfig.color} 
            wireframe 
            transparent 
            opacity={0.3} 
            blending={THREE.AdditiveBlending}
          />
        </Sphere>
      </group>
      
      {/* Outer Halo */}
      <Sphere args={[1.3, 32, 32]}>
        <meshBasicMaterial 
          color={visualConfig.color} 
          transparent 
          opacity={0.15} 
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>
    </group>
  )
}
