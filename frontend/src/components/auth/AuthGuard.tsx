import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const PUBLIC_PATHS = ['/login', '/register'];

interface AuthGuardProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

/**
 * 路由守卫
 * - 未登录访问受保护路由 → 重定向 /login?redirect=...
 * - 已登录访问 /login /register → 重定向 /
 * - 非管理员访问 /admin → 重定向 /
 */
export default function AuthGuard({ children, requireAdmin = false }: AuthGuardProps) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (isLoading) return;

    const isPublic = PUBLIC_PATHS.includes(location.pathname);

    // 已登录用户访问登录/注册页 → 跳首页
    if (isAuthenticated && isPublic) {
      navigate('/', { replace: true });
      return;
    }

    // 未登录用户访问非公开页 → 跳登录
    if (!isAuthenticated && !isPublic) {
      const redirect = encodeURIComponent(location.pathname + location.search);
      navigate(`/login?redirect=${redirect}`, { replace: true });
      return;
    }

    // 需要管理员权限
    if (requireAdmin && !isAdmin) {
      navigate('/', { replace: true });
      return;
    }
  }, [isAuthenticated, isAdmin, isLoading, location.pathname, location.search, navigate, requireAdmin]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#1A1612' }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rotate-45 border-2 border-[#F5A623] animate-pulse" />
          <span className="text-xs tracking-widest" style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}>
            LOADING...
          </span>
        </div>
      </div>
    );
  }

  // 未登录且访问公开页，或已登录且访问非公开页（且权限够），才渲染
  const isPublic = PUBLIC_PATHS.includes(location.pathname);

  if (!isAuthenticated && !isPublic) return null;
  if (isAuthenticated && isPublic) return null;
  if (requireAdmin && !isAdmin) return null;

  return <>{children}</>;
}
