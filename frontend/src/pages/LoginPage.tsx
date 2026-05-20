import { useState, useCallback } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { login } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login: authLogin } = useAuth();
  const { showToast } = useToast();

  const [account, setAccount] = useState('');
  const [password, setPassword] = useState('');
  const [isRemember, setIsRemember] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError('');
      if (!account.trim() || !password.trim()) {
        setError('请填写账号和密码');
        return;
      }
      setIsSubmitting(true);
      try {
        const res = await login({ account, password, is_remember: isRemember });
        authLogin(res.user, res.access_token, res.refresh_token);
        showToast('登录成功', 'success');
        const redirect = searchParams.get('redirect');
        navigate(redirect ? decodeURIComponent(redirect) : '/');
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : '登录失败';
        setError(msg);
      } finally {
        setIsSubmitting(false);
      }
    },
    [account, password, isRemember, authLogin, navigate, searchParams, showToast]
  );

  return (
    <div
      className="min-h-[100dvh] flex relative overflow-hidden"
      style={{ backgroundColor: '#0a0806' }}
    >
      {/* ========== 左侧深黑装饰区（45%） ========== */}
      <motion.div
        className="hidden lg:flex lg:w-[45%] relative flex-col justify-center p-10"
        style={{ backgroundColor: '#0a0806' }}
        initial={{ x: -60, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* 中央品牌区 */}
        <div className="relative flex flex-col items-center text-center">
          {/* 大标题 */}
          <motion.h1
            className="text-6xl font-black tracking-tighter mb-4"
            style={{ fontFamily: 'var(--font-display)', color: '#F5A623', lineHeight: 0.9 }}
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            DE
            <br />
            <span style={{ color: '#FFF8EE' }}>hub</span>
          </motion.h1>

          {/* 装饰性标语 */}
          <motion.p
            className="text-xs tracking-[0.3em] mb-8"
            style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.45, duration: 0.5 }}
          >
            WELCOME BACK, SEEKER
          </motion.p>

          {/* 眼镜符号装饰 */}
          <motion.div
            className="flex items-center gap-3 mb-6"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.55, duration: 0.4 }}
          >
            <div className="h-px w-12" style={{ backgroundColor: 'rgba(245, 166, 35, 0.4)' }} />
            <span className="text-2xl" style={{ color: '#F5A623' }}>👓</span>
            <div className="h-px w-12" style={{ backgroundColor: 'rgba(245, 166, 35, 0.4)' }} />
          </motion.div>

          {/* 菱形网格装饰 */}
          <div className="flex gap-2">
            {[...Array(5)].map((_, i) => (
              <motion.div
                key={i}
                className="w-3 h-3"
                style={{
                  backgroundColor: i === 2 ? '#F5A623' : 'rgba(245, 166, 35, 0.15)',
                  clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
                }}
                initial={{ scale: 0, rotate: -45 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{ delay: 0.6 + i * 0.06, type: 'spring', stiffness: 300 }}
              />
            ))}
          </div>
        </div>


      </motion.div>

      {/* ========== 斜向分割线（仅 lg 显示） ========== */}
      <div
        className="hidden lg:block absolute left-[45%] top-0 bottom-0 w-px z-10"
        style={{
          background: 'linear-gradient(180deg, transparent, #F5A623, #7FE6EF, #C4D70C, #FF4D4D, transparent)',
          opacity: 0.6,
        }}
      />

      {/* ========== 右侧暖金表单区（55%） ========== */}
      <motion.div
        className="flex-1 lg:w-[55%] flex items-center justify-center relative px-6 py-12"
        style={{ backgroundColor: '#F5A623' }}
        initial={{ x: 60, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >


        {/* 表单卡片 */}
        <motion.div
          className="w-full max-w-sm"
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* 标题 */}
          <div className="mb-8">
            <h2
              className="text-3xl font-black tracking-tight mb-2"
              style={{ fontFamily: 'var(--font-display)', color: '#1A1612', lineHeight: 1 }}
            >
              SIGN IN
            </h2>
            <p
              className="text-xs tracking-wider"
              style={{ color: 'rgba(26,22,18,0.5)', fontFamily: 'var(--font-mono)' }}
            >
              身份验证 / AUTHENTICATION
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 账号 */}
            <motion.div
              initial={{ y: 16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              <label
                className="block text-[10px] tracking-widest mb-1.5 font-bold"
                style={{ color: 'rgba(26,22,18,0.6)', fontFamily: 'var(--font-mono)' }}
              >
                ACCOUNT / 账号
              </label>
              <input
                type="text"
                value={account}
                onChange={(e) => setAccount(e.target.value)}
                className="w-full px-4 py-3 text-sm outline-none input-focus-yellow"
                style={{
                  color: '#FFF8EE',
                  fontFamily: 'var(--font-body)',
                  backgroundColor: '#1A1612',
                }}
                placeholder="邮箱或用户名"
                data-cursor-hover
              />
            </motion.div>

            {/* 密码 */}
            <motion.div
              initial={{ y: 16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.48 }}
            >
              <label
                className="block text-[10px] tracking-widest mb-1.5 font-bold"
                style={{ color: 'rgba(26,22,18,0.6)', fontFamily: 'var(--font-mono)' }}
              >
                PASSWORD / 密码
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 text-sm outline-none input-focus-yellow"
                style={{
                  color: '#FFF8EE',
                  fontFamily: 'var(--font-body)',
                  backgroundColor: '#1A1612',
                }}
                placeholder="输入密码"
                data-cursor-hover
              />
            </motion.div>

            {/* 记住登录 */}
            <motion.div
              className="flex items-center gap-2"
              initial={{ y: 16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.56 }}
            >
              <button
                type="button"
                className="w-4 h-4 flex items-center justify-center transition-all duration-150"
                style={{
                  border: '2px solid rgba(26,22,18,0.3)',
                  backgroundColor: isRemember ? '#1A1612' : 'transparent',
                }}
                onClick={() => setIsRemember((v) => !v)}
                data-cursor-hover
              >
                {isRemember && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-2 h-2"
                    style={{ backgroundColor: '#FFE52C' }}
                  />
                )}
              </button>
              <span
                className="text-xs font-bold"
                style={{ color: 'rgba(26,22,18,0.6)', fontFamily: 'var(--font-body)' }}
              >
                记住登录
              </span>
            </motion.div>

            {/* 错误提示 */}
            <AnimatePresence>
              {error && (
                <motion.div
                  className="flex items-center gap-2 px-4 py-3"
                  style={{
                    backgroundColor: 'rgba(194, 35, 3, 0.9)',
                  }}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                >
                  <div className="w-1.5 h-1.5 rotate-45 shrink-0" style={{ backgroundColor: '#FFF8EE' }} />
                  <span className="text-xs font-bold" style={{ color: '#FFF8EE' }}>
                    {error}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* 登录按钮 */}
            <motion.div
              initial={{ y: 16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.64 }}
            >
              <motion.button
                type="submit"
                className="w-full py-3.5 text-sm font-black tracking-widest relative overflow-hidden"
                style={{
                  backgroundColor: '#1A1612',
                  color: '#FFE52C',
                  fontFamily: 'var(--font-display)',
                  clipPath: 'polygon(14px 0%, 100% 0%, 100% calc(100% - 14px), calc(100% - 14px) 100%, 0% 100%, 0% 14px)',
                }}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.92 }}
                disabled={isSubmitting}
                data-cursor-hover
              >
                <span className="relative z-10">{isSubmitting ? 'VERIFYING...' : 'ENTER SYSTEM'}</span>
                {/* 悬停波纹 */}
                <motion.div
                  className="absolute inset-0"
                  style={{ backgroundColor: '#2A2118' }}
                  initial={{ x: '-100%' }}
                  whileHover={{ x: 0 }}
                  transition={{ duration: 0.3 }}
                />
              </motion.button>
            </motion.div>
          </form>

          {/* 底部链接 */}
          <motion.div
            className="mt-8 flex items-center gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            <div className="h-px flex-1" style={{ backgroundColor: 'rgba(26,22,18,0.15)' }} />
            <span className="text-xs" style={{ color: 'rgba(26,22,18,0.5)' }}>
              没有账号？
            </span>
            <Link
              to="/register"
              className="text-xs font-black tracking-wider"
              style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
              data-cursor-hover
            >
              注册 →
            </Link>
            <div className="h-px flex-1" style={{ backgroundColor: 'rgba(26,22,18,0.15)' }} />
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}
