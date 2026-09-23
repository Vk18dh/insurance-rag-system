'use client'

import React, { useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Sphere, Cylinder, Box, RoundedBox } from '@react-three/drei'
import * as THREE from 'three'

interface AIBotProps {
  reducedMotion: boolean
  isHovered: boolean
}

export default function AIBot({ reducedMotion, isHovered }: AIBotProps) {
  const groupRef = useRef<THREE.Group>(null)
  const headRef = useRef<THREE.Group>(null)
  const { mouse } = useThree()
  
  useFrame((state) => {
    if (!groupRef.current || !headRef.current) return
    
    // Idle bobbing animation
    const time = state.clock.getElapsedTime()
    if (!reducedMotion) {
      groupRef.current.position.y = Math.sin(time * 2) * 0.1
    }

    // Eyes tracking cursor (parallax based on normalized mouse coords)
    if (!reducedMotion) {
      const targetX = (mouse.x * Math.PI) / 4
      const targetY = (mouse.y * Math.PI) / 6
      
      headRef.current.rotation.y = THREE.MathUtils.lerp(headRef.current.rotation.y, targetX, 0.1)
      headRef.current.rotation.x = THREE.MathUtils.lerp(headRef.current.rotation.x, -targetY, 0.1)
    } else {
      headRef.current.rotation.y = THREE.MathUtils.lerp(headRef.current.rotation.y, 0, 0.1)
      headRef.current.rotation.x = THREE.MathUtils.lerp(headRef.current.rotation.x, 0, 0.1)
    }
  })

  // Colors
  const bodyColor = "#0f172a"
  const accentColor = isHovered ? "#38bdf8" : "#0ea5e9"
  const eyeColor = isHovered ? "#bae6fd" : "#38bdf8"

  return (
    <group ref={groupRef} dispose={null}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[2, 5, 2]} intensity={2.5} color="#ffffff" />
      <directionalLight position={[-2, -5, -2]} intensity={0.5} color="#4fd1c5" />
      
      <group ref={headRef}>
        {/* Main Body (Rounded Capsule-like shape) */}
        <RoundedBox args={[1.2, 1.4, 1.2]} radius={0.5} smoothness={4}>
          <meshStandardMaterial 
            color={bodyColor} 
            roughness={0.4} 
            metalness={0.8}
            envMapIntensity={1}
          />
        </RoundedBox>

        {/* Visor/Screen Area */}
        <Box args={[0.9, 0.4, 1.05]} position={[0, 0.2, 0.1]} radius={0.1}>
          <meshStandardMaterial 
            color="#020617" 
            roughness={0.2}
            metalness={0.9}
          />
        </Box>

        {/* Eyes */}
        <group position={[0, 0.2, 0.65]}>
          <Sphere args={[0.08, 16, 16]} position={[-0.2, 0, 0]}>
            <meshBasicMaterial color={eyeColor} toneMapped={false} />
          </Sphere>
          <Sphere args={[0.08, 16, 16]} position={[0.2, 0, 0]}>
            <meshBasicMaterial color={eyeColor} toneMapped={false} />
          </Sphere>
        </group>

        {/* Antenna / Status Light */}
        <Cylinder args={[0.02, 0.02, 0.3]} position={[0, 0.8, 0]}>
          <meshStandardMaterial color="#334155" />
        </Cylinder>
        <Sphere args={[0.06, 16, 16]} position={[0, 0.95, 0]}>
          <meshBasicMaterial color={accentColor} toneMapped={false} />
        </Sphere>
      </group>

      {/* Floating Base Ring */}
      <Cylinder args={[0.6, 0.6, 0.05, 32]} position={[0, -0.9, 0]}>
        <meshBasicMaterial 
          color={accentColor}
          transparent
          opacity={0.2}
          side={THREE.DoubleSide}
        />
      </Cylinder>
    </group>
  )
}
