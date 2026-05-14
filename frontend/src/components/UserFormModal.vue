<template>
  <Modal
    :model-value="modelValue"
    :title="mode === 'create' ? '创建用户' : '编辑用户'"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <form class="user-form" @submit.prevent="handleSubmit">
      <div class="form-group">
        <label class="form-label">用户名 <span v-if="mode === 'create'" class="required">*</span></label>
        <input v-model="form.username" class="form-input" type="text" placeholder="3~64 字符" />
        <span v-if="errors.username" class="error-text">{{ errors.username }}</span>
      </div>

      <div class="form-group">
        <label class="form-label">邮箱 <span v-if="mode === 'create'" class="required">*</span></label>
        <input v-model="form.email" class="form-input" type="email" placeholder="有效邮箱地址" />
        <span v-if="errors.email" class="error-text">{{ errors.email }}</span>
      </div>

      <div class="form-group">
        <label class="form-label">
          密码
          <span v-if="mode === 'create'" class="required">*</span>
          <span v-else class="hint">（留空表示不修改）</span>
        </label>
        <input v-model="form.password" class="form-input" type="password" placeholder="6~128 字符" />
        <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
      </div>

      <div class="form-group">
        <label class="form-label">权限</label>
        <select v-model="form.permission" class="form-select">
          <option :value="0">普通用户</option>
          <option :value="1">管理员</option>
          <option :value="2">超级管理员</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">个人简介</label>
        <textarea v-model="form.personal_profile" class="form-textarea" rows="3" placeholder="可选" />
      </div>

      <div v-if="mode === 'edit'" class="form-group">
        <label class="form-label">头像</label>
        <div class="avatar-upload">
          <ImageUploader
            :preview-url="form.avatar_url"
            :name="form.username || ''"
            :size="80"
            @select="handleAvatarSelect"
          />
        </div>
      </div>
    </form>

    <template #footer>
      <button class="modal-btn" @click="$emit('update:modelValue', false)">取消</button>
      <PrimaryButton :disabled="submitting" @click="handleSubmit">
        {{ submitting ? '保存中…' : mode === 'create' ? '创建' : '保存' }}
      </PrimaryButton>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import type { UserResponse, UserCreate, UserUpdate } from '@/types'
import { useUiStore } from '@/stores/ui'
import { createUser, updateUser } from '@/api/user'
import Modal from './Modal.vue'
import PrimaryButton from './PrimaryButton.vue'
import ImageUploader from './ImageUploader.vue'

interface Props {
  modelValue: boolean
  mode: 'create' | 'edit'
  user?: UserResponse | null
}

const props = withDefaults(defineProps<Props>(), {
  user: null
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: [user: UserResponse]
}>()

const form = ref({
  username: '',
  email: '',
  password: '',
  permission: 0,
  personal_profile: '',
  avatar_url: null as string | null
})

const errors = ref<Record<string, string>>({})
const submitting = ref(false)
const avatarFile = ref<File | null>(null)

function resetForm() {
  if (avatarObjectUrl) {
    URL.revokeObjectURL(avatarObjectUrl)
    avatarObjectUrl = null
  }
  form.value = {
    username: '',
    email: '',
    password: '',
    permission: 0,
    personal_profile: '',
    avatar_url: null
  }
  errors.value = {}
  avatarFile.value = null
}

function populateForm(user: UserResponse) {
  if (avatarObjectUrl) {
    URL.revokeObjectURL(avatarObjectUrl)
    avatarObjectUrl = null
  }
  form.value = {
    username: user.username,
    email: user.email,
    password: '',
    permission: user.permission,
    personal_profile: user.personal_profile || '',
    avatar_url: user.avatar_url
  }
  errors.value = {}
  avatarFile.value = null
}

watch(() => props.modelValue, (visible) => {
  if (visible) {
    nextTick(() => {
      if (props.mode === 'edit' && props.user) {
        populateForm(props.user)
      } else {
        resetForm()
      }
    })
  }
})

let avatarObjectUrl: string | null = null

function handleAvatarSelect(file: File) {
  if (avatarObjectUrl) {
    URL.revokeObjectURL(avatarObjectUrl)
  }
  avatarFile.value = file
  avatarObjectUrl = URL.createObjectURL(file)
  form.value.avatar_url = avatarObjectUrl
}

onUnmounted(() => {
  if (avatarObjectUrl) {
    URL.revokeObjectURL(avatarObjectUrl)
  }
})

function validate(): boolean {
  errors.value = {}
  if (props.mode === 'create' || form.value.username) {
    if (!form.value.username || form.value.username.length < 3 || form.value.username.length > 64) {
      errors.value.username = '用户名需 3~64 字符'
    }
  }
  if (props.mode === 'create' || form.value.email) {
    if (!form.value.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)) {
      errors.value.email = '请输入有效邮箱'
    }
  }
  if (props.mode === 'create') {
    if (!form.value.password || form.value.password.length < 6 || form.value.password.length > 128) {
      errors.value.password = '密码需 6~128 字符'
    }
  } else if (form.value.password && (form.value.password.length < 6 || form.value.password.length > 128)) {
    errors.value.password = '密码需 6~128 字符'
  }
  return Object.keys(errors.value).length === 0
}

function buildCreateData(): UserCreate {
  return {
    username: form.value.username,
    email: form.value.email,
    password: form.value.password,
    permission: form.value.permission,
    personal_profile: form.value.personal_profile || undefined
  }
}

function buildUpdateFormData(): FormData {
  const formData = new FormData()
  const data: UserUpdate = {}
  if (form.value.username) data.username = form.value.username
  if (form.value.email) data.email = form.value.email
  if (form.value.password) data.password = form.value.password
  data.permission = form.value.permission
  if (form.value.personal_profile) data.personal_profile = form.value.personal_profile
  if (form.value.avatar_url && !avatarFile.value) data.avatar_url = form.value.avatar_url

  formData.append('user_in', JSON.stringify(data))
  if (avatarFile.value) {
    formData.append('file', avatarFile.value)
  }
  return formData
}

async function handleSubmit() {
  if (!validate()) return
  submitting.value = true
  const uiStore = useUiStore()
  try {
    if (props.mode === 'create') {
      const { data } = await createUser(buildCreateData())
      emit('success', data)
    } else if (props.user) {
      const { data } = await updateUser(props.user.id, buildUpdateFormData())
      emit('success', data)
    }
    emit('update:modelValue', false)
  } catch (error: any) {
    const message = error.response?.data?.message || '操作失败'
    uiStore.showToast(message, 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.user-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-label {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.required {
  color: var(--error-red);
}
.hint {
  font-weight: 400;
  color: var(--text-tertiary);
  font-size: 12px;
}
.form-input,
.form-select,
.form-textarea {
  padding: 8px 12px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
  background: var(--button-default-light);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color 0.2s;
}
.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  border-color: var(--apple-blue);
}
.form-textarea {
  resize: vertical;
  min-height: 60px;
}
.error-text {
  font-size: 12px;
  color: var(--error-red);
}
.avatar-upload {
  display: flex;
  align-items: center;
}
.modal-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-family: var(--font-body);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  background: var(--button-default-light);
  color: var(--text-secondary);
}
</style>
