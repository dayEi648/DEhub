import type { ApiError } from './types';

const BASE_URL = '';

function getToken(): string | null {
  return sessionStorage.getItem('access_token');
}

export function setToken(token: string) {
  sessionStorage.setItem('access_token', token);
}

export function clearToken() {
  sessionStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

function buildUrl(path: string): string {
  if (path.startsWith('http')) return path;
  return `${BASE_URL}${path}`;
}

export class ApiErrorException extends Error {
  code: number;
  detail?: unknown;

  constructor(error: ApiError) {
    super(error.message);
    this.name = 'ApiErrorException';
    this.code = error.code;
    this.detail = error.detail;
  }
}

async function parseError(res: Response): Promise<ApiErrorException> {
  let err: ApiError;
  try {
    err = await res.json();
  } catch {
    err = { code: res.status, message: res.statusText || '未知错误' };
  }
  return new ApiErrorException(err);
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = buildUrl(path);
  const headers = new Headers(options.headers);

  if (!headers.has('Authorization')) {
    const token = getToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const exc = await parseError(res);
    if (exc.code === 401) {
      clearToken();
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }
    throw exc;
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
