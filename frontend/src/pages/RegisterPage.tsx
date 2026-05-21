import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { register, login } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const { showToast } = useToast();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = useCallback((): boolean => {
    const errs: Record<string, string> = {};
    if (username.length < 3 || username.length > 64) {
      errs.username = '用户名长度需在 3~64 字符之间';
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errs.email = '请输入有效的邮箱地址';
    }
    if (password.length < 6 || password.length > 128) {
      errs.password = '密码长度需在 6~128 字符之间';
    }
    if (password !== confirmPassword) {
      errs.confirmPassword = '两次输入的密码不一致';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }, [username, email, password, confirmPassword]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validate()) return;
      setIsSubmitting(true);
      try {
        await register({ username, email, password });
        try {
          const res = await login({ account: username, password });
          authLogin(res.user, res.access_token, res.refresh_token);
          showToast('注册成功，已自动登录', 'success');
          navigate('/');
        } catch (loginErr: unknown) {
          const msg = loginErr instanceof Error ? loginErr.message : '登录失败';
          setErrors({ general: `注册成功，但自动登录失败：${msg}` });
        }
      } catch (regErr: unknown) {
        const msg = regErr instanceof Error ? regErr.message : '注册失败';
        setErrors({ general: msg });
      } finally {
        setIsSubmitting(false);
      }
    },
    [username, email, password, validate, authLogin, navigate, showToast]
  );

  const fields = [
    { label: 'USERNAME / 用户名', value: username, setter: setUsername, name: 'username', type: 'text', placeholder: '请输入用户名' },
    { label: 'EMAIL / 邮箱', value: email, setter: setEmail, name: 'email', type: 'email', placeholder: '请输入邮箱' },
    { label: 'PASSWORD / 密码', value: password, setter: setPassword, name: 'password', type: 'password', placeholder: '请输入密码' },
    { label: 'CONFIRM / 确认密码', value: confirmPassword, setter: setConfirmPassword, name: 'confirmPassword', type: 'password', placeholder: '请再次输入密码' },
  ];

  /** 单个字段 blur 校验 */
  const validateFieldOnBlur = useCallback((name: string, value: string) => {
    const fieldErrors: Record<string, string> = {};
    if (name === 'username') {
      if (value.length > 0 && (value.length < 3 || value.length > 64)) {
        fieldErrors.username = '用户名长度需在 3~64 字符之间';
      }
    } else if (name === 'email') {
      if (value.length > 0 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        fieldErrors.email = '请输入有效的邮箱地址';
      }
    } else if (name === 'password') {
      if (value.length > 0 && (value.length < 6 || value.length > 128)) {
        fieldErrors.password = '密码长度需在 6~128 字符之间';
      }
    } else if (name === 'confirmPassword') {
      if (value.length > 0 && value !== password) {
        fieldErrors.confirmPassword = '两次输入的密码不一致';
      }
    }
    setErrors((prev) => ({ ...prev, ...fieldErrors, general: '' }));
  }, [password]);

  return (
    <div
      className="min-h-[100dvh] flex relative overflow-hidden"
      style={{ backgroundColor: '#0a0806' }}
    >
      {/* ========== 左侧暖金表单区（60%） ========== */}
      <motion.div
        className="flex-1 lg:w-[60%] flex items-center justify-center relative px-6 py-12"
        style={{ backgroundColor: '#F5A623' }}
        initial={{ x: -60, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >


        {/* 表单卡片 */}
        <motion.div
          className="w-full max-w-md"
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
              JOIN US
            </h2>
            <p
              className="text-xs tracking-wider"
              style={{ color: 'rgba(26,22,18,0.5)', fontFamily: 'var(--font-mono)' }}
            >
              新用户注册 / REGISTRATION
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {fields.map((field, i) => (
              <motion.div
                key={field.name}
                initial={{ y: 16, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 + i * 0.07 }}
              >
                <label
                  className="block text-[10px] tracking-widest mb-1.5 font-bold"
                  style={{ color: 'rgba(26,22,18,0.6)', fontFamily: 'var(--font-mono)' }}
                >
                  {field.label}
                </label>
                <input
                  type={field.type}
                  value={field.value}
                  onChange={(e) => {
                    field.setter(e.target.value);
                    setErrors((prev) => ({ ...prev, [field.name]: '', general: '' }));
                  }}
                  className={`w-full px-4 py-3 text-sm outline-none transition-all duration-200 ${errors[field.name] ? 'input-focus-yellow-error' : 'input-focus-yellow'}`}
                  style={{
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                    backgroundColor: '#1A1612',
                  }}
                  placeholder={field.placeholder}
                  data-cursor-hover
                  onBlur={(e) => {
                    validateFieldOnBlur(field.name, e.target.value);
                  }}
                />
                <AnimatePresence>
                  {errors[field.name] && (
                    <motion.div
                      className="flex items-center gap-1.5 mt-1.5"
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                    >
                      <div className="w-1.5 h-1.5 rotate-45 shrink-0" style={{ backgroundColor: '#C22303' }} />
                      <span className="text-[11px] font-bold" style={{ color: '#C22303' }}>
                        {errors[field.name]}
                      </span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}

            {/* 全局错误 */}
            <AnimatePresence>
              {errors.general && (
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
                    {errors.general}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* 注册按钮 */}
            <motion.div
              initial={{ y: 16, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.72 }}
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
                <span className="relative z-10">{isSubmitting ? 'PROCESSING...' : 'CREATE ACCOUNT'}</span>
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
            transition={{ delay: 0.9 }}
          >
            <div className="h-px flex-1" style={{ backgroundColor: 'rgba(26,22,18,0.15)' }} />
            <span className="text-xs" style={{ color: 'rgba(26,22,18,0.5)' }}>
              已有账号？
            </span>
            <Link
              to="/login"
              className="text-xs font-black tracking-wider"
              style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
              data-cursor-hover
            >
              直接登录 →
            </Link>
            <div className="h-px flex-1" style={{ backgroundColor: 'rgba(26,22,18,0.15)' }} />
          </motion.div>
        </motion.div>
      </motion.div>

      {/* ========== 斜向分割线（仅 lg 显示） ========== */}
      <div
        className="hidden lg:block absolute left-[60%] top-0 bottom-0 w-px z-10"
        style={{
          background: 'linear-gradient(180deg, transparent, #C4D70C, #7FE6EF, #F5A623, #FF4D4D, transparent)',
          opacity: 0.6,
        }}
      />

      {/* ========== 右侧深黑装饰区（40%） ========== */}
      <motion.div
        className="hidden lg:flex lg:w-[40%] relative flex-col justify-center p-10"
        style={{ backgroundColor: '#0a0806' }}
        initial={{ x: 60, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* 中央品牌区 */}
        <div className="relative flex flex-col items-center text-center">
          <motion.h1
            className="text-6xl font-black tracking-tighter mb-4"
            style={{ fontFamily: 'var(--font-display)', color: '#F5A623', lineHeight: 0.9 }}
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            NEW
            <br />
            <span style={{ color: '#FFF8EE' }}>FACE</span>
          </motion.h1>

          <motion.p
            className="text-xs tracking-[0.3em] mb-8"
            style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.45, duration: 0.5 }}
          >
            STEP INTO THE SIGNAL
          </motion.p>

          {/* 眼镜符号装饰 */}
          <motion.div
            className="flex items-center gap-3 mb-6"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.55, duration: 0.4 }}
          >
            <div className="h-px w-12" style={{ backgroundColor: 'rgba(245, 166, 35, 0.4)' }} />
            <span className="text-2xl" style={{ color: '#F5A623' }}>◈</span>
            <div className="h-px w-12" style={{ backgroundColor: 'rgba(245, 166, 35, 0.4)' }} />
          </motion.div>

          {/* 菱形网格装饰 */}
          <div className="flex gap-2">
            {[...Array(5)].map((_, i) => (
              <motion.div
                key={i}
                className="w-3 h-3"
                style={{
                  backgroundColor: i === 2 ? '#7FE6EF' : 'rgba(127, 230, 239, 0.2)',
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
    </div>
  );
}
