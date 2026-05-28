<script setup lang="ts">
import { reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { ElMessage, type FormInstance } from 'element-plus'
import { User } from '@element-plus/icons-vue'
import AuthShell from './AuthShell.vue'
import { login } from '@/api/user'
import { setAuth } from '@/utils/authStorage'
import { validatePassword, validateUsername } from '@/utils/validators'
import { useRouter } from 'vue-router'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
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
  password: [
    {
      validator: (_: unknown, value: string, cb: (e?: Error) => void) => {
        const r = validatePassword(value)
        cb(r === true ? undefined : new Error(r))
      },
      trigger: 'blur'
    }
  ]
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
    const res = await login({
      username: form.username.trim(),
      password: form.password
    })
    setAuth(res.user, res.token)
    ElMessage.success('登录成功')
    router.push('/home')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell>
    <div class="auth-card">
      <div class="auth-brand">
        <div class="auth-brand__title">回声记忆</div>
        <div class="auth-brand__sub">用情绪谱曲，让回忆有迹可循</div>
        <div class="auth-brand__en">EchoMemory</div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            maxlength="32"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
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
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        还没有账号？
        <RouterLink to="/register">立即注册</RouterLink>
      </div>
    </div>
  </AuthShell>
</template>

<style scoped>
.auth-submit {
  margin-top: 4px;
}
</style>
