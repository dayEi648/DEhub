<script setup lang="ts">
import {
  Trophy, Lightning, Star, Collection, FolderOpened,
  Opportunity, Headset, Microphone, ChatDotRound, TrendCharts
} from '@element-plus/icons-vue'
import type { DiscoverTab } from '../useDiscoverPage'

const emit = defineEmits<{
  (e: 'goTab', tab: DiscoverTab): void
}>()

const categories = [
  {
    key: 'hot' as DiscoverTab,
    label: '热歌榜',
    desc: '最热音乐排行',
    icon: Trophy,
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
    shadow: 'rgba(245, 158, 11, 0.25)'
  },
  {
    key: 'new' as DiscoverTab,
    label: '新歌榜',
    desc: '最新发布音乐',
    icon: Lightning,
    gradient: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
    shadow: 'rgba(16, 185, 129, 0.25)'
  },
  {
    key: 'vip' as DiscoverTab,
    label: 'VIP',
    desc: 'VIP专属音乐',
    icon: Star,
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
    shadow: 'rgba(139, 92, 246, 0.25)'
  },
  {
    key: 'playlist' as DiscoverTab,
    label: '歌单',
    desc: '精选歌单推荐',
    icon: Collection,
    gradient: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
    shadow: 'rgba(59, 130, 246, 0.25)'
  },
  {
    key: 'album' as DiscoverTab,
    label: '专辑',
    desc: '热门专辑精选',
    icon: FolderOpened,
    gradient: 'linear-gradient(135deg, #d97706 0%, #ea580c 100%)',
    shadow: 'rgba(217, 119, 6, 0.25)'
  },
  {
    key: 'emotion' as DiscoverTab,
    label: '按情绪浏览',
    desc: '用情绪找音乐',
    icon: Opportunity,
    gradient: 'linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)',
    shadow: 'rgba(236, 72, 153, 0.25)'
  },
  {
    key: 'interest' as DiscoverTab,
    label: '按兴趣浏览',
    desc: '按兴趣 discover',
    icon: TrendCharts,
    gradient: 'linear-gradient(135deg, #14b8a6 0%, #0ea5e9 100%)',
    shadow: 'rgba(20, 184, 166, 0.25)'
  },
  {
    key: 'style' as DiscoverTab,
    label: '按曲风浏览',
    desc: '探索不同曲风',
    icon: Headset,
    gradient: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
    shadow: 'rgba(99, 102, 241, 0.25)'
  },
  {
    key: 'instrument' as DiscoverTab,
    label: '按乐器浏览',
    desc: '按乐器筛选',
    icon: Microphone,
    gradient: 'linear-gradient(135deg, #f97316 0%, #eab308 100%)',
    shadow: 'rgba(249, 115, 22, 0.25)'
  },
  {
    key: 'language' as DiscoverTab,
    label: '按语种浏览',
    desc: '多语种音乐',
    icon: ChatDotRound,
    gradient: 'linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%)',
    shadow: 'rgba(14, 165, 233, 0.25)'
  }
]
</script>

<template>
  <section class="overview-section">
    <!-- 欢迎标题 -->
    <div class="overview-hero">
      <h1 class="overview-title">发现音乐</h1>
      <p class="overview-subtitle">探索无限音乐世界，找到属于你的旋律</p>
    </div>

    <!-- 分类卡片网格 -->
    <div class="category-grid">
      <div
        v-for="cat in categories"
        :key="cat.key"
        class="category-card"
        :style="{ '--card-shadow': cat.shadow }"
        @click="emit('goTab', cat.key)"
      >
        <div class="card-icon-wrap" :style="{ background: cat.gradient }">
          <el-icon class="card-icon" :size="28"><component :is="cat.icon" /></el-icon>
        </div>
        <div class="card-info">
          <div class="card-label">{{ cat.label }}</div>
          <div class="card-desc">{{ cat.desc }}</div>
        </div>
        <el-icon class="card-arrow" :size="16"><ArrowRight /></el-icon>
      </div>
    </div>
  </section>
</template>

<style scoped>
.overview-section {
  padding: 20px 0;
}

.overview-hero {
  text-align: center;
  margin-bottom: 40px;
}

.overview-title {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(90deg, #e2e8f0 0%, #a78bfa 50%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.overview-subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.45);
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.category-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.category-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 80% 20%, var(--card-shadow) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.35s ease;
}

.category-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}

.category-card:hover::before {
  opacity: 1;
}

.card-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.card-info {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.card-label {
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.card-arrow {
  color: rgba(255, 255, 255, 0.25);
  flex-shrink: 0;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1;
}

.category-card:hover .card-arrow {
  color: rgba(255, 255, 255, 0.7);
  transform: translateX(4px);
}

@media (max-width: 1024px) {
  .category-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .category-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .overview-title {
    font-size: 28px;
  }
}
</style>
