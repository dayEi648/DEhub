<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)

interface Particle {
  x: number
  y: number
  baseY: number
  size: number
  speedX: number
  speedY: number
  opacity: number
  color: string
  phase: number
  amplitude: number
  frequency: number
}

let animationId: number | null = null
let particles: Particle[] = []
let mouseX = -1000
let mouseY = -1000
let ctx: CanvasRenderingContext2D | null = null
let w = 0
let h = 0
let dpr = 1

const PARTICLE_COUNT = 80
const CONNECTION_DISTANCE = 120
const MOUSE_RADIUS = 150

const colors = [
  '107, 70, 193',   // purple
  '236, 72, 153',   // pink
  '6, 182, 212',    // cyan
  '139, 92, 246',   // violet
]

function initParticles() {
  particles = []
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const x = Math.random() * w
    const baseY = Math.random() * h
    particles.push({
      x,
      y: baseY,
      baseY,
      size: Math.random() * 2 + 0.5,
      speedX: (Math.random() - 0.5) * 0.3,
      speedY: (Math.random() - 0.5) * 0.1,
      opacity: Math.random() * 0.5 + 0.2,
      color: colors[Math.floor(Math.random() * colors.length)]!,
      phase: Math.random() * Math.PI * 2,
      amplitude: Math.random() * 30 + 10,
      frequency: Math.random() * 0.002 + 0.001
    })
  }
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const parent = canvas.parentElement
  if (!parent) return

  dpr = window.devicePixelRatio || 1
  w = parent.clientWidth
  h = parent.clientHeight

  canvas.width = w * dpr
  canvas.height = h * dpr
  canvas.style.width = w + 'px'
  canvas.style.height = h + 'px'

  ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.scale(dpr, dpr)
  }

  initParticles()
}

function draw() {
  if (!ctx) return
  ctx.clearRect(0, 0, w, h)

  const time = Date.now()

  // Update and draw particles
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i]!

    // Wave motion
    p.y = p.baseY + Math.sin(time * p.frequency + p.phase) * p.amplitude
    p.x += p.speedX
    p.phase += 0.01

    // Mouse interaction - repel
    const dx = p.x - mouseX
    const dy = p.y - mouseY
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist < MOUSE_RADIUS) {
      const force = (MOUSE_RADIUS - dist) / MOUSE_RADIUS
      p.x += (dx / dist) * force * 2
      p.y += (dy / dist) * force * 2
    }

    // Wrap around
    if (p.x < 0) p.x = w
    if (p.x > w) p.x = 0
    if (p.baseY < 0) p.baseY = h
    if (p.baseY > h) p.baseY = 0

    // Draw particle
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${p.color}, ${p.opacity})`
    ctx.fill()
  }

  // Draw connections
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const p1 = particles[i]!
      const p2 = particles[j]!
      const dx = p1.x - p2.x
      const dy = p1.y - p2.y
      const dist = Math.sqrt(dx * dx + dy * dy)

      if (dist < CONNECTION_DISTANCE) {
        const opacity = (1 - dist / CONNECTION_DISTANCE) * 0.15
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.strokeStyle = `rgba(107, 70, 193, ${opacity})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
  }

  animationId = requestAnimationFrame(draw)
}

function handleMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  mouseX = e.clientX - rect.left
  mouseY = e.clientY - rect.top
}

function handleMouseLeave() {
  mouseX = -1000
  mouseY = -1000
}

function handleVisibilityChange() {
  if (document.hidden) {
    if (animationId) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
  } else {
    if (!animationId) {
      draw()
    }
  }
}

onMounted(() => {
  resize()
  draw()

  window.addEventListener('resize', resize)
  document.addEventListener('visibilitychange', handleVisibilityChange)

  const canvas = canvasRef.value
  if (canvas) {
    canvas.addEventListener('mousemove', handleMouseMove)
    canvas.addEventListener('mouseleave', handleMouseLeave)
  }
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  window.removeEventListener('resize', resize)
  document.removeEventListener('visibilitychange', handleVisibilityChange)

  const canvas = canvasRef.value
  if (canvas) {
    canvas.removeEventListener('mousemove', handleMouseMove)
    canvas.removeEventListener('mouseleave', handleMouseLeave)
  }
})
</script>

<template>
  <canvas
    ref="canvasRef"
    class="wave-background"
  />
</template>

<style scoped src="./WaveBackground.css"></style>
