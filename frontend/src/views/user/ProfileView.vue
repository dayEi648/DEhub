<template>
  <div class="profile-page">
    <section class="profile-hero">
      <div class="container hero-content">
        <ImageUploader
          :preview-url="previewAvatar || authStore.user?.avatar_url"
          :name="authStore.user?.username || ''"
          :size="160"
          @select="handleFileSelect"
        />
        <h1 class="profile-name">{{ authStore.user?.username }}</h1>
        <span class="permission-badge" :class="permissionClass">{{ permissionLabel }}</span>
      </div>
    </section>

    <section class="profile-form-section">
      <div class="container">
        <div class="profile-form">
          <div class="form-group">
            <label>用户名</label>
            <FilterButton as-input v-model="form.username" placeholder="用户名" />
            <span v-if="errors.username" class="field-error">{{ errors.username }}</span>
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <FilterButton as-input v-model="form.email" placeholder="邮箱" />
            <span v-if="errors.email" class="field-error">{{ errors.email }}</span>
          </div>
          <div class="form-group">
            <label>个人简介</label>
            <textarea v-model="form.personal_profile" class="form-input" rows="4" />
            <span v-if="errors.personal_profile" class="field-error">{{ errors.personal_profile }}</span>
          </div>
          <PrimaryButton @click="handleSave">保存更改</PrimaryButton>

          <div class="password-section">
            <div class="section-toggle" @click="togglePasswordSection">
              {{ showPassword ? '收起' : '修改密码' }}
            </div>
            <div v-if="showPassword" class="password-form">
              <div class="form-group">
                <label>旧密码</label>
                <input v-model="passwordForm.oldPassword" type="password" class="form-input" placeholder="请输入旧密码" />
                <span v-if="errors.oldPassword" class="field-error">{{ errors.oldPassword }}</span>
              </div>
              <div class="form-group">
                <label>新密码</label>
                <input v-model="passwordForm.newPassword" type="password" class="form-input" placeholder="6-128 位字符" />
                <span v-if="errors.newPassword" class="field-error">{{ errors.newPassword }}</span>
              </div>
              <div class="form-group">
                <label>确认新密码</label>
                <input v-model="passwordForm.confirmPassword" type="password" class="form-input" placeholder="再次输入新密码" />
                <span v-if="errors.confirmPassword" class="field-error">{{ errors.confirmPassword }}</span>
              </div>
              <PrimaryButton @click="handleChangePassword">确认修改</PrimaryButton>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import ImageUploader from '@/components/ImageUploader.vue'
import FilterButton from '@/components/FilterButton.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'

const authStore = useAuthStore()
const userStore = useUserStore()

const previewAvatar = ref<string | null>(null)
const selectedFile = ref<File | null>(null)
const showPassword = ref(false)

const form = reactive({
  username: '',
  email: '',
  personal_profile: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const errors = reactive<Record<string, string>>({})

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

onMounted(() => {
  if (authStore.user) {
    form.username = authStore.user.username
    form.email = authStore.user.email
    form.personal_profile = authStore.user.personal_profile || ''
  }
})

function handleFileSelect(file: File) {
  selectedFile.value = file
  previewAvatar.value = URL.createObjectURL(file)
}

function togglePasswordSection() {
  showPassword.value = !showPassword.value
  if (!showPassword.value) {
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    clearFieldErrors(['oldPassword', 'newPassword', 'confirmPassword'])
  }
}

function clearFieldErrors(fields: string[]) {
  fields.forEach((f) => delete errors[f])
}

function validateProfile(): boolean {
  let valid = true
  clearFieldErrors(['username', 'email', 'personal_profile'])

  if (!form.username || form.username.length < 3 || form.username.length > 64) {
    errors.username = '用户名长度为 3-64 字符'
    valid = false
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.email || !emailRegex.test(form.email)) {
    errors.email = '请输入有效的邮箱地址'
    valid = false
  }

  return valid
}

function validatePassword(): boolean {
  let valid = true
  clearFieldErrors(['oldPassword', 'newPassword', 'confirmPassword'])

  if (!passwordForm.oldPassword) {
    errors.oldPassword = '请输入旧密码'
    valid = false
  } else if (passwordForm.oldPassword.length < 6 || passwordForm.oldPassword.length > 128) {
    errors.oldPassword = '旧密码长度为 6-128 字符'
    valid = false
  }

  if (!passwordForm.newPassword || passwordForm.newPassword.length < 6 || passwordForm.newPassword.length > 128) {
    errors.newPassword = '新密码长度为 6-128 字符'
    valid = false
  }

  if (passwordForm.newPassword === passwordForm.oldPassword && passwordForm.newPassword) {
    errors.newPassword = '新密码不能与旧密码相同'
    valid = false
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
    valid = false
  }

  return valid
}

async function handleSave() {
  if (!authStore.user) return
  if (!validateProfile()) return

  try {
    await userStore.updateProfile(authStore.user.id, {
      username: form.username,
      email: form.email,
      personal_profile: form.personal_profile
    }, selectedFile.value || undefined)
    selectedFile.value = null
    previewAvatar.value = null
  } catch (error: any) {
    if (error.response?.status === 422 && error.response.data?.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        detail.forEach((item: any) => {
          const field = item.loc?.[item.loc.length - 1]
          if (field && typeof field === 'string') {
            errors[field] = item.msg
          }
        })
      }
    }
  }
}

async function handleChangePassword() {
  if (!validatePassword()) return

  try {
    await userStore.changePassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })
  } catch (error: any) {
    const status = error.response?.status
    const message = error.response?.data?.message

    if (status === 401) {
      errors.oldPassword = message || '旧密码错误'
    } else if (status === 400) {
      errors.newPassword = message || '新密码不能与旧密码相同'
    } else if (status === 422 && error.response.data?.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        detail.forEach((item: any) => {
          const field = item.loc?.[item.loc.length - 1]
          if (field === 'old_password') {
            errors.oldPassword = item.msg
          } else if (field === 'new_password') {
            errors.newPassword = item.msg
          }
        })
      }
    }
  }
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
  color: #8e8e93;
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
  font-family: var(--font-body);
}
.form-input:focus {
  border-color: var(--apple-blue);
}
.field-error {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--error-red);
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
