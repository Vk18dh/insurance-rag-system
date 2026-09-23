'use client'

import React, { useRef, useState, useMemo, useEffect } from 'react'
import { useFrame, useThree, useLoader } from '@react-three/fiber'
import { Sphere, Line } from '@react-three/drei'
import * as THREE from 'three'
import { useRouter } from 'next/navigation'

interface EarthProps {
  reducedMotion: boolean
}

// Procedural texture for stylized continents using noise could be complex, 
// so we'll use a stylized wireframe / point approach or just a solid shader.
export default function Earth({ reducedMotion }: EarthProps) {
  const meshRef = useRef<THREE.Group>(null)
  const globeRef = useRef<THREE.Mesh>(null)
  
  const { size, viewport, camera, gl } = useThree()
  
  // Interaction states
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [dragDelta, setDragDelta] = useState({ x: 0, y: 0 })
  
  const rotationVelocity = useRef({ x: 0, y: reducedMotion ? 0 : 0.001 })
  const targetRotation = useRef({ x: 0, y: 0 })
  
  // Mouse position for parallax
  const mouse = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const handlePointerMove = (e: PointerEvent) => {
      // Normalize mouse to -1 to 1
      mouse.current.x = (e.clientX / window.innerWidth) * 2 - 1
      mouse.current.y = -(e.clientY / window.innerHeight) * 2 + 1
      
      if (isDragging) {
        setDragDelta({
          x: e.clientX - dragStart.x,
          y: e.clientY - dragStart.y
        })
      }
    }

    const handlePointerUp = () => {
      if (isDragging) {
        setIsDragging(false)
        // Add momentum based on last drag delta
        rotationVelocity.current.x = dragDelta.y * 0.0005
        rotationVelocity.current.y = dragDelta.x * 0.0005
      }
    }

    window.addEventListener('pointermove', handlePointerMove)
    window.addEventListener('pointerup', handlePointerUp)
    
    return () => {
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerup', handlePointerUp)
    }
  }, [isDragging, dragStart, dragDelta])

  const handlePointerDown = (e: any) => {
    e.stopPropagation()
    setIsDragging(true)
    setDragStart({ x: e.clientX, y: e.clientY })
    setDragDelta({ x: 0, y: 0 })
    rotationVelocity.current = { x: 0, y: 0 }
  }

  useFrame((state, delta) => {
    if (!meshRef.current || !globeRef.current) return

    // Idle rotation
    if (!reducedMotion && !isDragging) {
      targetRotation.current.y += rotationVelocity.current.y
      targetRotation.current.x += rotationVelocity.current.x
      
      // Gradually restore default idle velocity if not dragging
      rotationVelocity.current.x = THREE.MathUtils.lerp(rotationVelocity.current.x, 0, 0.05)
      rotationVelocity.current.y = THREE.MathUtils.lerp(rotationVelocity.current.y, 0.001, 0.02)
    }

    if (isDragging && !reducedMotion) {
      targetRotation.current.y += dragDelta.x * 0.0005
      targetRotation.current.x += dragDelta.y * 0.0005
    }

    // Apply rotation
    meshRef.current.rotation.y = targetRotation.current.y
    meshRef.current.rotation.x = targetRotation.current.x

    // Mouse parallax (subtle tilt towards cursor)
    if (!reducedMotion && !isDragging) {
      const targetParallaxX = mouse.current.y * 0.2
      const targetParallaxY = mouse.current.x * 0.2
      
      meshRef.current.rotation.x = THREE.MathUtils.lerp(meshRef.current.rotation.x, targetRotation.current.x + targetParallaxX, 0.05)
      meshRef.current.rotation.y = THREE.MathUtils.lerp(meshRef.current.rotation.y, targetRotation.current.y + targetParallaxY, 0.05)
    }
  })

  // Load Earth texture
  const colorMap = useLoader(THREE.TextureLoader, '/textures/earth.jpg')

  return (
    <group ref={meshRef} onPointerDown={handlePointerDown} scale={1.2}>
      <ambientLight intensity={0.2} />
      <directionalLight position={[5, 3, 5]} intensity={2.5} color="#ffffff" />
      <directionalLight position={[-5, -3, -5]} intensity={0.5} color="#4fd1c5" />
      
      {/* Base Globe */}
      <Sphere ref={globeRef} args={[2, 64, 64]}>
        <meshStandardMaterial 
          map={colorMap}
          color="#a0c0d0"
          roughness={0.6}
          metalness={0.1}
        />
      </Sphere>

      {/* Atmosphere Glow */}
      <Sphere args={[2.08, 64, 64]}>
        <meshLambertMaterial 
          color="#38bdf8"
          transparent={true}
          opacity={0.15}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>
      
      {/* Outer Halo */}
      <Sphere args={[2.2, 64, 64]}>
        <meshBasicMaterial 
          color="#0ea5e9"
          transparent={true}
          opacity={0.05}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </Sphere>
      
      <FloatingNodes reducedMotion={reducedMotion} />
    </group>
  )
}

function FloatingNodes({ reducedMotion }: { reducedMotion: boolean }) {
  const router = useRouter()
  const nodes = useMemo(() => [
    { id: 'life', label: 'Life Protection', lat: 20, lng: 40, query: 'What does the policy say about life protection benefits?' },
    { id: 'savings', label: 'Savings', lat: -20, lng: 80, query: 'What are the savings and investment benefits?' },
    { id: 'retirement', label: 'Retirement', lat: 40, lng: -40, query: 'What are the retirement benefits?' },
    { id: 'family', label: 'Family Protection', lat: -30, lng: -60, query: 'How does the policy protect my family?' },
    { id: 'knowledge', label: 'Policy Knowledge', lat: 10, lng: 120, query: 'What are the general terms of this policy?' },
  ], [])

  const handleNodeClick = (query: string, e: any) => {
    e.stopPropagation()
    // Open chat and populate query via URL param or context
    // Since we can't easily pass context from here without an app provider, we'll use URL params.
    router.push(`/?q=${encodeURIComponent(query)}`)
  }

  const [hovered, setHovered] = useState<string | null>(null)

  return (
    <group>
      {nodes.map((node) => {
        // Convert lat/lng to 3D Cartesian coordinates
        const phi = (90 - node.lat) * (Math.PI / 180)
        const theta = (node.lng + 180) * (Math.PI / 180)
        const r = 2.4 // Orbit radius

        const x = -(r * Math.sin(phi) * Math.cos(theta))
        const z = r * Math.sin(phi) * Math.sin(theta)
        const y = r * Math.cos(phi)

        const isHovered = hovered === node.id

        return (
          <group 
            key={node.id} 
            position={[x, y, z]} 
            onPointerOver={(e) => { e.stopPropagation(); setHovered(node.id) }}
            onPointerOut={(e) => { e.stopPropagation(); setHovered(null) }}
            onClick={(e) => handleNodeClick(node.query, e)}
          >
            {/* The interactive node indicator */}
            <Sphere args={[isHovered ? 0.08 : 0.05, 16, 16]}>
              <meshBasicMaterial color={isHovered ? "#38bdf8" : "#94a3b8"} />
            </Sphere>
            
            {/* Outer glow */}
            <Sphere args={[0.15, 16, 16]}>
              <meshBasicMaterial 
                color="#0ea5e9" 
                transparent 
                opacity={isHovered ? 0.4 : 0.1} 
                blending={THREE.AdditiveBlending}
              />
            </Sphere>

            {/* Connecting line to earth */}
            <Line
              points={[[0, 0, 0], [-x * 0.15, -y * 0.15, -z * 0.15]]}
              color={isHovered ? "#38bdf8" : "#475569"}
              lineWidth={1}
              transparent
              opacity={0.5}
            />
          </group>
        )
      })}
    </group>
  )
}
