"use client"

import React, { useRef, useMemo, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

const vertexShader = `
uniform float uTime;
uniform vec2 uMouse;
uniform float uActiveIntensity;

varying vec2 vUv;
varying float vElevation;

// Simplex 2D noise
vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
  + i.x + vec3(0.0, i1.x, 1.0 ));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
    dot(x12.zw,x12.zw)), 0.0);
  m = m*m ;
  m = m*m ;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vUv = uv;
  vec4 modelPosition = modelMatrix * vec4(position, 1.0);
  
  // Parallax based on mouse
  modelPosition.x += uMouse.x * 2.0;
  modelPosition.y += uMouse.y * 2.0;
  
  // Elevation via noise
  float elevation = snoise(vec2(modelPosition.x * 0.1, modelPosition.y * 0.1 + uTime * 0.15)) * 2.5;
  elevation += snoise(vec2(modelPosition.x * 0.2 - uTime * 0.1, modelPosition.y * 0.2)) * 1.0;
  
  modelPosition.z += elevation;
  vElevation = elevation;
  
  gl_Position = projectionMatrix * viewMatrix * modelPosition;
}
`;

const fragmentShader = `
uniform vec3 uColorNavy;
uniform vec3 uColorBlue;
uniform vec3 uColorCyan;
uniform vec3 uColorViolet;
uniform float uOpacity;
uniform float uActiveIntensity;

varying float vElevation;
varying vec2 vUv;

void main() {
  // Normalize elevation roughly to 0.0 -> 1.0
  float mixStrength = (vElevation + 3.0) / 6.0;
  mixStrength = clamp(mixStrength, 0.0, 1.0);
  
  // Gradient mapping
  vec3 color = mix(uColorNavy, uColorBlue, mixStrength);
  color = mix(color, uColorCyan, smoothstep(0.6, 1.0, mixStrength));
  color = mix(color, uColorViolet, smoothstep(0.8, 1.0, mixStrength) * 0.5);
  
  // Fade out near edges of the plane
  float alphaX = smoothstep(0.0, 0.2, vUv.x) * smoothstep(1.0, 0.8, vUv.x);
  float alphaY = smoothstep(0.0, 0.2, vUv.y) * smoothstep(1.0, 0.8, vUv.y);
  float alpha = alphaX * alphaY;
  
  gl_FragColor = vec4(color, alpha * uOpacity * uActiveIntensity);
}
`;

interface IntelligenceFieldProps {
  isActive: boolean;
  reducedMotion: boolean;
}

function IntelligenceField({ isActive, reducedMotion }: IntelligenceFieldProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const { size, viewport } = useThree();
  
  // Smoothly transition intensity
  const targetIntensity = isActive ? 0.35 : 1.0;
  const currentIntensity = useRef(targetIntensity);
  
  const targetMouse = useRef(new THREE.Vector2(0, 0));
  const currentMouse = useRef(new THREE.Vector2(0, 0));

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (reducedMotion) return;
      targetMouse.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      targetMouse.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [reducedMotion]);

  const uniforms = useMemo(() => ({
    uTime: { value: 0 },
    uMouse: { value: new THREE.Vector2(0, 0) },
    uColorNavy: { value: new THREE.Color('#0A1424') }, // Slightly lighter navy
    uColorBlue: { value: new THREE.Color('#1E90FF') },  // Brighter blue
    uColorCyan: { value: new THREE.Color('#00E5FF') },  // Brighter cyan
    uColorViolet: { value: new THREE.Color('#8B5CF6') }, // Brighter violet
    uOpacity: { value: 1.0 }, // Increased from 0.8
    uActiveIntensity: { value: 1.0 }
  }), []);

  useFrame((state, delta) => {
    if (!materialRef.current) return;
    
    if (!reducedMotion) {
      materialRef.current.uniforms.uTime.value += delta;
      
      // Interpolate mouse
      currentMouse.current.lerp(targetMouse.current, 0.05);
      materialRef.current.uniforms.uMouse.value.copy(currentMouse.current);
    }
    
    // Interpolate intensity based on empty vs active state
    // Boosted the active state minimum from 0.35 to 0.55 so it's not too dim
    const target = isActive ? 0.55 : 1.0;
    currentIntensity.current = THREE.MathUtils.lerp(currentIntensity.current, target, 0.05);
    materialRef.current.uniforms.uActiveIntensity.value = currentIntensity.current;
  });

  return (
    <mesh ref={meshRef} position={[0, -2, -5]} rotation={[-Math.PI * 0.35, 0, 0]}>
      {/* A large plane, lots of segments for smooth displacement */}
      <planeGeometry args={[40, 30, 100, 80]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
}

function DataParticles({ isActive, reducedMotion }: IntelligenceFieldProps) {
  const pointsRef = useRef<THREE.Points>(null);
  
  const targetIntensity = isActive ? 0.5 : 1.0; // Boosted
  const currentIntensity = useRef(targetIntensity);
  const targetMouse = useRef(new THREE.Vector2(0, 0));
  const currentMouse = useRef(new THREE.Vector2(0, 0));

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (reducedMotion) return;
      targetMouse.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      targetMouse.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [reducedMotion]);

  // Generate particles
  const particlesCount = 300;
  const [positions, phases] = useMemo(() => {
    const p = new Float32Array(particlesCount * 3);
    const ph = new Float32Array(particlesCount);
    for (let i = 0; i < particlesCount; i++) {
      p[i * 3 + 0] = (Math.random() - 0.5) * 40;
      p[i * 3 + 1] = (Math.random() - 0.5) * 30;
      p[i * 3 + 2] = (Math.random() - 0.5) * 10 - 2;
      ph[i] = Math.random() * Math.PI * 2;
    }
    return [p, ph];
  }, [particlesCount]);

  useFrame((state, delta) => {
    if (!pointsRef.current) return;
    const material = pointsRef.current.material as THREE.PointsMaterial;
    
    currentIntensity.current = THREE.MathUtils.lerp(currentIntensity.current, targetIntensity, 0.05);
    material.opacity = currentIntensity.current * 0.7; // increased max opacity

    if (!reducedMotion) {
      currentMouse.current.lerp(targetMouse.current, 0.05);
      pointsRef.current.rotation.y = currentMouse.current.x * 0.05;
      pointsRef.current.rotation.x = -currentMouse.current.y * 0.05;
      
      const positionsAttr = pointsRef.current.geometry.attributes.position;
      const array = positionsAttr.array as Float32Array;
      for (let i = 0; i < particlesCount; i++) {
        // Subtle drift
        array[i * 3 + 1] += Math.sin(state.clock.elapsedTime * 0.5 + phases[i]) * 0.005;
      }
      positionsAttr.needsUpdate = true;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={particlesCount}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.06} // slightly larger
        color="#00E5FF" // brighter cyan
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        opacity={0.7}
      />
    </points>
  );
}

export function Chat3DBackground({ isActive }: { isActive: boolean }) {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return (
    <div className="absolute inset-0 pointer-events-none z-0">
      <Canvas
        camera={{ position: [0, 0, 10], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      >
        <IntelligenceField isActive={isActive} reducedMotion={reducedMotion} />
        <DataParticles isActive={isActive} reducedMotion={reducedMotion} />
      </Canvas>
      {/* Overlay gradient to ensure text readability - reduced opacity significantly to let colors shine */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#050A12]/40 via-transparent to-[#050A12]/40 pointer-events-none mix-blend-overlay" />
      <div className="absolute inset-0 bg-[#050A12]/10 pointer-events-none" />
    </div>
  );
}
