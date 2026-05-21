import { apiFetch, buildQueryString } from './client';
import type {
  UserResponse,
  UserListResponse,
  UserUpdate,
  UserCreate,
} from './types';

export async function listUsers(params?: {
  skip?: number;
  limit?: number;
  include_deleted?: boolean;
  username?: string;
  email?: string;
  permission?: number;
}): Promise<UserListResponse> {
  return apiFetch<UserListResponse>(`/api/v1/users/${buildQueryString(params ?? {})}`);
}

export async function createUser(data: UserCreate): Promise<UserResponse> {
  return apiFetch<UserResponse>('/api/v1/users/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateUser(
  userId: number,
  data: UserUpdate,
  file?: File
): Promise<UserResponse> {
  const formData = new FormData();
  formData.append('user_in', JSON.stringify(data));
  if (file) {
    formData.append('file', file);
  }
  return apiFetch<UserResponse>(`/api/v1/users/${userId}`, {
    method: 'PUT',
    body: formData,
  });
}

export async function softDeleteUser(userId: number): Promise<void> {
  return apiFetch<void>(`/api/v1/users/${userId}`, {
    method: 'DELETE',
  });
}

export async function hardDeleteUser(userId: number): Promise<void> {
  return apiFetch<void>(`/api/v1/users/${userId}/hard`, {
    method: 'DELETE',
  });
}
