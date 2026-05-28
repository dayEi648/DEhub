import { ref, onMounted, onUnmounted, type Ref } from 'vue'
import gsap from 'gsap'

export function useTilt(elementRef: Ref<HTMLElement | null>, options: {
  max?: number
  scale?: number
  speed?: number
  glare?: boolean
} = {}) {
  const { max = 8, scale = 1.02, speed = 0.4 } = options
  const isHovered = ref(false)

  let rafId: number | null = null

  function handleMouseMove(e: MouseEvent) {
    const el = elementRef.value
    if (!el) return

    const rect = el.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const centerX = rect.width / 2
    const centerY = rect.height / 2

    const rotateX = ((y - centerY) / centerY) * -max
    const rotateY = ((x - centerX) / centerX) * max

    if (rafId) cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(() => {
      gsap.to(el, {
        rotateX,
        rotateY,
        scale,
        duration: speed,
        ease: 'power2.out',
        transformPerspective: 1000,
        transformOrigin: 'center center'
      })
    })
  }

  function handleMouseEnter() {
    isHovered.value = true
  }

  function handleMouseLeave() {
    isHovered.value = false
    const el = elementRef.value
    if (!el) return
    gsap.to(el, {
      rotateX: 0,
      rotateY: 0,
      scale: 1,
      duration: speed * 1.5,
      ease: 'elastic.out(1, 0.5)'
    })
  }

  onMounted(() => {
    const el = elementRef.value
    if (!el) return
    el.addEventListener('mousemove', handleMouseMove)
    el.addEventListener('mouseenter', handleMouseEnter)
    el.addEventListener('mouseleave', handleMouseLeave)
    el.style.transformStyle = 'preserve-3d'
  })

  onUnmounted(() => {
    const el = elementRef.value
    if (!el) return
    el.removeEventListener('mousemove', handleMouseMove)
    el.removeEventListener('mouseenter', handleMouseEnter)
    el.removeEventListener('mouseleave', handleMouseLeave)
    if (rafId) cancelAnimationFrame(rafId)
  })

  return { isHovered }
}
