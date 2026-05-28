<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { CollectionTag, CircleCheck } from '@element-plus/icons-vue'
import { getPlaylistPage } from '@/api/playlist'
import { addSongToPlaylist } from '@/api/playlist'
import { getUser, setUser } from '@/utils/authStorage'
import type { PlaylistVO } from '@/types/playlist'

const props = defineProps<{
  visible: boolean
  musicId: number
}>()

const emit = defineEmits<{
  submit: [playlistId: number]
  cancel: []
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => {
    if (!val) emit('cancel')
  }
})

const playlists = ref<PlaylistVO[]>([])
const loading = ref(false)

const user = computed(() => getUser())

watch(() => props.visible, (val) => {
  if (val) {
    loadPlaylists()
  }
})

async function loadPlaylists() {
  const uid = user.value?.id
  if (!uid) {
    playlists.value = []
    return
  }
  loading.value = true
  try {
    const res = await getPlaylistPage({
      pageNum: 1,
      pageSize: 100,
      userId: uid
    })
    playlists.value = res.records
  } catch {
    playlists.value = []
    ElMessage.error('加载歌单失败')
  } finally {
    loading.value = false
  }
}

function isSongInPlaylist(pl: PlaylistVO): boolean {
  return pl.songIds?.includes(props.musicId) ?? false
}

async function handleSelectPlaylist(pl: PlaylistVO) {
  if (isSongInPlaylist(pl)) {
    ElMessage.warning('该歌曲已在歌单中')
    return
  }
  try {
    await addSongToPlaylist(pl.id, props.musicId)
    ElMessage.success(`已添加到「${pl.playlistName}」`)
    // 同步更新 localStorage 中的 collectMusicIds
    const user = getUser()
    if (user) {
      const ids = new Set(user.collectMusicIds ?? [])
      ids.add(props.musicId)
      user.collectMusicIds = Array.from(ids)
      user.collectMusicCount = (user.collectMusicCount ?? 0) + 1
      setUser(user)
    }
    emit('submit', pl.id)
  } catch (err: any) {
    ElMessage.error(err.message || '添加失败')
  }
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="添加到歌单"
    width="400px"
    :close-on-click-modal="false"
    :append-to-body="true"
    destroy-on-close
    class="add-to-playlist-dialog"
    @close="emit('cancel')"
  >
    <div v-loading="loading" class="playlist-select-list">
      <div
        v-for="pl in playlists"
        :key="pl.id"
        class="playlist-select-item"
        :class="{ disabled: isSongInPlaylist(pl) }"
        @click="handleSelectPlaylist(pl)"
      >
        <div class="select-item-cover">
          <img v-if="pl.imageUrl" :src="pl.imageUrl" :alt="pl.playlistName" />
          <el-icon v-else size="20"><CollectionTag /></el-icon>
        </div>
        <div class="select-item-info">
          <div class="select-item-name">{{ pl.playlistName }}</div>
          <div class="select-item-meta">{{ pl.songIds?.length || 0 }}首</div>
        </div>
        <div v-if="isSongInPlaylist(pl)" class="select-item-checked">
          <el-icon size="16"><CircleCheck /></el-icon>
          <span>已添加</span>
        </div>
      </div>
      <div v-if="playlists.length === 0 && !loading" class="empty-tip">
        暂无歌单，请先创建歌单
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.add-to-playlist-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 20px 24px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.add-to-playlist-dialog :deep(.el-dialog__title) {
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 600;
}

.add-to-playlist-dialog :deep(.el-dialog__body) {
  padding: 12px 16px 20px;
  max-height: 400px;
  overflow-y: auto;
}

.playlist-select-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.playlist-select-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.playlist-select-item:hover:not(.disabled) {
  background: rgba(107, 70, 193, 0.12);
}

.playlist-select-item.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.select-item-cover {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.select-item-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.select-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.select-item-name {
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.select-item-meta {
  font-size: 12px;
  color: #64748b;
}

.select-item-checked {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #10b981;
  flex-shrink: 0;
}

.empty-tip {
  text-align: center;
  padding: 32px 0;
  color: #64748b;
  font-size: 14px;
}
</style>
