<template>
  <div
    class="auth-layout"
    :style="shellStyle"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  >
    <canvas ref="canvasRef" class="bg-canvas"></canvas>
    <div class="bg-overlay"></div>
    <div class="auth-toolbar">
      <LocaleSwitcher />
    </div>
    <div class="content-wrapper">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import { useBrandingStore } from '@/stores/branding'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let animationFrameId: number
const brandingStore = useBrandingStore()

// Particle system parameters
const particles: Particle[] = []
const particleCount = 80 // Suitable density for standard screens
const connectionDistance = 150
const mouseRadius = 180

let mouse = {
  x: -1000,
  y: -1000
}

let speedMultiplier = 1
let colorIntensity = 1

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
}

const shellStyle = computed(() => ({
  backgroundImage: brandingStore.loginBackgroundUrl
    ? `linear-gradient(180deg, rgba(248, 250, 252, 0.84) 0%, rgba(241, 245, 249, 0.76) 100%), url("${brandingStore.loginBackgroundUrl}")`
    : 'linear-gradient(180deg, #f8fafc 0%, var(--sys-color-bg-base) 55%, #e9eef5 100%)',
  backgroundSize: brandingStore.loginBackgroundUrl ? 'cover' : undefined,
  backgroundPosition: brandingStore.loginBackgroundUrl ? 'center' : undefined,
}))

const handleMouseMove = (e: MouseEvent) => {
  mouse.x = e.clientX
  mouse.y = e.clientY
}

const handleMouseLeave = () => {
  mouse.x = -1000
  mouse.y = -1000
}

const initParticles = () => {
  if (!canvasRef.value) return
  particles.length = 0
  const width = canvasRef.value.width
  const height = canvasRef.value.height

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8,
      size: Math.random() * 2 + 1
    })
  }
}

const resizeCanvas = () => {
  if (!canvasRef.value) return
  canvasRef.value.width = window.innerWidth
  canvasRef.value.height = window.innerHeight
  initParticles()
}

const animate = () => {
  if (!canvasRef.value || !ctx) return
  
  // Contextual Speed & Intensity based on global class states
  const isActive = document.body.classList.contains('auth-active-state')
  const isLoading = document.body.classList.contains('auth-loading-state')
  
  const targetSpeed = isLoading ? 6 : (isActive ? 2.5 : 1)
  const targetIntensity = isLoading ? 1.8 : (isActive ? 1.3 : 1)
  
  // Smoothly interpolate towards target values
  speedMultiplier += (targetSpeed - speedMultiplier) * 0.05
  colorIntensity += (targetIntensity - colorIntensity) * 0.05

  ctx.clearRect(0, 0, canvasRef.value.width, canvasRef.value.height)

  // Update and draw particles
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i]
    
    // Move
    p.x += p.vx * speedMultiplier
    p.y += p.vy * speedMultiplier
    
    // Bounce off edges
    if (p.x < 0 || p.x > canvasRef.value.width) p.vx *= -1
    if (p.y < 0 || p.y > canvasRef.value.height) p.vy *= -1
    
    // Mouse interaction - gentle repel effect
    const dx = mouse.x - p.x
    const dy = mouse.y - p.y
    const distance = Math.sqrt(dx * dx + dy * dy)
    
    if (distance < mouseRadius) {
      const forceDirectionX = dx / distance
      const forceDirectionY = dy / distance
      const force = (mouseRadius - distance) / mouseRadius
      
      p.x -= forceDirectionX * force * 1.5
      p.y -= forceDirectionY * force * 1.5
    }

    // Draw particle
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(64, 158, 255, ${0.4 * colorIntensity})`
    ctx.fill()
    
    // Connect particles to each other
    for (let j = i + 1; j < particles.length; j++) {
      const p2 = particles[j]
      const pdx = p.x - p2.x
      const pdy = p.y - p2.y
      const pDistance = Math.sqrt(pdx * pdx + pdy * pdy)
      
      if (pDistance < connectionDistance) {
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(p2.x, p2.y)
        const opacity = (1 - (pDistance / connectionDistance)) * 0.25 * colorIntensity
        ctx.strokeStyle = `rgba(64, 158, 255, ${opacity})`
        ctx.lineWidth = 1
        ctx.stroke()
      }
    }
    
    // Connect particle to mouse
    if (distance < mouseRadius) {
      ctx.beginPath()
      ctx.moveTo(p.x, p.y)
      ctx.lineTo(mouse.x, mouse.y)
      const opacity = (1 - (distance / mouseRadius)) * 0.3 * colorIntensity
      ctx.strokeStyle = `rgba(64, 158, 255, ${opacity})`
      ctx.lineWidth = 1
      ctx.stroke()
    }
  }
  
  animationFrameId = requestAnimationFrame(animate)
}

onMounted(() => {
  brandingStore.initialize()
  if (canvasRef.value) {
    ctx = canvasRef.value.getContext('2d')
    window.addEventListener('resize', resizeCanvas)
    resizeCanvas()
    animate()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCanvas)
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.auth-layout {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #f8fafc 0%, $bg-body 55%, #e9eef5 100%);
}

.bg-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.42), transparent 35%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.1), var(--brand-login-shell-overlay, rgba(255, 255, 255, 0.12)));
}

.bg-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  pointer-events: none;
}

.content-wrapper {
  position: relative;
  z-index: 3;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
}

.auth-toolbar {
  position: absolute;
  top: 20px;
  right: 24px;
  z-index: 4;
  padding: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

@media (max-width: 720px) {
  .auth-toolbar {
    top: 14px;
    right: 14px;
  }
}
</style>
