import client from './client'
import type { UserLogin, UserLoginResponse, UserCreate, UserResponse } from '@/types'

export function login(data: UserLogin) {
  return client.post<UserLoginResponse>('/users/login', data)
}

export function register(data: UserCreate) {
  return client.post<UserResponse>('/users/register', data)
}

export function logout(refreshToken?: string) {
  return client.post('/users/logout', { refresh_token: refreshToken })
}

export function refreshToken(refreshToken: string) {
  return client.post<UserLoginResponse>('/users/refresh-token', { refresh_token: refreshToken })
}
