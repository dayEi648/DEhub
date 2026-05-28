<script setup lang="ts">
import {
  ArrowLeft, VideoPlay, Star, StarFilled, ChatDotRound,
  Headset, CirclePlus
} from '@element-plus/icons-vue'
import { usePlaylistDetail } from './usePlaylistDetail'
import AddToPlaylistDialog from '@/views/profile/AddToPlaylistDialog.vue'
import CommentSection from '@/components/CommentSection/CommentSection.vue'
import { ref } from 'vue'

const {
  type,
  id,
  detailLoading,
  songPageData,
  songPageNum,
  songPageSize,
  songTotal,
  songLoading,
  isCollected,
  collectLoading,
  isOwnPlaylist,
  detailName,
  coverUrl,
  creatorText,
  description,
  playCount,
  collectCount,
  hot,
  headerCommentCount,
  formatCount,
  toggleCollect,
  playMusic,
  goBack,
  formatTime
} = usePlaylistDetail()

const addDialogVisible = ref(false)
const addDialogMusicId = ref(0)

function openAddToPlaylistDialog(musicId: number) {
  addDialogMusicId.value = musicId
  addDialogVisible.value = true
}

function defaultCover() {
  return 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
}
</script>

<template>
  <div class="playlist-detail-page">
    <!-- 背景光效 -->
    <div class="detail-bg-glow" />
    <div class="detail-stars">
      <div v-for="i in 5" :key="i" class="star-dot" :class="`star-${i}`" />
    </div>

    <!-- Header -->
    <header class="detail-header">
      <div class="header-inner">
        <div class="header-left">
          <button class="back-btn" @click="goBack">
            <el-icon size="16"><ArrowLeft /></el-icon>
            <span>返回</span>
          </button>
          <div class="header-divider" />
          <h1 class="page-title">
            {{ type === 'playlist' ? '歌单详情' : '专辑详情' }}
          </h1>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="detail-main">
      <div v-loading="detailLoading" class="detail-content">
        <!-- 信息头部区 -->
        <div class="info-header">
          <div class="info-cover">
            <img
              v-if="coverUrl"
              :src="coverUrl"
              :alt="detailName"
            />
            <div v-else class="cover-placeholder">
              <el-icon size="48"><Headset /></el-icon>
            </div>
          </div>
          <div class="info-meta">
            <h2 class="info-name">{{ detailName || '-' }}</h2>
            <div class="info-creator">
              <span class="creator-label">{{ type === 'playlist' ? '创建者' : '作者' }}</span>
              <span class="creator-name">{{ creatorText }}</span>
            </div>
            <p v-if="description" class="info-desc">{{ description }}</p>
            <div class="info-stats">
              <span class="stat-item">
                <el-icon size="14"><VideoPlay /></el-icon>
                {{ formatCount(playCount) }}
              </span>
              <span class="stat-item">
                <el-icon size="14"><Star /></el-icon>
                {{ formatCount(collectCount) }}
              </span>
              <span v-if="type === 'playlist'" class="stat-item">
                <el-icon size="14"><ChatDotRound /></el-icon>
                {{ formatCount(headerCommentCount) }}
              </span>
              <span class="stat-item hot">
                热度 {{ formatCount(hot) }}
              </span>
            </div>
            <div class="info-actions">
              <el-button
                v-if="!(type === 'playlist' && isOwnPlaylist)"
                :type="isCollected ? 'primary' : 'default'"
                :loading="collectLoading"
                class="collect-btn"
                @click="toggleCollect"
              >
                <el-icon size="16">
                  <StarFilled v-if="isCollected" />
                  <Star v-else />
                </el-icon>
                <span>{{ isCollected ? '已收藏' : '收藏' }}</span>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 歌曲列表区 -->
        <div class="song-section">
          <div class="section-title">
            <span>歌曲列表</span>
            <span class="section-count">{{ songTotal }}首</span>
          </div>

          <div v-loading="songLoading" class="song-list-body">
            <div
              v-for="(music, index) in songPageData"
              :key="music.id"
              class="song-item"
              :style="{ animationDelay: `${index * 0.03}s` }"
            >
              <div class="song-rank">
                {{ (songPageNum - 1) * songPageSize + index + 1 }}
              </div>
              <div class="song-cover-small">
                <img
                  v-if="music.image1Url"
                  :src="music.image1Url"
                  :alt="music.musicName"
                />
                <div v-else class="cover-placeholder-small">
                  <el-icon size="14"><Headset /></el-icon>
                </div>
              </div>
              <div class="song-info-main">
                <div class="song-name-main">{{ music.musicName }}</div>
                <div class="song-meta-main">
                  <span>{{ music.authorNameList?.filter(Boolean).join(' / ') || '未知作者' }}</span>
                  <template v-if="music.albumName">
                    <span class="meta-dot">·</span>
                    <span>{{ music.albumName }}</span>
                  </template>
                </div>
              </div>
              <div class="song-actions">
                <button class="action-btn play" @click="playMusic(music)">
                  <el-icon size="16"><VideoPlay /></el-icon>
                </button>
                <el-dropdown trigger="click" popper-class="detail-dropdown-popper">
                  <button class="action-btn collect">
                    <el-icon size="16"><CirclePlus /></el-icon>
                  </button>
                  <template #dropdown>
                    <el-dropdown-menu class="detail-dropdown-menu">
                      <el-dropdown-item @click="openAddToPlaylistDialog(music.id)">
                        收藏到歌单
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <div v-if="songTotal === 0 && !songLoading" class="empty-state">
              <el-icon size="40" color="#475569"><Headset /></el-icon>
              <span>暂无歌曲</span>
            </div>
          </div>

          <div v-if="songTotal > 0" class="pagination-bar">
            <el-pagination
              v-model:current-page="songPageNum"
              v-model:page-size="songPageSize"
              :total="songTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              background
            />
          </div>
        </div>

        <!-- 评论区（仅歌单） -->
        <CommentSection
          v-if="type === 'playlist'"
          scene-type="playlist"
          :scene-id="id"
        />
      </div>
    </main>

    <AddToPlaylistDialog
      :visible="addDialogVisible"
      :music-id="addDialogMusicId"
      @submit="addDialogVisible = false"
      @cancel="addDialogVisible = false"
    />
  </div>
</template>

<style scoped src="./playlist-detail.css"></style>
