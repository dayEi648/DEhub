import request from '../utils/request'
import type {
  User,
  UserListResponse,
  UserListParams,
  CreateUserData,
  UpdateUserData,
  LoginData,
  LoginResponse,
  RegisterData,
  LogoutData,
  RefreshTokenData,
  ChangePasswordData,
} from '../types/user'

// ===== User Management =====

export function getUserList(params: UserListParams = {}) {
  return request.get<UserListResponse>('/users/', { params })
}

export function getUserDetail(userId: number) {
  return request.get<User>(`/users/${userId}`)
}

export function createUser(data: CreateUserData) {
  return request.post<User>('/users/', data)
}

export function updateUser(userId: number, data: UpdateUserData | FormData) {
  return request.put<User>(`/users/${userId}`, data)
}

export function deleteUser(userId: number) {
  return request.delete(`/users/${userId}`)
}

export function hardDeleteUser(userId: number) {
  return request.delete(`/users/${userId}/hard`)
}

// ===== Auth =====

export function login(data: LoginData) {
  return request.post<LoginResponse>('/users/login', data)
}

export function register(data: RegisterData) {
  return request.post<User>('/users/register', data)
}

export function logout(data: LogoutData = {}) {
  return request.post('/users/logout', data)
}

export function refreshToken(data: RefreshTokenData) {
  return request.post<LoginResponse>('/users/refresh-token', data)
}

export function changePassword(data: ChangePasswordData) {
  return request.post('/users/me/change-password', data)
}
