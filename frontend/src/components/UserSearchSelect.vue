<template>
  <div class="user-search-select">
    <div v-if="selectedUser" class="selected-user">
      <Avatar :size="24" :src="selectedUser.avatar_url" :name="selectedUser.username" />
      <span class="username">{{ selectedUser.username }}</span>
      <button v-if="!disabled" class="clear-btn" @click="clear">×</button>
    </div>
    <div v-else class="input-wrap">
      <input
        v-model="keyword"
        type="text"
        class="form-input"
        :placeholder="placeholder"
        :disabled="disabled"
        @focus="isOpen = true"
        @blur="onBlur"
      />
      <div v-if="isOpen && users.length > 0" class="dropdown">
        <div
          v-for="user in users"
          :key="user.id"
          class="dropdown-item"
          @mousedown.prevent="select(user)"
        >
          <Avatar :size="24" :src="user.avatar_url" :name="user.username" />
          <div class="user-info">
            <span class="username">{{ user.username }}</span>
            <span class="email">{{ user.email }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="isOpen && keyword && !loading" class="dropdown empty">
        <span>未找到用户</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { UserResponse } from '@/types'
import * as userApi from '@/api/user'
import Avatar from './Avatar.vue'

interface Props {
  modelValue?: number | null
  placeholder?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  placeholder: '输入用户名或邮箱搜索',
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const keyword = ref('')
const users = ref<UserResponse[]>([])
const selectedUser = ref<UserResponse | null>(null)
const isOpen = ref(false)
const loading = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | null = null

watch(() => props.modelValue, async (val) => {
  if (val && val !== selectedUser.value?.id) {
    try {
      const { data } = await userApi.fetchUserById(val)
      selectedUser.value = data
    } catch {
      selectedUser.value = null
    }
  } else if (!val) {
    selectedUser.value = null
  }
}, { immediate: true })

watch(keyword, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (!val.trim()) {
    users.value = []
    isOpen.value = false
    return
  }
  loading.value = true
  debounceTimer = setTimeout(async () => {
    try {
      const keyword = val.trim()
      const [byName, byEmail] = await Promise.all([
        userApi.fetchUsers({ username: keyword, limit: 10 }),
        userApi.fetchUsers({ email: keyword, limit: 10 })
      ])
      const merged = new Map<number, UserResponse>()
      byName.data.items.forEach((u) => merged.set(u.id, u))
      byEmail.data.items.forEach((u) => merged.set(u.id, u))
      users.value = Array.from(merged.values())
      isOpen.value = true
    } catch {
      users.value = []
    } finally {
      loading.value = false
    }
  }, 300)
})

function select(user: UserResponse) {
  selectedUser.value = user
  emit('update:modelValue', user.id)
  keyword.value = ''
  users.value = []
  isOpen.value = false
}

function clear() {
  selectedUser.value = null
  emit('update:modelValue', null)
  keyword.value = ''
}

function onBlur() {
  // 延迟关闭以允许点击下拉项
  setTimeout(() => {
    isOpen.value = false
  }, 150)
}


</script>

<style scoped>
.user-search-select {
  position: relative;
}
.selected-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
}
.selected-user .username {
  font-size: 14px;
  color: var(--text-primary);
}
.clear-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 18px;
  color: var(--text-tertiary);
  cursor: pointer;
  line-height: 1;
}
.clear-btn:hover {
  color: var(--error-red);
}
.input-wrap {
  position: relative;
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
.dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-height: 240px;
  overflow-y: auto;
  background: var(--text-white);
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 10;
  padding: 4px;
}
.dropdown.empty {
  padding: 12px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 14px;
}
.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.15s;
}
.dropdown-item:hover {
  background: var(--bg-gray);
}
.user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.user-info .username {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.user-info .email {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
