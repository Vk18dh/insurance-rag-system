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
    <group ref={meshRef} onPointerDown={handlePointerDown} scale={1.3}>
      <ambientLight intensity={0.15} />
      {/* Cinematic side lighting */}
      <directionalLight position={[5, 2, 5]} intensity={2.0} color="#ffffff" />
      {/* Deep blue fill light from the bottom left */}
      <directionalLight position={[-5, -3, -5]} intensity={1.5} color="#0ea5e9" />
      {/* Cyan rim light from top right */}
      <spotLight position={[3, 5, -2]} intensity={2.5} color="#06b6d4" penumbra={1} />
      
      {/* Base Globe */}
      <Sphere ref={globeRef} args={[2, 64, 64]}>
        <meshStandardMaterial 
          map={colorMap}
          color="#ffffff"
          roughness={0.7}
          metalness={0.4}
        />
      </Sphere>

      {/* Atmosphere Glow */}
      <Sphere args={[2.2, 64, 64]}>
        <shaderMaterial
          vertexShader={`
            varying vec3 vNormal;
            void main() {
              vNormal = normalize(normalMatrix * normal);
              gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
          `}
          fragmentShader={`
            varying vec3 vNormal;
            void main() {
              // Calculate fresnel intensity based on normal and view angle
              float intensity = pow(max(0.0, 0.65 - dot(vNormal, vec3(0, 0, 1.0))), 4.0);
              // Deep cyan glow matching the UI
              gl_FragColor = vec4(0.02, 0.71, 0.83, 1.0) * intensity * 1.2;
            }
          `}
          blending={THREE.AdditiveBlending}
          side={THREE.BackSide}
          transparent={true}
          depthWrite={false}
        />
      </Sphere>
    </group>
  )
}
