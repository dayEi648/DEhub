<script setup lang="ts">
import { Tools } from '@element-plus/icons-vue'
import ProfileLayout from '@/components/ProfileLayout/ProfileLayout.vue'
import { useProfilePage } from './useProfilePage'
import ProfileFavorites from './ProfileFavorites.vue'
import ProfileSettings from './ProfileSettings.vue'
import ProfileSocial from './ProfileSocial.vue'
import ProfileSpace from './ProfileSpace.vue'

const { activeTab } = useProfilePage()
</script>

<template>
  <ProfileLayout v-model:active-tab="activeTab">
    <ProfileFavorites v-if="activeTab === 'favorites'" />
    <ProfileSocial v-else-if="activeTab === 'social'" />
    <ProfileSpace v-else-if="activeTab === 'space'" />
    <ProfileSettings v-else-if="activeTab === 'settings'" />
    <div v-else class="placeholder-page">
      <div class="placeholder-icon">
        <el-icon size="48" color="#a78bfa"><Tools /></el-icon>
      </div>
      <h2 class="placeholder-title">功能开发中</h2>
      <p class="placeholder-desc">该模块即将上线，敬请期待</p>
    </div>
  </ProfileLayout>
</template>

<style scoped>
.placeholder-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
  text-align: center;
}

.placeholder-icon {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(107, 70, 193, 0.15);
}

.placeholder-title {
  font-size: 20px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.placeholder-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}
</style>
