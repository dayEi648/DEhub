<template>
  <div class="log-monitor-page">
    <div class="container">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1 class="page-title">日志监控</h1>
      </div>

      <!-- 统计卡片区 -->
      <div class="stats-grid">
        <div
          v-for="card in statCards"
          :key="card.key"
          class="stat-card"
          :class="[card.key, { pulse: card.key === 'critical' && card.value > 0 }]"
        >
          <div class="stat-title">{{ card.title }}</div>
          <div class="stat-value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-bar" :style="{ background: card.color }" />
        </div>
      </div>

      <!-- 筛选工具栏 -->
      <div class="toolbar">
        <select v-model="levelFilter" class="filter-select">
          <option value="">全部级别</option>
          <option value="WARN">WARN</option>
          <option value="ERROR">ERROR</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
        <FilterButton
          as-input
          v-model="moduleQuery"
          placeholder="搜索模块名"
          @enter="handleSearch"
        />
        <input
          v-model="createdAfter"
          type="datetime-local"
          class="filter-select"
          title="起始时间"
        />
        <input
          v-model="createdBefore"
          type="datetime-local"
          class="filter-select"
          title="截止时间"
        />
        <label class="toggle-label">
          <div class="toggle-track" :class="{ active: showResolved }" @click="showResolved = !showResolved">
            <div class="toggle-thumb" />
          </div>
          <span>包含已处理</span>
        </label>
        <PrimaryButton @click="handleSearch">查询</PrimaryButton>
        <GhostButton @click="handleReset">重置</GhostButton>
      </div>

      <!-- 表格列表 -->
      <div v-if="logStore.logList.length" class="admin-table">
        <div class="table-row header">
          <div class="col-check">
            <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
          </div>
          <div class="col-level">级别</div>
          <div class="col-module">模块 / 消息</div>
          <div class="col-trace">追踪 ID</div>
          <div class="col-time">时间</div>
          <div class="col-status">状态</div>
          <div class="col-actions">操作</div>
        </div>
        <div
          v-for="log in logStore.logList"
          :key="log.id"
          class="table-row"
          :class="{ resolved: log.is_resolved }"
        >
          <div class="col-check">
            <input
              type="checkbox"
              :checked="selectedIds.has(log.id)"
              @change="toggleSelect(log.id)"
            />
          </div>
          <div class="col-level">
            <span class="level-badge" :class="log.level.toLowerCase()">{{ log.level }}</span>
          </div>
          <div class="col-module">
            <div class="module-name">{{ log.module || '-' }}</div>
            <div class="message-text">{{ log.message }}</div>
          </div>
          <div class="col-trace">{{ formatTraceId(log.trace_id) }}</div>
          <div class="col-time">{{ formatDateTime(log.created_at) }}</div>
          <div class="col-status">
            <span v-if="log.is_resolved" class="status-resolved">
              <span class="status-dot resolved" />已处理
            </span>
            <span v-else class="status-unresolved">
              <span class="status-dot unresolved" />未处理
            </span>
          </div>
          <div class="col-actions">
            <button class="action-link" @click="openDetail(log)">查看</button>
            <button
              v-if="!log.is_resolved"
              class="action-link"
              @click="handleResolve(log.id)"
            >处理</button>
            <button class="action-link danger" @click="confirmDelete(log.id)">删除</button>
          </div>
        </div>
      </div>
      <EmptyState v-else-if="!logStore.loading" description="暂无符合条件的日志" />

      <!-- 分页 -->
      <Pagination
        v-if="logStore.totalLogs > pageSize"
        v-model:current-page="currentPage"
        :total="logStore.totalLogs"
        :page-size="pageSize"
      />
    </div>

    <!-- 详情弹窗 -->
    <Modal v-model="detailModalOpen" title="日志详情">
      <div v-if="detailLog" class="detail-content">
        <div class="detail-header">
          <span class="level-badge" :class="detailLog.level.toLowerCase()">{{ detailLog.level }}</span>
          <span class="detail-module">{{ detailLog.module || '-' }}</span>
          <span class="detail-time">{{ formatDateTime(detailLog.created_at) }}</span>
        </div>
        <div class="detail-message">{{ detailLog.message }}</div>
        <div v-if="detailLog.exception" class="detail-section">
          <div class="section-title" @click="showException = !showException">
            {{ showException ? '▼' : '▶' }} 异常堆栈
          </div>
          <pre v-show="showException" class="section-body exception">{{ detailLog.exception }}</pre>
        </div>
        <div v-if="detailLog.extra" class="detail-section">
          <div class="section-title" @click="showExtra = !showExtra">
            {{ showExtra ? '▼' : '▶' }} 上下文数据
          </div>
          <pre v-show="showExtra" class="section-body json">{{ JSON.stringify(detailLog.extra, null, 2) }}</pre>
        </div>
        <div class="detail-meta">
          <div v-if="detailLog.trace_id" class="meta-item">
            <span class="meta-key">trace_id</span>
            <span class="meta-value">{{ detailLog.trace_id }}</span>
          </div>
          <div v-if="detailLog.ip" class="meta-item">
            <span class="meta-key">ip</span>
            <span class="meta-value">{{ detailLog.ip }}</span>
          </div>
          <div v-if="detailLog.user_id" class="meta-item">
            <span class="meta-key">user_id</span>
            <span class="meta-value">{{ detailLog.user_id }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="modal-btn" @click="detailModalOpen = false">关闭</button>
        <button
          v-if="detailLog && !detailLog.is_resolved"
          class="modal-btn success"
          @click="handleResolveFromModal"
        >标记为已处理</button>
        <button class="modal-btn danger" @click="handleDeleteFromModal">删除</button>
      </template>
    </Modal>

    <!-- 删除确认 -->
    <Modal v-model="deleteModalOpen" title="确认删除">
      <p>确定要删除这条日志吗？此操作不可恢复。</p>
      <template #footer>
        <button class="modal-btn" @click="deleteModalOpen = false">取消</button>
        <button class="modal-btn danger" @click="executeDelete">确认删除</button>
      </template>
    </Modal>

    <!-- 批量操作浮动条 -->
    <Transition name="batch-bar">
      <div v-if="selectedIds.size > 0" class="batch-bar">
        <span class="batch-text">已选择 {{ selectedIds.size }} 条日志</span>
        <PrimaryButton @click="handleBatchResolve">批量标记已处理</PrimaryButton>
        <GhostButton @click="selectedIds.clear()">取消选择</GhostButton>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useLogMonitorStore } from '@/stores/logMonitor'
import type { SystemLogResponse } from '@/types'
import FilterButton from '@/components/FilterButton.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import GhostButton from '@/components/GhostButton.vue'
import Pagination from '@/components/Pagination.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'

const logStore = useLogMonitorStore()

// 筛选状态
const levelFilter = ref('')
const moduleQuery = ref('')
const createdAfter = ref('')
const createdBefore = ref('')
const showResolved = ref(false)
const currentPage = ref(1)
const pageSize = 20

// 弹窗状态
const detailModalOpen = ref(false)
const deleteModalOpen = ref(false)
const detailLog = ref<SystemLogResponse | null>(null)
const showException = ref(true)
const showExtra = ref(true)
const pendingDeleteId = ref<number | null>(null)

// 批量选择
const selectedIds = ref<Set<number>>(new Set())

const isAllSelected = computed(() => {
  if (logStore.logList.length === 0) return false
  return logStore.logList.every((log) => selectedIds.value.has(log.id))
})

// 统计卡片
const statCards = computed(() => {
  const s = logStore.stats
  return [
    { key: 'unresolved', title: '未处理', value: s?.total_unresolved ?? 0, color: 'var(--error-red)' },
    { key: 'warn', title: 'WARN', value: s?.warn_count ?? 0, color: 'var(--warning-orange)' },
    { key: 'error', title: 'ERROR', value: s?.error_count ?? 0, color: 'var(--error-red)' },
    { key: 'critical', title: 'CRITICAL', value: s?.critical_count ?? 0, color: 'var(--admin-purple)' },
  ]
})

onMounted(() => {
  logStore.fetchStats()
  loadLogs()
})

watch(currentPage, () => {
  loadLogs()
})

function loadLogs() {
  logStore.fetchLogs({
    skip: (currentPage.value - 1) * pageSize,
    limit: pageSize,
    level: levelFilter.value || undefined,
    is_resolved: showResolved.value ? undefined : false,
    module: moduleQuery.value || undefined,
    created_after: createdAfter.value || undefined,
    created_before: createdBefore.value || undefined,
  })
}

function handleSearch() {
  currentPage.value = 1
  selectedIds.value.clear()
  loadLogs()
}

function handleReset() {
  levelFilter.value = ''
  moduleQuery.value = ''
  createdAfter.value = ''
  createdBefore.value = ''
  showResolved.value = false
  currentPage.value = 1
  selectedIds.value.clear()
  loadLogs()
}

function openDetail(log: SystemLogResponse) {
  detailLog.value = log
  showException.value = !!log.exception
  showExtra.value = !!log.extra
  detailModalOpen.value = true
}

function handleResolve(id: number) {
  logStore.resolveLog(id).then(() => {
    logStore.fetchStats()
  })
}

function handleResolveFromModal() {
  if (!detailLog.value) return
  logStore.resolveLog(detailLog.value.id).then(() => {
    logStore.fetchStats()
    if (detailLog.value) {
      detailLog.value = logStore.logList.find((l) => l.id === detailLog.value!.id) || detailLog.value
    }
  })
}

function confirmDelete(id: number) {
  pendingDeleteId.value = id
  deleteModalOpen.value = true
}

function executeDelete() {
  if (pendingDeleteId.value == null) return
  logStore.deleteLog(pendingDeleteId.value).then(() => {
    logStore.fetchStats()
    deleteModalOpen.value = false
    pendingDeleteId.value = null
    if (detailModalOpen.value) detailModalOpen.value = false
  })
}

function handleDeleteFromModal() {
  if (!detailLog.value) return
  confirmDelete(detailLog.value.id)
  detailModalOpen.value = false
}

function toggleSelect(id: number) {
  const set = selectedIds.value
  if (set.has(id)) {
    set.delete(id)
  } else {
    set.add(id)
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value.clear()
  } else {
    logStore.logList.forEach((log) => selectedIds.value.add(log.id))
  }
}

function handleBatchResolve() {
  const ids = Array.from(selectedIds.value)
  if (ids.length === 0) return
  logStore.batchResolveLogs(ids).then(() => {
    selectedIds.value.clear()
    logStore.fetchStats()
  })
}

function formatDateTime(date: string) {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatTraceId(traceId: string | null) {
  if (!traceId) return '-'
  return traceId.length > 10 ? traceId.slice(0, 8) + '…' : traceId
}
</script>

<style scoped>
.log-monitor-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px - 44px - 32px);
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.stat-card {
  background: var(--text-white);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-card);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: rgba(0, 0, 0, 0.28) 3px 8px 36px 0px;
}
.stat-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.stat-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  line-height: 1.2;
  margin-bottom: 12px;
}
.stat-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 2px 2px 0 0;
}
.stat-card.pulse {
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(175, 82, 222, 0.25); }
  50% { box-shadow: 0 0 0 8px rgba(175, 82, 222, 0); }
}
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.filter-select {
  padding: 8px 14px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  outline: none;
  font-family: var(--font-body);
  color: var(--text-primary);
}
.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
}
.toggle-track {
  width: 44px;
  height: 24px;
  border-radius: var(--radius-pill);
  background: rgba(0, 0, 0, 0.16);
  transition: background 0.2s ease;
  position: relative;
  cursor: pointer;
}
.toggle-track.active {
  background: var(--success-green);
}
.toggle-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
.toggle-track.active .toggle-thumb {
  transform: translateX(20px);
}

/* 表格 */
.admin-table {
  background: var(--text-white);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: 24px;
}
.table-row {
  display: grid;
  grid-template-columns: 40px 72px 1.5fr 1fr 140px 90px 120px;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  font-size: 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.table-row.header {
  font-weight: 600;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.02);
  font-size: 13px;
  letter-spacing: -0.2px;
  position: sticky;
  top: 0;
  z-index: 10;
}
.table-row:hover:not(.header) {
  background: rgba(0, 0, 0, 0.02);
}
.table-row.resolved {
  background: rgba(52, 199, 89, 0.03);
}
.col-check {
  display: flex;
  align-items: center;
  justify-content: center;
}
.col-check input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--apple-blue);
  cursor: pointer;
}
.col-level {
  display: flex;
  align-items: center;
}
.level-badge {
  display: inline-block;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--radius-pill);
  text-align: center;
}
.level-badge.warn {
  background: rgba(255, 149, 0, 0.12);
  color: var(--warning-orange);
}
.level-badge.error {
  background: rgba(255, 59, 48, 0.12);
  color: var(--error-red);
}
.level-badge.critical {
  background: rgba(175, 82, 222, 0.12);
  color: var(--admin-purple);
}
.col-module {
  min-width: 0;
}
.module-name {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 2px;
}
.message-text {
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.col-trace {
  color: var(--text-tertiary);
  font-size: 13px;
  font-family: monospace;
}
.col-time {
  color: var(--text-secondary);
  font-size: 13px;
}
.col-status {
  display: flex;
  align-items: center;
}
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.unresolved {
  background: var(--warning-orange);
}
.status-dot.resolved {
  background: var(--success-green);
}
.status-unresolved {
  color: var(--warning-orange);
  font-size: 13px;
}
.status-resolved {
  color: var(--success-green);
  font-size: 13px;
  opacity: 0.8;
}
.col-actions {
  display: flex;
  gap: 8px;
}
.action-link {
  font-size: 12px;
  color: var(--link-blue);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background 0.15s ease;
}
.action-link:hover {
  background: rgba(0, 102, 204, 0.08);
}
.action-link.danger {
  color: var(--error-red);
}
.action-link.danger:hover {
  background: rgba(255, 59, 48, 0.08);
}

/* 详情弹窗 */
.detail-content {
  max-height: 60vh;
  overflow-y: auto;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.detail-module {
  font-size: 14px;
  color: var(--text-secondary);
}
.detail-time {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-left: auto;
}
.detail-message {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-primary);
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 16px;
  word-break: break-word;
}
.detail-section {
  margin-bottom: 12px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.02);
  cursor: pointer;
  user-select: none;
}
.section-body {
  padding: 12px 14px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  line-height: 1.5;
  background: #f5f5f7;
  margin: 0;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.section-body.exception {
  color: var(--error-red);
}
.section-body.json {
  color: var(--text-secondary);
}
.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.meta-key {
  font-size: 12px;
  color: var(--text-tertiary);
}
.meta-value {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: monospace;
}

/* 弹窗按钮 */
.modal-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-family: var(--font-body);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  background: var(--button-default-light);
  color: var(--text-secondary);
}
.modal-btn.danger {
  background: var(--error-red);
  color: var(--text-white);
}
.modal-btn.success {
  background: var(--success-green);
  color: var(--text-white);
}

/* 批量浮动条 */
.batch-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--text-white);
  padding: 12px 24px;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 100;
}
.batch-text {
  font-size: 14px;
  color: var(--text-secondary);
}
.batch-bar-enter-active,
.batch-bar-leave-active {
  transition: all 0.3s ease;
}
.batch-bar-enter-from,
.batch-bar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
