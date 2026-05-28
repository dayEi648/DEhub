
<script setup lang="ts">
import { PageLoading, pageLoadingState } from '@/components/PageLoading'
import { PlayerBar } from '@/components/PlayerBar'

const { isLoading: isRouteLoading } = pageLoadingState
</script>

<template>
  <PageLoading :visible="isRouteLoading" />
  <router-view />
  <PlayerBar />
</template>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f1419;
  color: #e2e8f0;
  line-height: 1.6;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #1e1b2e 100%);
  background-attachment: fixed;
  position: relative;
}

/* Noise texture overlay for subtle grain */
#app::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 128px 128px;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #6b46c1 0%, #ec4899 100%);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #7c4ddb 0%, #f05aa8 100%);
}

/* Element Plus 主题覆盖 */
:root {
  --el-color-primary: #6b46c1;
  --el-color-primary-light-3: #8b5cf6;
  --el-color-primary-light-5: #a78bfa;
  --el-color-primary-light-7: #c4b5fd;
  --el-color-primary-light-8: #ddd6fe;
  --el-color-primary-light-9: #f3e8ff;
  --el-color-primary-dark-2: #5b21b6;

  --el-color-success: #10b981;
  --el-color-warning: #f59e0b;
  --el-color-danger: #ef4444;
  --el-color-info: #64748b;

  --el-bg-color: #1a1f2e;
  --el-bg-color-overlay: rgba(26, 31, 46, 0.95);
  --el-text-color-primary: #e2e8f0;
  --el-text-color-regular: #94a3b8;
  --el-text-color-secondary: #64748b;
  --el-border-color: rgba(255, 255, 255, 0.1);
  --el-border-color-light: rgba(255, 255, 255, 0.05);
  --el-fill-color: rgba(255, 255, 255, 0.05);
  --el-fill-color-light: rgba(255, 255, 255, 0.08);
  --el-fill-color-lighter: rgba(255, 255, 255, 0.03);

  /* ===== 新增情绪色彩系统 ===== */
  --emotion-romance: #6b46c1;
  --emotion-melancholy: #3b82f6;
  --emotion-energy: #f59e0b;
  --emotion-healing: #10b981;
  --emotion-passion: #ec4899;
  --emotion-nostalgia: #d97706;
  --emotion-calm: #64748b;

  /* 光晕 */
  --glow-purple: 0 0 40px rgba(107, 70, 193, 0.3);
  --glow-pink: 0 0 40px rgba(236, 72, 153, 0.3);
  --glow-cyan: 0 0 40px rgba(6, 182, 212, 0.3);

  /* 玻璃拟态 */
  --glass-bg: rgba(255, 255, 255, 0.03);
  --glass-border: rgba(255, 255, 255, 0.06);
  --glass-blur: 16px;
}

/* 按钮样式优化 */
.el-button--primary {
  background: linear-gradient(135deg, #6b46c1 0%, #8b5cf6 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(107, 70, 193, 0.4);
  transition: all 0.3s ease;
}

.el-button--primary:hover {
  background: linear-gradient(135deg, #7c4ddb 0%, #9c6af7 100%);
  box-shadow: 0 6px 20px rgba(107, 70, 193, 0.5);
  transform: translateY(-1px);
}

.el-button--danger {
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
}

.el-button--danger:hover {
  background: linear-gradient(135deg, #f55a5a 0%, #fb8888 100%);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5);
}

/* 弹窗遮罩 */
.el-overlay {
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
}

/* 下拉菜单 */
.el-select-dropdown {
  background: linear-gradient(135deg, #1a1f2e 0%, #2d1b4e 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.el-select-dropdown__item {
  color: #94a3b8;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background: rgba(107, 70, 193, 0.2);
  color: #e2e8f0;
}

.el-select-dropdown__item.selected {
  color: #ec4899;
}

/* 日期选择器 */
.el-picker-panel {
  background: linear-gradient(135deg, #1a1f2e 0%, #2d1b4e 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.el-date-table th,
.el-date-table td {
  color: #94a3b8;
}

.el-date-table td.current:not(.disabled) span {
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  color: white;
}

.el-date-table td.today span {
  color: #ec4899;
}

.el-date-table td.available:hover {
  color: #e2e8f0;
}

/* 消息提示 */
.el-message {
  background: linear-gradient(135deg, #1a1f2e 0%, #2d1b4e 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.el-message .el-message__content {
  color: #e2e8f0;
}

/* 确认框 */
.el-message-box {
  background: linear-gradient(135deg, #1a1f2e 0%, #2d1b4e 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.el-message-box__title {
  color: #e2e8f0;
}

.el-message-box__message {
  color: #94a3b8;
}

/* 加载动画 */
.el-loading-mask {
  background: rgba(15, 20, 25, 0.8);
  backdrop-filter: blur(2px);
}

.el-loading-spinner .path {
  stroke: url(#gradient);
}

/* 表单相关 */
.el-form-item.is-error .el-input__wrapper {
  box-shadow: 0 0 0 1px #ef4444 inset;
}

.el-form-item__error {
  color: #ef4444;
}

/* Switch 开关 */
.el-switch.is-checked .el-switch__core {
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border-color: transparent;
}
</style>
