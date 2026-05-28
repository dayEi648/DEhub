import { ref, onMounted, onUnmounted } from 'vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

export function useCountUp(
  targetValue: number,
  options: {
    duration?: number
    decimals?: number
    suffix?: string
    prefix?: string
    scrollTrigger?: boolean
    triggerRef?: HTMLElement | null
  } = {}
) {
  const {
    duration = 2,
    decimals = 0,
    suffix = '',
    prefix = '',
    scrollTrigger: useScrollTrigger = true,
    triggerRef = null
  } = options

  const displayValue = ref(`${prefix}${decimals > 0 ? '0.00' : '0'}${suffix}`)
  const hasAnimated = ref(false)

  let triggerInstance: ScrollTrigger | null = null

  function animate() {
    if (hasAnimated.value) return
    hasAnimated.value = true

    const obj = { value: 0 }
    gsap.to(obj, {
      value: targetValue,
      duration,
      ease: 'power2.out',
      onUpdate: () => {
        const val = decimals > 0
          ? obj.value.toFixed(decimals)
          : Math.round(obj.value).toString()
        displayValue.value = `${prefix}${val}${suffix}`
      }
    })
  }

  onMounted(() => {
    if (useScrollTrigger && triggerRef) {
      triggerInstance = ScrollTrigger.create({
        trigger: triggerRef,
        start: 'top 85%',
        onEnter: animate,
        once: true
      })
    } else {
      animate()
    }
  })

  onUnmounted(() => {
    if (triggerInstance) {
      triggerInstance.kill()
    }
  })

  return { displayValue, animate }
}
