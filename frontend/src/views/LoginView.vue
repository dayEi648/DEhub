<template>
  <div class="login-page">
    <div class="login-content">
      <h1 class="login-title">DE hub</h1>
      <p class="login-subtitle">A personal platform for developers</p>

      <div class="login-card">
        <Transition name="fade" mode="out-in">
          <div v-if="isLogin" key="login" class="login-form">
            <div class="form-group">
              <input
                v-model="loginForm.account"
                class="form-input"
                placeholder="邮箱或用户名"
                @input="clearFieldError('account')"
              />
              <p v-if="fieldErrors.account" class="field-error">{{ fieldErrors.account }}</p>
            </div>
            <div class="form-group">
              <input
                v-model="loginForm.password"
                type="password"
                class="form-input"
                placeholder="密码"
                @input="clearFieldError('password')"
              />
              <p v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</p>
            </div>
            <label class="remember-row">
              <input v-model="loginForm.is_remember" type="checkbox" />
              <span>记住登录</span>
            </label>
            <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
            <PrimaryButton class="full-width" @click="handleLogin">登录</PrimaryButton>
            <p class="switch-text">
              还没有账号？<button class="link-btn" @click="isLogin = false">创建账号</button>
            </p>
          </div>

          <div v-else key="register" class="register-form">
            <div class="form-group">
              <input v-model="registerForm.username" class="form-input" placeholder="用户名" @input="clearFieldError('username')" />
              <p v-if="fieldErrors.username" class="field-error">{{ fieldErrors.username }}</p>
            </div>
            <div class="form-group">
              <input v-model="registerForm.email" class="form-input" placeholder="邮箱" @input="clearFieldError('email')" />
              <p v-if="fieldErrors.email" class="field-error">{{ fieldErrors.email }}</p>
            </div>
            <div class="form-group">
              <input v-model="registerForm.password" type="password" class="form-input" placeholder="密码" @input="clearFieldError('password')" />
              <p v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</p>
            </div>
            <div class="form-group">
              <input v-model="registerForm.confirmPassword" type="password" class="form-input" placeholder="确认密码" @input="clearFieldError('confirmPassword')" />
              <p v-if="fieldErrors.confirmPassword" class="field-error">{{ fieldErrors.confirmPassword }}</p>
            </div>
            <p v-if="errorMsg" class="error-text">{{ errorMsg }}</p>
            <PrimaryButton class="full-width" @click="handleRegister">注册</PrimaryButton>
            <p class="switch-text">
              已有账号？<button class="link-btn" @click="isLogin = true">立即登录</button>
            </p>
          </div>
        </Transition>
      </div>
    </div>
    <p class="login-footer">Built with Vue 3, FastAPI & Apple Design</p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import PrimaryButton from '@/components/PrimaryButton.vue'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()

const isLogin = ref(true)
const errorMsg = ref('')
const fieldErrors = reactive<Record<string, string>>({})

const loginForm = reactive({
  account: '',
  password: '',
  is_remember: false
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

function clearFieldError(field: string) {
  delete fieldErrors[field]
}

function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function validateLogin(): boolean {
  errorMsg.value = ''
  Object.keys(fieldErrors).forEach((k) => delete fieldErrors[k])

  if (!loginForm.account || loginForm.account.length < 3 || loginForm.account.length > 255) {
    fieldErrors.account = '账号长度需在 3-255 个字符之间'
  }
  if (!loginForm.password || loginForm.password.length < 6 || loginForm.password.length > 128) {
    fieldErrors.password = '密码长度需在 6-128 个字符之间'
  }

  return Object.keys(fieldErrors).length === 0
}

function validateRegister(): boolean {
  errorMsg.value = ''
  Object.keys(fieldErrors).forEach((k) => delete fieldErrors[k])

  if (!registerForm.username || registerForm.username.length < 3 || registerForm.username.length > 64) {
    fieldErrors.username = '用户名长度需在 3-64 个字符之间'
  }
  if (!registerForm.email || !validateEmail(registerForm.email)) {
    fieldErrors.email = '请输入有效的邮箱地址'
  }
  if (!registerForm.password || registerForm.password.length < 6 || registerForm.password.length > 128) {
    fieldErrors.password = '密码长度需在 6-128 个字符之间'
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    fieldErrors.confirmPassword = '两次输入的密码不一致'
  }

  return Object.keys(fieldErrors).length === 0
}

async function handleLogin() {
  if (!validateLogin()) return
  try {
    await authStore.login({
      account: loginForm.account,
      password: loginForm.password,
      is_remember: loginForm.is_remember
    })
    router.push('/')
  } catch (err: any) {
    errorMsg.value = err.response?.data?.message || '登录失败'
  }
}

async function handleRegister() {
  if (!validateRegister()) return
  try {
    await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })
    uiStore.showToast('注册成功，请登录', 'success')
    isLogin.value = true
    loginForm.account = registerForm.username
    loginForm.password = ''
  } catch (err: any) {
    errorMsg.value = err.response?.data?.message || '注册失败'
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--bg-black);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.login-content {
  width: 100%;
  max-width: 420px;
  text-align: center;
}
.login-title {
  font-family: var(--font-display);
  font-size: 56px;
  font-weight: 600;
  line-height: 1.07;
  letter-spacing: -0.28px;
  color: var(--text-white);
  margin-bottom: 8px;
}
.login-subtitle {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 400;
  line-height: 1.19;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 40px;
}
.login-card {
  background: var(--dark-surface-1);
  border-radius: var(--radius-md);
  padding: 40px;
}
.form-group {
  margin-bottom: 16px;
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-white);
  background: var(--text-primary);
  border: none;
  border-radius: var(--radius-lg);
  outline: none;
}
.form-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}
.form-input:focus {
  outline: 2px solid var(--apple-blue);
}
.remember-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-white);
  margin-bottom: 16px;
  cursor: pointer;
}
.error-text {
  font-size: 12px;
  color: var(--error-red);
  margin-bottom: 12px;
}
.field-error {
  font-size: 12px;
  color: var(--error-red);
  margin-top: 6px;
  text-align: left;
}
.full-width {
  width: 100%;
}
.switch-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 16px;
}
.link-btn {
  background: transparent;
  border: none;
  color: var(--link-blue-dark);
  cursor: pointer;
  font-size: 14px;
}
.link-btn:hover {
  text-decoration: underline;
}
.login-footer {
  position: absolute;
  bottom: 24px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.48);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
