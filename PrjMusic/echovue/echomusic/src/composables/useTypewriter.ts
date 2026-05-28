import { ref, onMounted, onUnmounted } from 'vue'

export function useTypewriter(text: string, options: {
  speed?: number
  delay?: number
  loop?: boolean
  loopDelay?: number
} = {}) {
  const { speed = 60, delay = 0, loop = false, loopDelay = 3000 } = options
  const displayText = ref('')
  const isTyping = ref(false)
  const isDone = ref(false)

  let timeoutIds: ReturnType<typeof setTimeout>[] = []
  let currentIndex = 0

  function clearAllTimeouts() {
    timeoutIds.forEach(id => clearTimeout(id))
    timeoutIds = []
  }

  function typeNext() {
    if (currentIndex < text.length) {
      displayText.value += text[currentIndex]
      currentIndex++
      isTyping.value = true
      const id = setTimeout(typeNext, speed)
      timeoutIds.push(id)
    } else {
      isTyping.value = false
      isDone.value = true
      if (loop) {
        const id = setTimeout(() => {
          displayText.value = ''
          currentIndex = 0
          isDone.value = false
          typeNext()
        }, loopDelay)
        timeoutIds.push(id)
      }
    }
  }

  function start() {
    clearAllTimeouts()
    displayText.value = ''
    currentIndex = 0
    isDone.value = false
    const id = setTimeout(typeNext, delay)
    timeoutIds.push(id)
  }

  function stop() {
    clearAllTimeouts()
    isTyping.value = false
  }

  onMounted(() => {
    start()
  })

  onUnmounted(() => {
    clearAllTimeouts()
  })

  return { displayText, isTyping, isDone, start, stop }
}
