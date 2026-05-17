import { ref } from 'vue'
import { defineStore } from 'pinia'
import type {
  SystemLogResponse,
  SystemLogStatsResponse,
} from '@/types'
import * as systemLogApi from '@/api/systemLog'
import { useUiStore } from './ui'

export const useLogMonitorStore = defineStore('logMonitor', () => {
  const uiStore = useUiStore()

  const logList = ref<SystemLogResponse[]>([])
  const totalLogs = ref(0)
  const stats = ref<SystemLogStatsResponse | null>(null)
  const currentLog = ref<SystemLogResponse | null>(null)
  const loading = ref(false)

  async function fetchLogs(params?: Parameters<typeof systemLogApi.fetchSystemLogs>[0]) {
    loading.value = true
    try {
      const { data } = await systemLogApi.fetchSystemLogs(params)
      logList.value = data.items
      totalLogs.value = data.total
      return data
    } catch (error: any) {
      const message = error.response?.data?.message || '获取日志列表失败'
      uiStore.showToast(message, 'error')
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchStats() {
    try {
      const { data } = await systemLogApi.fetchSystemLogStats()
      stats.value = data
      return data
    } catch (error: any) {
      const message = error.response?.data?.message || '获取日志统计失败'
      uiStore.showToast(message, 'error')
      throw error
    }
  }

  async function fetchLogById(id: number) {
    try {
      const { data } = await systemLogApi.fetchSystemLogById(id)
      currentLog.value = data
      return data
    } catch (error: any) {
      const message = error.response?.data?.message || '获取日志详情失败'
      uiStore.showToast(message, 'error')
      throw error
    }
  }

  async function resolveLog(id: number) {
    try {
      const { data } = await systemLogApi.resolveSystemLog(id)
      const idx = logList.value.findIndex((l) => l.id === id)
      if (idx !== -1) {
        logList.value[idx] = data
      }
      if (currentLog.value?.id === id) {
        currentLog.value = data
      }
      uiStore.showToast('已标记为已处理', 'success')
      return data
    } catch (error: any) {
      const message = error.response?.data?.message || '操作失败'
      uiStore.showToast(message, 'error')
      throw error
    }
  }

  async function batchResolveLogs(ids: number[]) {
    try {
      const { data } = await systemLogApi.batchResolveSystemLogs(ids)
      logList.value = logList.value.map((log) => {
        if (ids.includes(log.id)) {
          return { ...log, is_resolved: true, resolved_at: new Date().toISOString() }
        }
        return log
      })
      uiStore.showToast(`已批量标记 ${data.resolved_count} 条日志为已处理`, 'success')
      return data.resolved_count
    } catch (error: any) {
      const message = error.response?.data?.message || '批量操作失败'
      uiStore.showToast(message, 'error')
      throw error
    }
  }

  async function deleteLog(id: number) {
    try {
      await systemLogApi.deleteSystemLog(id)
      logList.value = logList.value.filter((l) => l.id !== id)
      totalLogs.value -= 1
      uiStore.showToast('日志已删除', 'success')
    } catch (error: any) {
      const message = error.response?.data?.message || '删除失败'
      uiStore.showToast(message, 'error')
      throw error
    }
  }

  return {
    logList,
    totalLogs,
    stats,
    currentLog,
    loading,
    fetchLogs,
    fetchStats,
    fetchLogById,
    resolveLog,
    batchResolveLogs,
    deleteLog,
  }
})
