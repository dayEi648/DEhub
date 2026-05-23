export type UserPermission = 0 | 1 | 2

export interface UserBriefInfo {
  id: number
  username: string
  avatar_url: string | null
}

export interface User {
  id: number
  username: string
  email: string
  created_at: string
  permission: UserPermission
  is_deleted: boolean
  avatar_url: string | null
  personal_profile: string | null
}

export interface UserListResponse {
  items: User[]
  total: number
}

export interface UserListParams {
  skip?: number
  limit?: number
  include_deleted?: boolean
  username?: string
  email?: string
  permission?: UserPermission
}

export interface CreateUserData {
  username: string
  email: string
  password: string
  permission?: UserPermission
  personal_profile?: string
}

export interface UpdateUserData {
  username?: string
  email?: string
  password?: string
  permission?: UserPermission
  personal_profile?: string
}

export interface LoginData {
  account: string
  password: string
  is_remember?: boolean
}

export interface LoginResponse {
  access_token: string
  refresh_token: string | null
  token_type: string
  user: User
  access_token_expires_in: number
  refresh_token_expires_in: number | null
}

export interface RegisterData {
  username: string
  email: string
  password: string
  personal_profile?: string
}

export interface ChangePasswordData {
  old_password: string
  new_password: string
}

export interface LogoutData {
  refresh_token?: string
}

export interface RefreshTokenData {
  refresh_token: string
}
