import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'warning'
  duration: number
}

export const useUiStore = defineStore('ui', () => {
  const isMobileMenuOpen = ref(false)
  const isChatSidebarCollapsed = ref(false)
  const globalLoading = ref(false)
  const toasts = ref<ToastItem[]>([])
  let toastId = 0

  function setLoading(value: boolean) {
    globalLoading.value = value
  }

  function showToast(message: string, type: 'success' | 'error' | 'warning' = 'success', duration = 3000) {
    const id = ++toastId
    toasts.value.push({ id, message, type, duration })
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function removeToast(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function toggleMobileMenu() {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
  }

  function toggleChatSidebar() {
    isChatSidebarCollapsed.value = !isChatSidebarCollapsed.value
  }

  return {
    isMobileMenuOpen,
    isChatSidebarCollapsed,
    globalLoading,
    toasts,
    setLoading,
    showToast,
    removeToast,
    toggleMobileMenu,
    toggleChatSidebar
  }
})
