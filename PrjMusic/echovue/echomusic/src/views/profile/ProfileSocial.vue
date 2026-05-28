<script setup lang="ts">
import { UserFilled } from '@element-plus/icons-vue'
import { useProfileSocial } from './useProfileSocial'

const {
  activeSubTab,
  users,
  pageNum,
  pageSize,
  total,
  loading,
  isFollowed,
  toggleFollow,
  goUserDetail,
  handlePageChange
} = useProfileSocial()
</script>

<template>
  <div class="social-page">
    <!-- 子 Tab 切换 -->
    <div class="sub-tab-bar">
      <div
        class="sub-tab-item"
        :class="{ active: activeSubTab === 'follows' }"
        @click="activeSubTab = 'follows'"
      >
        我的关注
      </div>
      <div
        class="sub-tab-item"
        :class="{ active: activeSubTab === 'fans' }"
        @click="activeSubTab = 'fans'"
      >
        我的粉丝
      </div>
    </div>

    <!-- 用户列表 -->
    <div v-loading="loading" class="user-list">
      <div v-if="users.length === 0" class="empty-state">
        <el-icon :size="48" class="empty-icon"><UserFilled /></el-icon>
        <p>{{ activeSubTab === 'follows' ? '暂无关注用户' : '暂无粉丝' }}</p>
      </div>

      <div v-else class="user-grid">
        <div
          v-for="user in users"
          :key="user.id"
          class="user-card"
          @click="goUserDetail(user.id)"
        >
          <el-avatar
            :size="64"
            :src="user.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'"
            class="user-avatar"
          />
          <div class="user-name">{{ user.name || user.username }}</div>
          <el-button
            size="small"
            :type="isFollowed(user) ? 'default' : 'primary'"
            class="follow-btn"
            @click.stop="toggleFollow(user)"
          >
            {{ isFollowed(user) ? '取关' : '关注' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrap">
      <el-pagination
        v-model:current-page="pageNum"
        v-model:page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.social-page {
  padding: 24px;
}

.sub-tab-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  padding: 6px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.sub-tab-item {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 10px 20px;
  border-radius: 12px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sub-tab-item:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.05);
}

.sub-tab-item.active {
  color: #e2e8f0;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.3) 0%, rgba(236, 72, 153, 0.2) 100%);
  box-shadow: 0 0 20px rgba(107, 70, 193, 0.15);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #64748b;
  gap: 12px;
}

.empty-icon {
  color: #475569;
  opacity: 0.5;
}

.user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
}

.user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-card:hover {
  background: rgba(107, 70, 193, 0.08);
  border-color: rgba(107, 70, 193, 0.2);
  transform: translateY(-2px);
}

.user-avatar {
  border: 2px solid rgba(107, 70, 193, 0.3);
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

.follow-btn {
  min-width: 72px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.pagination-wrap :deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-hover-color: #c4b5fd;
  --el-pagination-button-color: #94a3b8;
  --el-pagination-button-disabled-color: #475569;
}
</style>
