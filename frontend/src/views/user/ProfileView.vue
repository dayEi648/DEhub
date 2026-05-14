<template>
  <div class="profile-page">
    <section class="profile-hero">
      <div class="container hero-content">
        <div class="avatar-upload" @click="triggerFileInput">
          <Avatar
            :src="previewAvatar || authStore.user?.avatar_url"
            :name="authStore.user?.username || ''"
            :size="160"
            class="profile-avatar"
          />
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            hidden
            @change="handleFileChange"
          />
        </div>
        <h1 class="profile-name">{{ authStore.user?.username }}</h1>
        <span class="permission-badge" :class="permissionClass">{{ permissionLabel }}</span>
      </div>
    </section>

    <section class="profile-form-section">
      <div class="container">
        <div class="profile-form">
          <div class="form-group">
            <label>用户名</label>
            <input v-model="form.username" class="form-input" />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input v-model="form.email" class="form-input" />
          </div>
          <div class="form-group">
            <label>个人简介</label>
            <textarea v-model="form.personal_profile" class="form-input" rows="4" />
          </div>
          <PrimaryButton @click="handleSave">保存更改</PrimaryButton>

          <div class="password-section">
            <div class="section-toggle" @click="showPassword = !showPassword">
              {{ showPassword ? '收起' : '修改密码' }}
            </div>
            <div v-if="showPassword" class="password-form">
              <div class="form-group">
                <label>旧密码</label>
                <input v-model="passwordForm.oldPassword" type="password" class="form-input" />
              </div>
              <div class="form-group">
                <label>新密码</label>
                <input v-model="passwordForm.newPassword" type="password" class="form-input" />
              </div>
              <div class="form-group">
                <label>确认新密码</label>
                <input v-model="passwordForm.confirmPassword" type="password" class="form-input" />
              </div>
              <PrimaryButton @click="handlePasswordChange">修改密码</PrimaryButton>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import Avatar from '@/components/Avatar.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'

const authStore = useAuthStore()
const userStore = useUserStore()

const fileInput = ref<HTMLInputElement>()
const previewAvatar = ref<string | null>(null)
const selectedFile = ref<File | null>(null)
const showPassword = ref(false)

const form = reactive({
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
  personal_profile: authStore.user?.personal_profile || ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const permissionLabel = computed(() => {
  const p = authStore.user?.permission
  if (p === 2) return '超级管理员'
  if (p === 1) return '管理员'
  return '普通用户'
})

const permissionClass = computed(() => {
  const p = authStore.user?.permission
  if (p === 2) return 'super-admin'
  if (p === 1) return 'admin'
  return 'user'
})

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    alert('头像大小不能超过 5MB')
    return
  }
  selectedFile.value = file
  previewAvatar.value = URL.createObjectURL(file)
}

async function handleSave() {
  if (!authStore.user) return
  await userStore.updateProfile(authStore.user.id, {
    username: form.username,
    email: form.email,
    personal_profile: form.personal_profile
  }, selectedFile.value || undefined)
  selectedFile.value = null
}

async function handlePasswordChange() {
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    alert('两次输入的密码不一致')
    return
  }
  if (!authStore.user) return
  await userStore.updateProfile(authStore.user.id, {
    password: passwordForm.newPassword
  })
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  showPassword.value = false
}
</script>

<style scoped>
.profile-hero {
  height: 320px;
  background: var(--bg-black);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.hero-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.avatar-upload {
  cursor: pointer;
  margin-bottom: 16px;
}
.profile-avatar {
  border: 3px solid rgba(255, 255, 255, 0.2);
}
.profile-name {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-white);
  margin-bottom: 8px;
}
.permission-badge {
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--radius-pill);
}
.permission-badge.user {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}
.permission-badge.admin {
  background: rgba(0, 113, 227, 0.2);
  color: var(--apple-blue);
}
.permission-badge.super-admin {
  background: rgba(175, 82, 222, 0.2);
  color: var(--admin-purple);
}
.profile-form-section {
  background: var(--bg-gray);
  padding: 60px 0;
}
.profile-form {
  max-width: 600px;
  margin: 0 auto;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  outline: none;
}
.form-input:focus {
  border-color: var(--apple-blue);
}
.password-section {
  margin-top: 40px;
}
.section-toggle {
  font-size: 14px;
  font-weight: 600;
  color: var(--link-blue);
  cursor: pointer;
  margin-bottom: 16px;
}
.password-form {
  padding-top: 8px;
}
</style>
