<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, RefreshRight } from '@element-plus/icons-vue'
import { updateProfile } from '@/api/user'
import { getUser, setUser } from '@/utils/authStorage'
import { genderOptions } from '@/types/user'
import type { UploadFile } from 'element-plus'

const user = computed(() => getUser())
const defaultAvatar = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'

const previewUrl = ref(user.value?.avatar || defaultAvatar)

const form = reactive({
  name: user.value?.name || '',
  gender: user.value?.gender ?? 0,
  city: user.value?.city || '',
  description: user.value?.description || '',
  birth: user.value?.birth || '',
  avatarFile: null as File | null
})

const saving = ref(false)

function handleAvatarChange(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  if (!raw) return
  if (!raw.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  form.avatarFile = raw
  previewUrl.value = URL.createObjectURL(raw)
}

async function handleSave() {
  saving.value = true
  try {
    const updated = await updateProfile({
      name: form.name,
      gender: form.gender,
      city: form.city,
      description: form.description,
      birth: form.birth,
      avatarFile: form.avatarFile
    })
    setUser(updated)
    // 若上传了新头像，更新预览为服务端返回的 URL
    if (updated.avatar) {
      previewUrl.value = updated.avatar
      form.avatarFile = null
    }
    ElMessage.success('保存成功')
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

function handleReset() {
  const u = getUser()
  form.name = u?.name || ''
  form.gender = u?.gender ?? 0
  form.city = u?.city || ''
  form.description = u?.description || ''
  form.birth = u?.birth || ''
  form.avatarFile = null
  previewUrl.value = u?.avatar || defaultAvatar
}
</script>

<template>
  <div class="settings-page">
    <div class="settings-card">
      <h2 class="settings-title">个人资料</h2>

      <!-- 头像 -->
      <div class="avatar-section">
        <el-avatar :size="96" :src="previewUrl" class="settings-avatar" />
        <el-upload
          accept="image/*"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleAvatarChange"
        >
          <el-button type="primary" class="upload-btn" :icon="Upload">
            更换头像
          </el-button>
        </el-upload>
      </div>

      <!-- 表单 -->
      <el-form label-position="top" class="settings-form">
        <el-form-item label="昵称">
          <el-input v-model="form.name" placeholder="请输入昵称" maxlength="30" show-word-limit />
        </el-form-item>

        <div class="form-row">
          <el-form-item label="性别" class="form-item-half">
            <el-select v-model="form.gender" placeholder="请选择性别" style="width: 100%">
              <el-option
                v-for="opt in genderOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="生日" class="form-item-half">
            <el-date-picker
              v-model="form.birth"
              type="date"
              placeholder="请选择生日"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
        </div>

        <el-form-item label="城市">
          <el-input v-model="form.city" placeholder="请输入所在城市" maxlength="50" />
        </el-form-item>

        <el-form-item label="个人简介">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="介绍一下你自己吧"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item>
          <div class="form-actions">
            <el-button type="primary" :loading="saving" class="save-btn" @click="handleSave">
              保存修改
            </el-button>
            <el-button :icon="RefreshRight" class="reset-btn" @click="handleReset">
              重置
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  animation: fadeUp 0.6s ease-out both;
}

.settings-card {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(107, 70, 193, 0.1);
  border-radius: 20px;
  padding: 32px;
  max-width: 640px;
}

.settings-title {
  font-size: 20px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0 0 24px 0;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.settings-avatar {
  border: 3px solid rgba(107, 70, 193, 0.4);
  box-shadow: 0 0 24px rgba(107, 70, 193, 0.2);
}

.upload-btn {
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border: none;
  border-radius: 10px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.upload-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(107, 70, 193, 0.35);
}

.settings-form :deep(.el-form-item__label) {
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  padding-bottom: 6px;
}

.settings-form :deep(.el-input__wrapper),
.settings-form :deep(.el-textarea__inner),
.settings-form :deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(107, 70, 193, 0.15);
  box-shadow: none;
  border-radius: 10px;
  color: #e2e8f0;
}

.settings-form :deep(.el-input__wrapper:hover),
.settings-form :deep(.el-textarea__inner:hover),
.settings-form :deep(.el-select .el-input__wrapper:hover) {
  border-color: rgba(107, 70, 193, 0.35);
}

.settings-form :deep(.el-input__wrapper.is-focus),
.settings-form :deep(.el-textarea__inner:focus),
.settings-form :deep(.el-select .el-input.is-focus .el-input__wrapper) {
  border-color: #6b46c1;
  box-shadow: 0 0 0 2px rgba(107, 70, 193, 0.15);
}

.settings-form :deep(.el-textarea__inner) {
  resize: none;
}

.settings-form :deep(.el-input__count) {
  color: #64748b;
  background: transparent;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-item-half {
  flex: 1;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.save-btn {
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border: none;
  border-radius: 10px;
  padding: 12px 28px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.save-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(107, 70, 193, 0.35);
}

.reset-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(107, 70, 193, 0.15);
  border-radius: 10px;
  padding: 12px 24px;
  font-size: 14px;
  color: #94a3b8;
  transition: all 0.3s ease;
}

.reset-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  border-color: rgba(107, 70, 193, 0.3);
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .settings-card {
    padding: 20px;
  }

  .form-row {
    flex-direction: column;
    gap: 0;
  }
}
</style>
