import { ref } from 'vue'

// 加载动画显示状态
const isLoading = ref(false)

// 最小显示时长（毫秒）
const MIN_DISPLAY_DURATION = 1000

// 存储timeout ID
let hideTimeout: ReturnType<typeof setTimeout> | null = null
let startTime: number = 0

/**
 * 页面加载动画控制 Hook
 *
 * 使用方式：
 * 1. 在路由守卫中调用 show() 显示动画
 * 2. 在路由加载完成后调用 hide() 隐藏动画
 * 3. 动画将保证至少显示 MIN_DISPLAY_DURATION 毫秒
 */
export function usePageLoading() {
  /**
   * 显示加载动画
   */
  const show = () => {
    // 清除之前的隐藏定时器
    if (hideTimeout) {
      clearTimeout(hideTimeout)
      hideTimeout = null
    }
    startTime = Date.now()
    isLoading.value = true
  }

  /**
   * 隐藏加载动画
   * 会确保动画至少显示 MIN_DISPLAY_DURATION 毫秒
   */
  const hide = () => {
    const elapsed = Date.now() - startTime
    const remaining = Math.max(0, MIN_DISPLAY_DURATION - elapsed)

    if (remaining === 0) {
      // 已经超过最小显示时长，直接隐藏
      isLoading.value = false
    } else {
      // 还需要等待一段时间
      hideTimeout = setTimeout(() => {
        isLoading.value = false
        hideTimeout = null
      }, remaining)
    }
  }

  /**
   * 强制立即隐藏（用于错误处理等特殊情况）
   */
  const hideImmediately = () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout)
      hideTimeout = null
    }
    isLoading.value = false
  }

  return {
    isLoading,
    show,
    hide,
    hideImmediately
  }
}

// 导出单例状态，供全局使用
export const pageLoadingState = {
  isLoading,
  show: () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout)
      hideTimeout = null
    }
    startTime = Date.now()
    isLoading.value = true
  },
  hide: () => {
    const elapsed = Date.now() - startTime
    const remaining = Math.max(0, MIN_DISPLAY_DURATION - elapsed)

    if (remaining === 0) {
      isLoading.value = false
    } else {
      hideTimeout = setTimeout(() => {
        isLoading.value = false
        hideTimeout = null
      }, remaining)
    }
  },
  hideImmediately: () => {
    if (hideTimeout) {
      clearTimeout(hideTimeout)
      hideTimeout = null
    }
    isLoading.value = false
  }
}
