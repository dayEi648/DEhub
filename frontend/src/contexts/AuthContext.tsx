import { createContext, useContext, useReducer, useEffect, useCallback, type ReactNode } from 'react';
import type { UserResponse } from '../api/types';
import { clearToken, setToken } from '../api/client';
import { refreshAccessToken } from '../api/auth';

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
}

type AuthAction =
  | { type: 'LOGIN'; payload: { user: UserResponse; token: string; refreshToken: string | null } }
  | { type: 'LOGOUT' }
  | { type: 'SET_USER'; payload: UserResponse | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'RESTORE'; payload: Partial<AuthState> };

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isAdmin: false,
  isLoading: true,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN': {
      const { user, token, refreshToken } = action.payload;
      return {
        ...state,
        user,
        token,
        refreshToken,
        isAuthenticated: true,
        isAdmin: user.permission >= 1,
        isLoading: false,
      };
    }
    case 'LOGOUT':
      clearToken();
      return { ...initialState, isLoading: false };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAdmin: action.payload ? action.payload.permission >= 1 : false,
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'RESTORE':
      return {
        ...state,
        ...action.payload,
        isAuthenticated: !!action.payload.token && !!action.payload.user,
        isAdmin: action.payload.user ? action.payload.user.permission >= 1 : false,
        isLoading: false,
      };
    default:
      return state;
  }
}

interface AuthContextValue extends AuthState {
  login: (user: UserResponse, token: string, refreshToken: string | null) => void;
  logout: () => void;
  setUser: (user: UserResponse | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // 初始化：尝试恢复登录态
  useEffect(() => {
    const init = async () => {
      const token = sessionStorage.getItem('access_token');
      const refresh = localStorage.getItem('refresh_token');
      const userStr = sessionStorage.getItem('user');

      if (token && userStr) {
        try {
          const user = JSON.parse(userStr) as UserResponse;
          dispatch({ type: 'RESTORE', payload: { token, refreshToken: refresh, user } });
          return;
        } catch {
          // parse error, fall through
        }
      }

      if (refresh) {
        try {
          const res = await refreshAccessToken(refresh);
          dispatch({
            type: 'LOGIN',
            payload: { user: res.user, token: res.access_token, refreshToken: res.refresh_token },
          });
          sessionStorage.setItem('user', JSON.stringify(res.user));
          return;
        } catch {
          // refresh failed, fall through
        }
      }

      dispatch({ type: 'SET_LOADING', payload: false });
    };

    init();
  }, []);

  // 监听全局 401 事件
  useEffect(() => {
    const handler = () => {
      dispatch({ type: 'LOGOUT' });
    };
    window.addEventListener('auth:unauthorized', handler);
    return () => window.removeEventListener('auth:unauthorized', handler);
  }, []);

  const login = useCallback((user: UserResponse, token: string, refreshToken: string | null) => {
    setToken(token);
    sessionStorage.setItem('user', JSON.stringify(user));
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    dispatch({ type: 'LOGIN', payload: { user, token, refreshToken } });
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem('user');
    dispatch({ type: 'LOGOUT' });
  }, []);

  const setUser = useCallback((user: UserResponse | null) => {
    if (user) sessionStorage.setItem('user', JSON.stringify(user));
    else sessionStorage.removeItem('user');
    dispatch({ type: 'SET_USER', payload: user });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
