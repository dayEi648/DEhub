/** ============================================================
 *  用户相关接口类型定义
 *  依据 planing/接口文档/用户接口文档.md
 *  ============================================================ */

/** 用户响应 */
export interface UserResponse {
  id: number;
  username: string;
  email: string;
  created_at: string;
  permission: number;
  is_deleted: boolean;
  avatar_url: string | null;
  personal_profile: string | null;
}

/** 用户列表响应 */
export interface UserListResponse {
  items: UserResponse[];
  total: number;
}

/** 登录请求 */
export interface UserLogin {
  account: string;
  password: string;
  is_remember?: boolean;
}

/** 登录响应 */
export interface UserLoginResponse {
  access_token: string;
  refresh_token: string | null;
  token_type: string;
  user: UserResponse;
  access_token_expires_in: number;
  refresh_token_expires_in: number | null;
}

/** 注册请求 */
export interface UserRegister {
  username: string;
  email: string;
  password: string;
}

/** 登出请求 */
export interface UserLogout {
  refresh_token?: string;
}

/** 刷新令牌请求 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

/** 用户更新请求（全可选） */
export interface UserUpdate {
  username?: string;
  email?: string;
  password?: string;
  permission?: number;
  avatar_url?: string;
  personal_profile?: string;
}

/** 创建用户请求 */
export interface UserCreate {
  username: string;
  email: string;
  password: string;
  permission?: number;
  avatar_url?: string;
  personal_profile?: string;
}

/** 标准错误响应 */
export interface ApiError {
  code: number;
  message: string;
  detail?: unknown;
}

/** 管理后台页面标识 */
export type AdminPage = 'users' | 'forum-zones' | 'logs';
