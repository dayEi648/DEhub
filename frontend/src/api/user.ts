import client from './client'
import type { UserResponse, UserListResponse } from '@/types'

export function fetchUsers(params?: {
  skip?: number
  limit?: number
  include_deleted?: boolean
  username?: string
  email?: string
  permission?: number
}) {
  return client.get<UserListResponse>('/users/', { params })
}

export function fetchUserById(id: number) {
  return client.get<UserResponse>(`/users/${id}`)
}

export function updateUser(id: number, formData: FormData) {
  return client.put<UserResponse>(`/users/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function deleteUser(id: number) {
  return client.delete(`/users/${id}`)
}

export function hardDeleteUser(id: number) {
  return client.delete(`/users/${id}/hard`)
}

export function changePassword(data: { old_password: string; new_password: string }) {
  return client.post('/users/me/change-password', data)
}
