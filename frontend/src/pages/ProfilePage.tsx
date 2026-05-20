import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { useLogout } from '../hooks/useLogout';
import { useToast } from '../components/ui/Toast';
import { updateUser } from '../api/user';
import { changePassword } from '../api/auth';
import { getPermissionInfo, formatDate } from '../utils/user';
import type { UserResponse } from '../api/types';

/* ============================================================
   P4 个人空间 — 终端控制台
   灵感来源：15. 滑块控制台 + 10. 对称舞台布景
   改造方向：将控制台概念与P4电视显像管美学融合，
   左侧为用户档案面板，右侧为显像管内容屏幕。
   ============================================================ */

type TabId = 'profile' | 'security';

interface TabDef {
  id: TabId;
  label: string;
  labelEn: string;
  color: string;
}

const TABS: TabDef[] = [
  { id: 'profile', label: '个人资料', labelEn: 'PROFILE', color: '#FFE52C' },
  { id: 'security', label: '账户安全', labelEn: 'SECURITY', color: '#FF4D4D' },
];

/* ============================================================
   电视换台转场
   ============================================================ */
function TVTransition({ children, tabKey }: { children: React.ReactNode; tabKey: string }) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={tabKey}
        initial={{ opacity: 0, scaleY: 0.015, filter: 'brightness(5)' }}
        animate={{ opacity: 1, scaleY: 1, filter: 'brightness(1)' }}
        exit={{ opacity: 0, scaleY: 0.015, filter: 'brightness(5)' }}
        transition={{ duration: 0.3, ease: [0.87, 0, 0.13, 1] }}
        style={{ transformOrigin: 'center center', height: '100%' }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

/* ============================================================
   主页面
   ============================================================ */
export default function ProfilePage() {
  const { user } = useAuth();
  const { handleLogout } = useLogout();
  const [activeTab, setActiveTab] = useState<TabId>('profile');
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setBooted(true), 100);
    return () => clearTimeout(t);
  }, []);

  const activeTabDef = useMemo(() => TABS.find(t => t.id === activeTab)!, [activeTab]);

  return (
    <div
      className="min-h-[100dvh] relative overflow-hidden flex flex-col"
      style={{ backgroundColor: '#0a0806' }}
    >
      {/* ===== 背景层 ===== */}
      <BackgroundLayer />

      {/* ===== 顶部 HUD ===== */}
      <TopBar user={user} onLogout={handleLogout} booted={booted} />

      {/* ===== 主内容区 ===== */}
      <main className="relative z-10 flex-1 flex items-stretch justify-center px-4 sm:px-6 lg:px-10 py-4 sm:py-6 gap-4 sm:gap-6 lg:gap-8" style={{ paddingTop: 72 }}>
        {/* 左侧档案面板 */}
        <motion.div
          className="hidden sm:flex flex-col shrink-0"
          style={{ width: 'clamp(260px, 32%, 380px)' }}
          initial={{ opacity: 0, x: -60 }}
          animate={booted ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
        >
          <ProfilePanel user={user} />
        </motion.div>

        {/* 斜向分割线（仅桌面） */}
        <div className="hidden lg:block shrink-0" style={{ width: 2, background: 'linear-gradient(180deg, transparent 0%, rgba(245,166,35,0.25) 20%, rgba(245,166,35,0.25) 80%, transparent 100%)' }} />

        {/* 右侧内容屏幕 */}
        <motion.div
          className="flex-1 flex flex-col min-w-0"
          initial={{ opacity: 0, x: 60 }}
          animate={booted ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.35 }}
        >
          <ContentScreen activeTab={activeTab} setActiveTab={setActiveTab} activeTabDef={activeTabDef} />
        </motion.div>
      </main>
    </div>
  );
}

/* ============================================================
   背景层
   ============================================================ */
function BackgroundLayer() {
  return (
    <>
      {/* 扫描线 */}
      <div
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.12) 2px, rgba(0,0,0,0.12) 4px)',
          opacity: 0.5,
        }}
      />
      {/* 中央微弱光晕 */}
      <div
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          background: 'radial-gradient(ellipse 60% 50% at 50% 50%, rgba(245,166,35,0.035) 0%, transparent 70%)',
        }}
      />
      {/* 底部装饰线 */}
      <div
        className="fixed bottom-0 left-0 right-0 h-px pointer-events-none z-0"
        style={{ backgroundColor: 'rgba(245, 166, 35, 0.12)' }}
      />
    </>
  );
}

/* ============================================================
   顶部 HUD 栏
   ============================================================ */
function TopBar({ user, onLogout, booted }: { user: UserResponse | null; onLogout: () => void; booted: boolean }) {
  return (
    <motion.header
      className="fixed top-0 left-0 right-0 z-30 flex items-center justify-between px-4 sm:px-6 lg:px-10"
      style={{
        height: 56,
        backgroundColor: 'rgba(10, 8, 6, 0.9)',
        borderBottom: '2px solid rgba(245, 166, 35, 0.15)',
      }}
      initial={{ opacity: 0, y: -30 }}
      animate={booted ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* 左侧：返回 + 彩条 */}
      <div className="flex items-center gap-3">
        <Link
          to="/"
          className="flex items-center gap-1.5 text-sm font-bold tracking-widest"
          style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
          data-cursor-hover
        >
          <span style={{ fontSize: 14 }}>←</span>
          <span className="hidden sm:inline">返回</span>
        </Link>
        <div className="hidden sm:block w-px h-4" style={{ backgroundColor: 'rgba(245,166,35,0.2)' }} />
        <div className="hidden sm:flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#F5A623' }} />
          <span className="text-xs tracking-wider" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
            PERSONAL SPACE
          </span>
        </div>
      </div>

      {/* 右侧：用户信息 + 退出 */}
      <div className="flex items-center gap-3">
        <span className="hidden md:inline text-sm" style={{ color: 'rgba(255,248,238,0.3)', fontFamily: 'var(--font-mono)' }}>
          {user?.username}
        </span>
        <div className="hidden md:block w-px h-4" style={{ backgroundColor: 'rgba(245,166,35,0.15)' }} />
        <span className="hidden lg:inline text-sm" style={{ color: 'rgba(255,248,238,0.25)', fontFamily: 'var(--font-mono)' }}>
          Lv.{user?.permission === 2 ? 'MAX' : user?.permission === 1 ? '2' : '1'}
        </span>
        <motion.button
          className="text-xs font-bold tracking-widest px-3 py-1.5"
          style={{
            color: '#FF4D4D',
            border: '1px solid rgba(255, 77, 77, 0.2)',
            fontFamily: 'var(--font-display)',
            clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
          }}
          whileHover={{ backgroundColor: 'rgba(194, 35, 3, 0.1)', borderColor: 'rgba(255, 77, 77, 0.4)' }}
          whileTap={{ scale: 0.92 }}
          onClick={onLogout}
          data-cursor-hover
        >
          退出
        </motion.button>
      </div>

    </motion.header>
  );
}

/* ============================================================
   左侧档案面板
   ============================================================ */
function ProfilePanel({ user }: { user: UserResponse | null }) {
  const perm = getPermissionInfo(user?.permission ?? 0);
  const roleText = perm.label;
  const roleColor = user?.permission === 2 ? '#FFE52C' : user?.permission === 1 ? '#F5A623' : '#7FE6EF';

  return (
    <div className="relative flex flex-col h-full" style={{ minHeight: 480 }}>
      {/* 面板外框 — 暖金粗边框 */}
      <div
        className="relative flex flex-col flex-1 overflow-hidden"
        style={{
          backgroundColor: 'rgba(26, 22, 18, 0.95)',
          border: '3px solid rgba(245, 166, 35, 0.35)',
          boxShadow: `
            inset 0 0 60px rgba(0,0,0,0.6),
            0 0 0 1px rgba(245,166,35,0.08),
            0 0 40px rgba(245,166,35,0.05)
          `,
        }}
      >
        {/* 屏幕反光 */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 40%, transparent 60%, rgba(255,255,255,0.02) 100%)',
          }}
        />

        {/* 内容区 */}
        <div className="relative flex flex-col items-center p-5 lg:p-6 flex-1 overflow-y-auto" style={{ scrollbarWidth: 'none' }}>
          {/* 菱形头像 */}
          <motion.div
            className="relative mb-4"
            initial={{ scale: 0, rotate: -45 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.5, type: 'spring', stiffness: 260, damping: 20 }}
          >
            <div
              className="absolute inset-0"
              style={{
                clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
                backgroundColor: '#F5A623',
                transform: 'scale(1.22)',
              }}
            />
            <div
              className="absolute inset-0"
              style={{
                clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
                backgroundColor: '#F7F3E8',
                transform: 'scale(1.12)',
              }}
            />
            <div
              className="relative w-20 h-20 lg:w-24 lg:h-24 flex items-center justify-center text-3xl font-bold overflow-hidden"
              style={{
                backgroundColor: '#2A2118',
                clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
              }}
            >
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
              ) : (
                <span style={{ color: '#F5A623' }}>{user?.username?.[0]?.toUpperCase() ?? '?'}</span>
              )}
            </div>
          </motion.div>

          {/* 用户名 */}
          <motion.h1
            className="text-2xl lg:text-3xl font-bold tracking-tight text-center mb-1"
            style={{ fontFamily: 'var(--font-display)', color: '#FFF8EE', lineHeight: 1, transform: 'rotate(-1deg)' }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.4 }}
          >
            {user?.username ?? '未知用户'}
          </motion.h1>

          {/* 角色标签 */}
          <motion.div
            className="text-xs font-semibold tracking-widest px-3 py-1 mb-4"
            style={{
              backgroundColor: `${roleColor}18`,
              color: roleColor,
              border: `1px solid ${roleColor}40`,
              fontFamily: 'var(--font-mono)',
              clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7, duration: 0.3 }}
          >
            {roleText}
          </motion.div>

          {/* 分割线 */}
          <motion.div
            className="w-20 h-px mb-4"
            style={{ background: 'linear-gradient(90deg, transparent, #F5A623, transparent)', opacity: 0.5 }}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.75, duration: 0.4 }}
          />

          {/* 数据列表 */}
          <div className="w-full space-y-1.5 mb-4">
            <DataRow label="邮箱" value={user?.email ?? '----'} delay={0.86} />
            <DataRow label="注册时间" value={formatDate(user?.created_at)} delay={0.92} />
            <DataRow label="个人简介" value={user?.personal_profile ? user.personal_profile.slice(0, 20) + (user.personal_profile.length > 20 ? '...' : '') : '暂无数据'} delay={0.98} />
          </div>


        </div>

        {/* 屏幕边缘阴影 */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ boxShadow: 'inset 0 0 30px rgba(0,0,0,0.5)' }}
        />
      </div>
    </div>
  );
}

/* ============================================================
   数据行组件
   ============================================================ */
function DataRow({ label, value, delay }: { label: string; value: string; delay: number }) {
  return (
    <motion.div
      className="flex items-center justify-between px-3 py-2"
      style={{ backgroundColor: 'rgba(245, 166, 35, 0.05)' }}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, duration: 0.4 }}
    >
      <span className="text-xs tracking-wider" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
        {label}
      </span>
      <span className="text-sm font-semibold tracking-tight truncate ml-2 max-w-[140px]" style={{ color: '#FFF8EE', fontFamily: 'var(--font-mono)' }}>
        {value}
      </span>
    </motion.div>
  );
}


/* ============================================================
   右侧内容屏幕
   ============================================================ */
function ContentScreen({ activeTab, setActiveTab, activeTabDef }: {
  activeTab: TabId;
  setActiveTab: (t: TabId) => void;
  activeTabDef: TabDef;
}) {
  return (
    <div className="relative flex flex-col h-full" style={{ minHeight: 480 }}>
      {/* 显像管屏幕外框 */}
      <div
        className="relative flex flex-col flex-1 overflow-hidden"
        style={{
          backgroundColor: 'rgba(26, 22, 18, 0.95)',
          border: '3px solid rgba(245, 166, 35, 0.3)',
          boxShadow: `
            inset 0 0 60px rgba(0,0,0,0.6),
            0 0 0 1px rgba(245,166,35,0.08),
            0 0 40px rgba(245,166,35,0.05)
          `,
        }}
      >
        {/* 屏幕反光 */}
        <div
          className="absolute inset-0 pointer-events-none z-[5]"
          style={{
            background: 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, transparent 40%, transparent 60%, rgba(255,255,255,0.02) 100%)',
          }}
        />

        {/* 导航选项卡 */}
        <TabBar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* 内容区 */}
        <div className="relative flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-5 lg:p-6" style={{ scrollbarWidth: 'none' }}>
          {/* 当前模块标题 */}
          <motion.div
            className="mb-5"
            key={`title-${activeTab}`}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05, duration: 0.3 }}
          >
            <div className="flex items-center gap-3 mb-1">
              <div className="w-2 h-2 rotate-45 shrink-0" style={{ backgroundColor: activeTabDef.color }} />
              <h2
                className="text-xl sm:text-2xl font-bold tracking-tight"
                style={{ fontFamily: 'var(--font-display)', color: activeTabDef.color, lineHeight: 1, transform: 'rotate(-0.5deg)' }}
              >
                {activeTabDef.labelEn}
              </h2>
            </div>
            <p className="text-sm tracking-wider ml-5" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
              {activeTabDef.label}
            </p>
          </motion.div>

          {/* 分割线 */}
          <motion.div
            className="w-full h-px mb-5"
            style={{ background: 'linear-gradient(90deg, transparent, rgba(245,166,35,0.25), transparent)', opacity: 0.5 }}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.1, duration: 0.4 }}
          />

          {/* 内容 */}
          <TVTransition tabKey={activeTab}>
            {activeTab === 'profile' && <ProfileEditTab />}
            {activeTab === 'security' && <SecurityTab />}
          </TVTransition>
        </div>

        {/* 屏幕边缘阴影 */}
        <div
          className="absolute inset-0 pointer-events-none z-[6]"
          style={{ boxShadow: 'inset 0 0 30px rgba(0,0,0,0.5)' }}
        />
      </div>
    </div>
  );
}

/* ============================================================
   选项卡导航栏
   ============================================================ */
function TabBar({ activeTab, setActiveTab }: { activeTab: TabId; setActiveTab: (t: TabId) => void }) {
  return (
    <div className="relative flex shrink-0" style={{ borderBottom: '1px solid rgba(245, 166, 35, 0.12)' }}>
      {TABS.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <motion.button
            key={tab.id}
            className="relative flex-1 flex items-center justify-center gap-2 py-3 sm:py-3.5 outline-none cursor-pointer"
            style={{
              backgroundColor: isActive ? tab.color : 'transparent',
              color: isActive ? '#1A1612' : 'rgba(255,248,238,0.5)',
              fontFamily: 'var(--font-mono)',
            }}
            onClick={() => setActiveTab(tab.id)}
            data-cursor-hover
            whileHover={!isActive ? { backgroundColor: 'rgba(245,166,35,0.08)' } : {}}
            whileTap={{ scale: 0.98 }}
          >
            <span className="text-sm sm:text-base font-semibold tracking-widest">
              {tab.labelEn}
            </span>
            {/* 未选中时的竖线分隔 */}
            {!isActive && (
              <div className="absolute right-0 top-1/4 h-1/2 w-px" style={{ backgroundColor: 'rgba(245,166,35,0.1)' }} />
            )}
          </motion.button>
        );
      })}
      {/* 底部选中指示条 */}
      <motion.div
        className="absolute bottom-0 h-0.5"
        animate={{
          left: `${TABS.findIndex(t => t.id === activeTab) * (100 / TABS.length)}%`,
          width: `${100 / TABS.length}%`,
          backgroundColor: TABS.find(t => t.id === activeTab)?.color || '#F5A623',
        }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      />
    </div>
  );
}

/* ============================================================
   PROFILE — 个人资料编辑
   ============================================================ */
function ProfileEditTab() {
  const { user, setUser } = useAuth();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [editUser, setEditUser] = useState<UserResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user) setEditUser({ ...user });
  }, [user]);

  const handleSave = useCallback(async () => {
    if (!editUser || !user) return;
    setLoading(true);
    try {
      const updated = await updateUser(user.id, {
        username: editUser.username,
        email: editUser.email,
        personal_profile: editUser.personal_profile ?? undefined,
      });
      setUser(updated);
      showToast('资料已更新', 'success');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '更新失败';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  }, [editUser, user, setUser, showToast]);

  const handleAvatarChange = useCallback(async (file: File) => {
    if (!user) return;
    setLoading(true);
    try {
      const updated = await updateUser(user.id, {}, file);
      setUser(updated);
      showToast('头像已更新', 'success');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '上传失败';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  }, [user, setUser, showToast]);

  if (!editUser) return null;

  return (
    <div className="flex flex-col gap-4">
      {/* 头像上传 */}
      <motion.div
        className="flex items-center gap-4"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <motion.button
          className="relative shrink-0"
          onClick={() => fileInputRef.current?.click()}
          data-cursor-hover
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <div
            className="absolute inset-0"
            style={{
              clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
              backgroundColor: '#F5A623',
              transform: 'scale(1.18)',
            }}
          />
          <div
            className="relative w-14 h-14 flex items-center justify-center text-lg font-bold overflow-hidden"
            style={{
              backgroundColor: '#2A2118',
              clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
            }}
          >
            {editUser.avatar_url ? (
              <img src={editUser.avatar_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <span style={{ color: '#F5A623' }}>{editUser.username[0]?.toUpperCase()}</span>
            )}
          </div>
        </motion.button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleAvatarChange(file);
          }}
        />
        <div className="flex flex-col">
          <span className="text-base font-bold" style={{ color: '#FFF8EE', fontFamily: 'var(--font-display)' }}>
            {editUser.username}
          </span>
          <span className="text-xs tracking-wider" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
            点击头像更换
          </span>
        </div>
      </motion.div>

      {/* 分割线 */}
      <div className="w-full h-px" style={{ background: 'linear-gradient(90deg, rgba(245,166,35,0.15), transparent)' }} />

      {/* 表单 */}
      <div className="space-y-3">
        <FormField
          label="用户名"
          value={editUser.username}
          onChange={(v) => setEditUser((u) => (u ? { ...u, username: v } : u))}
          delay={0.15}
        />
        <FormField
          label="邮箱"
          value={editUser.email}
          onChange={(v) => setEditUser((u) => (u ? { ...u, email: v } : u))}
          delay={0.22}
        />
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.29 }}>
          <label
            className="block text-xs tracking-widest mb-2 font-semibold"
            style={{ fontFamily: 'var(--font-mono)', color: 'rgba(255,248,238,0.5)' }}
          >
            个人简介
          </label>
          <textarea
            value={editUser.personal_profile || ''}
            onChange={(e) => setEditUser((u) => (u ? { ...u, personal_profile: e.target.value } : u))}
            rows={3}
            className="w-full px-3 py-2.5 text-sm outline-none resize-none input-focus-amber"
            style={{
              color: '#FFF8EE',
              fontFamily: 'var(--font-body)',
              backgroundColor: 'rgba(10, 8, 6, 0.85)',
              border: '1px solid rgba(245, 166, 35, 0.15)',
            }}
            placeholder="介绍一下自己..."
            data-cursor-hover
          />
        </motion.div>

        {/* 保存按钮 */}
        <motion.button
          className="relative w-full py-2.5 text-sm font-bold tracking-widest mt-2 overflow-hidden"
          style={{
            backgroundColor: '#F5A623',
            color: '#1A1612',
            fontFamily: 'var(--font-display)',
            clipPath: 'polygon(10px 0%, 100% 0%, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0% 100%, 0% 10px)',
          }}
          whileHover={{ scale: 1.02, backgroundColor: '#FFE52C' }}
          whileTap={{ scale: 0.94 }}
          onClick={handleSave}
          disabled={loading}
          data-cursor-hover
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.36 }}
        >
          {loading ? '保存中...' : '保存更改'}
        </motion.button>
      </div>

      {/* 底部信息面板 */}
      <motion.div
        className="mt-2 px-4 py-3"
        style={{
          backgroundColor: 'rgba(245, 166, 35, 0.04)',
          border: '1px solid rgba(245, 166, 35, 0.08)',
          clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.45 }}
      >
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1 h-1 rotate-45 shrink-0" style={{ backgroundColor: '#7FE6EF' }} />
          <span className="text-xs tracking-widest font-semibold" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
            账户信息
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <InfoItem label="权限" value={getPermissionInfo(user?.permission ?? 0).label} />
          <InfoItem label="注册时间" value={formatDate(user?.created_at)} />
          <InfoItem label="状态" value="活跃" />
        </div>
      </motion.div>
    </div>
  );
}

/* ============================================================
   表单字段组件
   ============================================================ */
function FormField({ label, value, onChange, delay, type = 'text' }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  delay: number;
  type?: string;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}>
      <label
        className="block text-xs tracking-widest mb-2 font-semibold"
        style={{ fontFamily: 'var(--font-mono)', color: 'rgba(255,248,238,0.5)' }}
      >
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 text-sm outline-none input-focus-amber"
        style={{
          color: '#FFF8EE',
          fontFamily: 'var(--font-body)',
          backgroundColor: 'rgba(10, 8, 6, 0.85)',
          border: '1px solid rgba(245, 166, 35, 0.15)',
        }}
        data-cursor-hover
      />
    </motion.div>
  );
}


/* ============================================================
   SECURITY — 账户安全
   ============================================================ */
function SecurityTab() {
  const { showToast } = useToast();
  const { logout: authLogout } = useAuth();
  const navigate = useNavigate();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (newPassword.length < 6 || newPassword.length > 128) {
      errs.newPassword = '密码长度需在 6~128 字符之间';
    }
    if (newPassword !== confirmPassword) {
      errs.confirmPassword = '两次输入的密码不一致';
    }
    if (newPassword === oldPassword && oldPassword) {
      errs.newPassword = '新密码不能与旧密码相同';
    }
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setLoading(true);
    try {
      await changePassword({ old_password: oldPassword, new_password: newPassword });
      showToast('密码已修改，请重新登录', 'success');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      authLogout();
      navigate('/login');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '修改失败';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  }, [oldPassword, newPassword, confirmPassword, showToast, authLogout, navigate]);

  return (
    <div className="flex flex-col gap-4">
      {/* 警告提示 */}
      <motion.div
        className="flex items-start gap-2.5 px-3 py-2.5"
        style={{
          backgroundColor: 'rgba(194, 35, 3, 0.08)',
          border: '1px solid rgba(194, 35, 3, 0.15)',
          clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
        }}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
      >
        <span className="text-sm shrink-0" style={{ color: '#FF4D4D' }}>▲</span>
        <div>
          <span className="text-sm font-bold block mb-1" style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}>
            安全提示
          </span>
          <span className="text-xs" style={{ color: 'rgba(255,248,238,0.4)' }}>
            修改密码后需要重新登录
          </span>
        </div>
      </motion.div>

      {/* 表单 */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <PasswordField label="旧密码" value={oldPassword} onChange={setOldPassword} error={errors.oldPassword} delay={0.1} />
        <PasswordField label="新密码" value={newPassword} onChange={setNewPassword} error={errors.newPassword} delay={0.17} />
        <PasswordField label="确认密码" value={confirmPassword} onChange={setConfirmPassword} error={errors.confirmPassword} delay={0.24} />

        <motion.button
          type="submit"
          className="relative w-full py-2.5 text-sm font-bold tracking-widest mt-2 overflow-hidden"
          style={{
            backgroundColor: '#C22303',
            color: '#FFF8EE',
            fontFamily: 'var(--font-display)',
            clipPath: 'polygon(10px 0%, 100% 0%, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0% 100%, 0% 10px)',
          }}
          whileHover={{ scale: 1.02, backgroundColor: '#FF4D4D' }}
          whileTap={{ scale: 0.94 }}
          disabled={loading}
          data-cursor-hover
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.31 }}
        >
          {loading ? '更新中...' : '修改密码'}
        </motion.button>
      </form>

      {/* 安全建议 */}
      <motion.div
        className="mt-2 px-4 py-3"
        style={{
          backgroundColor: 'rgba(127, 230, 239, 0.04)',
          border: '1px solid rgba(127, 230, 239, 0.08)',
          clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1 h-1 rotate-45 shrink-0" style={{ backgroundColor: '#7FE6EF' }} />
          <span className="text-xs tracking-widest font-semibold" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
            安全建议
          </span>
        </div>
        <ul className="space-y-1">
          <SecurityTip text="密码长度建议 12 位以上" />
          <SecurityTip text="混合使用大小写字母、数字和符号" />
          <SecurityTip text="避免使用与个人信息相关的密码" />
        </ul>
      </motion.div>
    </div>
  );
}

/* ============================================================
   密码字段组件
   ============================================================ */
function PasswordField({ label, value, onChange, error, delay }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
  delay: number;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}>
      <label
        className="block text-xs tracking-widest mb-2 font-semibold"
        style={{ fontFamily: 'var(--font-mono)', color: 'rgba(255,248,238,0.5)' }}
      >
        {label}
      </label>
      <input
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full px-3 py-2.5 text-sm outline-none ${error ? 'input-focus-amber-error' : 'input-focus-amber'}`}
        style={{
          color: '#FFF8EE',
          fontFamily: 'var(--font-body)',
          backgroundColor: 'rgba(10, 8, 6, 0.85)',
          border: error ? undefined : '1px solid rgba(245, 166, 35, 0.15)',
        }}
        data-cursor-hover
      />
      {error && (
        <div className="flex items-center gap-1.5 mt-1.5">
          <div className="w-1 h-1 rotate-45 shrink-0" style={{ backgroundColor: '#FF4D4D' }} />
          <span className="text-xs" style={{ color: '#FF4D4D' }}>{error}</span>
        </div>
      )}
    </motion.div>
  );
}


/* ============================================================
   InfoItem — 信息项（用于底部面板）
   ============================================================ */
function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs tracking-widest mb-1" style={{ color: 'rgba(255,248,238,0.3)', fontFamily: 'var(--font-mono)' }}>
        {label}
      </span>
      <span className="text-sm font-semibold tracking-tight truncate" style={{ color: '#FFF8EE', fontFamily: 'var(--font-mono)' }}>
        {value}
      </span>
    </div>
  );
}

/* ============================================================
   SecurityTip — 安全提示项
   ============================================================ */
function SecurityTip({ text }: { text: string }) {
  return (
    <li className="flex items-center gap-1.5">
      <div className="w-0.5 h-0.5 rotate-45 shrink-0" style={{ backgroundColor: '#7FE6EF' }} />
      <span className="text-sm" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-body)' }}>
        {text}
      </span>
    </li>
  );
}
