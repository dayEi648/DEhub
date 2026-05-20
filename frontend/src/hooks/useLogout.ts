import { useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { logout as apiLogout } from '../api/auth';
import { useToast } from '../components/ui/Toast';

/**
 * 封装登出逻辑：调用后端注销、清除本地状态、显示提示
 */
export function useLogout() {
  const { logout: authLogout } = useAuth();
  const { showToast } = useToast();

  const handleLogout = useCallback(async () => {
    try {
      const rt = localStorage.getItem('refresh_token') || undefined;
      await apiLogout(rt);
    } catch {
      // ignore
    } finally {
      authLogout();
      showToast('已登出', 'info');
    }
  }, [authLogout, showToast]);

  return { handleLogout };
}
