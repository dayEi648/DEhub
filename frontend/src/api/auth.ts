import { apiFetch, setToken, clearToken } from './client';
import type {
  UserLogin,
  UserLoginResponse,
  UserRegister,
  UserResponse,
  UserLogout,
  RefreshTokenRequest,
  ChangePasswordRequest,
} from './types';

export async function login(data: UserLogin): Promise<UserLoginResponse> {
  const res = await apiFetch<UserLoginResponse>('/api/v1/users/login', {
    method: 'POST',
    body: JSON.stringify(data),
    skipAuth: true,
  });
  setToken(res.access_token);
  if (data.is_remember && res.refresh_token) {
    localStorage.setItem('refresh_token', res.refresh_token);
  }
  return res;
}

export async function register(data: UserRegister): Promise<UserResponse> {
  return apiFetch<UserResponse>('/api/v1/users/register', {
    method: 'POST',
    body: JSON.stringify(data),
    skipAuth: true,
  });
}

export async function logout(refreshToken?: string): Promise<void> {
  const body: UserLogout = {};
  if (refreshToken) body.refresh_token = refreshToken;
  try {
    await apiFetch<void>('/api/v1/users/logout', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  } finally {
    clearToken();
  }
}

export async function refreshAccessToken(refreshToken: string): Promise<UserLoginResponse> {
  const req: RefreshTokenRequest = { refresh_token: refreshToken };
  const res = await apiFetch<UserLoginResponse>('/api/v1/users/refresh-token', {
    method: 'POST',
    body: JSON.stringify(req),
    skipAuth: true,
  });
  setToken(res.access_token);
  if (res.refresh_token) {
    localStorage.setItem('refresh_token', res.refresh_token);
  }
  return res;
}

export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  return apiFetch<void>('/api/v1/users/me/change-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
