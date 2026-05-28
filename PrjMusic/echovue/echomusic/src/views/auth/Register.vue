<script setup lang="ts">
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { User, EditPen } from '@element-plus/icons-vue'
import AuthShell from './AuthShell.vue'
import { register, updateProfile } from '@/api/user'
import { setAuth } from '@/utils/authStorage'
import { validateNickname, validatePassword, validateUsername } from '@/utils/validators'
import { Gender } from '@/types/user'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  name: '',
  password: '',
  confirmPassword: ''
})

const rules = {
  username: [
    {
      validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
        const r = validateUsername(value)
        cb(r === true ? undefined : new Error(r))
      },
      trigger: 'blur'
    }
  ],
  name: [
    {
      validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
        const r = validateNickname(value)
        cb(r === true ? undefined : new Error(r))
      },
      trigger: 'blur'
    }
  ],
  password: [
    {
      validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
        const r = validatePassword(value)
        cb(r === true ? undefined : new Error(r))
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    {
      validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
        if (!value) {
          cb(new Error('请再次输入密码'))
          return
        }
        if (value !== form.password) {
          cb(new Error('两次输入的密码不一致'))
          return
        }
        cb()
      },
      trigger: 'blur'
    }
  ]
}

/* ---------- 注册成功后个人信息弹窗 ---------- */
const showProfileDialog = ref(false)
const profileLoading = ref(false)

const profileForm = reactive({
  name: '',
  gender: Gender.UNKNOWN,
  city: '',
  description: '',
  avatarFile: null as File | null,
  avatarPreview: ''
})

function onAvatarChange(file: File) {
  profileForm.avatarFile = file
  profileForm.avatarPreview = URL.createObjectURL(file)
}

function onAvatarRemove() {
  profileForm.avatarFile = null
  profileForm.avatarPreview = ''
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    const u = form.username.trim()
    const nameTrim = form.name.trim()
    const res = await register({
      username: u,
      password: form.password,
      name: nameTrim || u
    })
    setAuth(res.user, res.token)
    // 预填昵称
    profileForm.name = res.user.name || res.user.username
    showProfileDialog.value = true
    ElMessage.success('注册成功，已自动登录')
  } finally {
    loading.value = false
  }
}

function goHome() {
  router.push('/home')
}

async function handleSaveProfile() {
  profileLoading.value = true
  try {
    const updated = await updateProfile({
      name: profileForm.name || undefined,
      gender: profileForm.gender,
      city: profileForm.city || undefined,
      description: profileForm.description || undefined,
      avatarFile: profileForm.avatarFile
    })
    // 更新本地缓存的用户信息
    const token = localStorage.getItem('echomusic_token') || ''
    setAuth(updated, token)
    ElMessage.success('资料保存成功')
    goHome()
  } finally {
    profileLoading.value = false
  }
}
</script>

<template>
  <AuthShell>
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-brand__title">加入回声记忆</div>
        <div class="auth-brand__sub">记录情绪，收藏属于你的声音轨迹</div>
        <div class="auth-brand__en">EchoMemory · Register</div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="3～32 位，支持中文、字母、数字、下划线"
            maxlength="32"
            show-word-limit
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item label="昵称（可选，默认同用户名）" prop="name">
          <el-input
            v-model="form.name"
            placeholder="不填则使用用户名作为昵称"
            maxlength="32"
            show-word-limit
            :prefix-icon="EditPen"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="8～64 位，需含字母与数字"
            maxlength="64"
            show-password
            clearable
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            maxlength="64"
            show-password
            clearable
            @keyup.enter="handleSubmit"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="auth-submit"
            style="width: 100%"
            :loading="loading"
            @click="handleSubmit"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        已有账号？
        <RouterLink to="/login">去登录</RouterLink>
      </div>
    </div>
  </AuthShell>

  <!-- 注册成功后完善资料弹窗 -->
  <el-dialog
    v-model="showProfileDialog"
    title="完善个人资料"
    width="420px"
    modal-class="auth-profile-mask"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    align-center
  >
    <div class="profile-dialog-content">
      <!-- 头像上传 -->
      <div class="avatar-row">
        <el-avatar :size="80" :src="profileForm.avatarPreview || undefined" class="avatar-preview">
          <el-icon :size="32"><User /></el-icon>
        </el-avatar>
        <el-upload
          class="avatar-uploader"
          action=""
          :auto-upload="false"
          :show-file-list="false"
          :on-change="(uploadFile: any) => onAvatarChange(uploadFile.raw)"
          accept="image/*"
        >
          <el-button type="primary" text size="small">上传头像</el-button>
        </el-upload>
        <el-button
          v-if="profileForm.avatarPreview"
          type="danger"
          text
          size="small"
          @click="onAvatarRemove"
        >
          移除
        </el-button>
      </div>

      <el-form label-position="top">
        <el-form-item label="昵称">
          <el-input v-model="profileForm.name" placeholder="你的昵称" maxlength="32" show-word-limit />
        </el-form-item>

        <el-form-item label="性别">
          <el-radio-group v-model="profileForm.gender">
            <el-radio :value="Gender.UNKNOWN">未知</el-radio>
            <el-radio :value="Gender.MALE">男</el-radio>
            <el-radio :value="Gender.FEMALE">女</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="居住城市">
          <el-input v-model="profileForm.city" placeholder="例如：北京" maxlength="50" show-word-limit />
        </el-form-item>

        <el-form-item label="个人简介">
          <el-input
            v-model="profileForm.description"
            type="textarea"
            :rows="3"
            placeholder="简单介绍一下自己"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="goHome">跳过</el-button>
        <el-button type="primary" :loading="profileLoading" @click="handleSaveProfile">
          保存并进入
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.auth-submit {
  margin-top: 4px;
}

.profile-dialog-content {
  padding: 0 8px;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.avatar-preview {
  flex-shrink: 0;
  background: var(--el-fill-color-light);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
