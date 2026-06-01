import type { User } from '../types/user'

const TOKEN_KEY = 'token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string) {
  localStorage.setItem(REFRESH_TOKEN_KEY, token)
}

export function getUser(): User | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function setUser(user: User) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function isLoggedIn(): boolean {
  return !!getToken()
}

export function decodeTokenPayload(token: string): { exp?: number } | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    let payload = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padding = payload.length % 4
    if (padding) {
      payload += '='.repeat(4 - padding)
    }
    const decoded = JSON.parse(atob(payload))
    return typeof decoded === 'object' && decoded !== null ? decoded : null
  } catch {
    return null
  }
}

export function isTokenExpired(): boolean {
  const token = getToken()
  if (!token) return true
  const payload = decodeTokenPayload(token)
  if (!payload || typeof payload.exp !== 'number') return true
  // 预留 60 秒缓冲，避免临界过期
  return payload.exp * 1000 < Date.now() + 60_000
}

export function isAuthenticated(): boolean {
  return !!getToken() && !isTokenExpired()
}
