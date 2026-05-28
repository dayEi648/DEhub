<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { uploadPlaylistCover } from '@/api/playlist'
import { getUser } from '@/utils/authStorage'
import type { PlaylistVO } from '@/types/playlist'

const props = defineProps<{
  visible: boolean
  mode: 'create' | 'edit'
  initialData?: Partial<PlaylistVO>
}>()

const emit = defineEmits<{
  submit: [data: Partial<PlaylistVO>]
  cancel: []
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => {
    if (!val) emit('cancel')
  }
})

const form = ref({
  playlistName: '',
  isPublic: true,
  imageUrl: ''
})

const fileList = ref<any[]>([])
const rawFile = ref<File | null>(null)
const loading = ref(false)

watch(() => props.visible, (val) => {
  if (val) {
    if (props.mode === 'edit' && props.initialData) {
      form.value.playlistName = props.initialData.playlistName || ''
      form.value.isPublic = !props.initialData.isPrivate
      form.value.imageUrl = props.initialData.imageUrl || ''
      if (form.value.imageUrl) {
        fileList.value = [{ url: form.value.imageUrl, name: 'cover' }]
      } else {
        fileList.value = []
      }
    } else {
      form.value.playlistName = ''
      form.value.isPublic = true
      form.value.imageUrl = ''
      fileList.value = []
    }
    rawFile.value = null
  }
})

const dialogTitle = computed(() =>
  props.mode === 'create' ? '创建歌单' : '编辑歌单'
)

function onFileChange(uploadFile: any) {
  rawFile.value = uploadFile.raw
}

function onFileRemove() {
  rawFile.value = null
  form.value.imageUrl = ''
}

async function handleSubmit() {
  if (!form.value.playlistName.trim()) {
    ElMessage.warning('请输入歌单名称')
    return
  }

  const user = getUser()
  if (!user?.id) {
    ElMessage.warning('请先登录')
    return
  }

  loading.value = true
  let imageUrl = form.value.imageUrl

  try {
    if (rawFile.value) {
      imageUrl = await uploadPlaylistCover(rawFile.value)
    }

    const payload: Partial<PlaylistVO> = {
      playlistName: form.value.playlistName.trim(),
      userId: user.id,
      isPrivate: !form.value.isPublic,
      isLike: false,
      imageUrl: imageUrl || undefined
    }

    if (props.mode === 'edit' && props.initialData?.id) {
      payload.id = props.initialData.id
    }

    emit('submit', payload)
  } catch (err: any) {
    ElMessage.error(err.message || '封面上传失败')
  } finally {
    loading.value = false
  }
}

function handleClose() {
  if (loading.value) return
  emit('cancel')
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="420px"
    :close-on-click-modal="false"
    :append-to-body="true"
    destroy-on-close
    class="playlist-form-dialog"
    @close="handleClose"
  >
    <el-form label-position="top" class="playlist-form">
      <el-form-item label="歌单封面">
        <el-upload
          v-model:file-list="fileList"
          :class="['playlist-uploader', fileList.length > 0 ? 'has-file' : '']"
          :auto-upload="false"
          :limit="1"
          list-type="picture-card"
          accept="image/*"
          @change="onFileChange"
          @remove="onFileRemove"
        >
          <el-icon v-if="fileList.length === 0"><Plus /></el-icon>
        </el-upload>
      </el-form-item>

      <el-form-item label="歌单名称">
        <el-input
          v-model="form.playlistName"
          placeholder="给你的歌单起个名字"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="是否公开">
        <el-switch
          v-model="form.isPublic"
          active-text="公开"
          inactive-text="私密"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit">
          {{ mode === 'create' ? '创建' : '保存' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.playlist-form-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 20px 24px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.playlist-form-dialog :deep(.el-dialog__title) {
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 600;
}

.playlist-form-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
}

.playlist-form-dialog :deep(.el-dialog__footer) {
  padding: 12px 24px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.playlist-form :deep(.el-form-item__label) {
  color: #94a3b8;
  font-size: 13px;
  padding-bottom: 6px;
}

.playlist-form :deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
}

.playlist-form :deep(.el-input__inner) {
  color: #e2e8f0;
}

.playlist-form :deep(.el-input__inner::placeholder) {
  color: #64748b;
}

.playlist-form :deep(.el-input__count-inner) {
  background: transparent;
  color: #64748b;
}

.playlist-uploader :deep(.el-upload--picture-card) {
  width: 120px;
  height: 120px;
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: #64748b;
}

.playlist-uploader.has-file :deep(.el-upload--picture-card) {
  display: none;
}

.playlist-uploader :deep(.el-upload-list__item) {
  width: 120px;
  height: 120px;
  border-radius: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
