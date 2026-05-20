import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { listUsers, updateUser, softDeleteUser, hardDeleteUser, createUser } from '../../api/user';
import { useToast } from '../../components/ui/Toast';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import Pagination from '../../components/ui/Pagination';
import AdminShell from '../../components/layout/AdminShell';
import { getPermissionInfo, formatDate } from '../../utils/user';
import type { UserResponse } from '../../api/types';

export default function AdminUsersPage() {
  return (
    <AdminShell activePage="users">
      <UsersContent />
    </AdminShell>
  );
}

function UsersContent() {
  const { showToast } = useToast();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [filters, setFilters] = useState({
    username: '',
    email: '',
    permission: '' as string,
  });
  const [showCreate, setShowCreate] = useState(false);
  const pageSize = 10;

  const fetchData = useCallback(async (targetPage: number) => {
    setLoading(true);
    try {
      const res = await listUsers({
        skip: (targetPage - 1) * pageSize,
        limit: pageSize,
        username: filters.username || undefined,
        email: filters.email || undefined,
        permission: filters.permission ? Number(filters.permission) : undefined,
      });
      setUsers(res.items);
      setTotal(res.total);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载失败';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  }, [filters, showToast]);

  useEffect(() => {
    fetchData(page);
  }, [page, fetchData]);

  const handleSearch = () => {
    if (page === 1) {
      fetchData(1);
    } else {
      setPage(1);
    }
  };

  return (
    <div>
      {/* 标题区 — 在金色底上用深棕黑文字 */}
      <div className="mb-6">
        <h2
          className="text-xl sm:text-2xl font-black tracking-tight"
          style={{ fontFamily: 'var(--font-display)', color: '#1A1612', lineHeight: 1 }}
        >
          用户管理
        </h2>
        <p className="text-xs mt-1" style={{ color: 'rgba(26,22,18,0.5)', fontFamily: 'var(--font-body)' }}>
          用户管理
        </p>
        <div className="mt-3 h-px w-24" style={{ background: 'linear-gradient(90deg, #1A1612, transparent)', opacity: 0.3 }} />
      </div>

      {/* HUD 统计卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <HudCard label="用户总数" value={String(total)} delay={0} />
        <HudCard label="本页数量" value={String(users.length)} delay={0.05} />
        <HudCard label="本页管理员" value={String(users.filter((u) => u.permission >= 1).length)} delay={0.1} />
      </div>

      {/* 筛选 + 新建 */}
      <div
        className="flex flex-wrap gap-3 mb-5 p-3 items-center justify-between"
        style={{
          backgroundColor: 'rgba(26, 22, 18, 0.08)',
          border: '1px solid rgba(26, 22, 18, 0.12)',
        }}
      >
        <div className="flex flex-wrap gap-3 items-center">
          <FilterInput
            placeholder="用户名"
            value={filters.username}
            onChange={(v) => setFilters((f) => ({ ...f, username: v }))}
          />
          <FilterInput
            placeholder="邮箱"
            value={filters.email}
            onChange={(v) => setFilters((f) => ({ ...f, email: v }))}
          />
          <select
            value={filters.permission}
            onChange={(e) => setFilters((f) => ({ ...f, permission: e.target.value }))}
            className="px-2 py-1.5 text-xs outline-none"
            style={{
              color: '#1A1612',
              fontFamily: 'var(--font-body)',
              backgroundColor: 'rgba(255,255,255,0.4)',
              border: '1px solid rgba(26,22,18,0.2)',
            }}
            data-cursor-hover
          >
            <option value="">全部权限</option>
            <option value="0">普通用户</option>
            <option value="1">管理员</option>
            <option value="2">超级管理员</option>
          </select>
          <motion.button
            className="px-4 py-1.5 text-[10px] font-bold tracking-widest"
            style={{
              backgroundColor: '#1A1612',
              color: '#FFE52C',
              fontFamily: 'var(--font-display)',
              clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
            }}
            whileHover={{ scale: 1.05, backgroundColor: '#2A2118' }}
            whileTap={{ scale: 0.92 }}
            onClick={handleSearch}
            data-cursor-hover
          >
            搜索
          </motion.button>
        </div>
        <motion.button
          className="px-4 py-1.5 text-[10px] font-bold tracking-widest"
          style={{
            backgroundColor: 'transparent',
            color: '#1A1612',
            border: '1px solid rgba(26,22,18,0.4)',
            fontFamily: 'var(--font-display)',
            clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
          }}
          whileHover={{ scale: 1.05, backgroundColor: 'rgba(26,22,18,0.08)' }}
          whileTap={{ scale: 0.92 }}
          onClick={() => setShowCreate(true)}
          data-cursor-hover
        >
          新建用户
        </motion.button>
      </div>

      {/* 创建用户弹窗 */}
      <CreateUserDialog open={showCreate} onClose={() => setShowCreate(false)} onSuccess={() => { setShowCreate(false); fetchData(page); }} />

      {/* 用户卡片流 */}
      <div className="space-y-3">
        {loading && users.length === 0 ? (
          <div className="py-12 text-center text-xs" style={{ color: 'rgba(26,22,18,0.4)' }}>
            加载中...
          </div>
        ) : users.length === 0 ? (
          <div className="py-12 text-center text-xs" style={{ color: 'rgba(26,22,18,0.4)' }}>
            暂无数据
          </div>
        ) : (
          users.map((u, idx) => (
            <UserCard
              key={u.id}
              user={u}
              index={idx}
              onRefresh={() => fetchData(page)}
            />
          ))
        )}
      </div>

      {/* 分页 — 用深色卡片包裹以确保在金色底上的可读性 */}
      <div className="mt-5 flex justify-end">
        <div
          className="inline-flex items-center px-3 py-2"
          style={{
            backgroundColor: 'rgba(26, 22, 18, 0.9)',
            clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
          }}
        >
          <Pagination current={page} total={total} pageSize={pageSize} onChange={setPage} />
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   HUD 统计卡片（在金色底上 — 深棕黑底+暖金文字）
   ============================================================ */
function HudCard({ label, value, delay }: { label: string; value: string; delay: number }) {
  return (
    <motion.div
      className="relative p-3 sm:p-4 overflow-hidden"
      style={{
        backgroundColor: 'rgba(26, 22, 18, 0.9)',
        clipPath: 'polygon(10px 0%, 100% 0%, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0% 100%, 0% 10px)',
      }}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ scale: 1.03, boxShadow: '0 0 20px rgba(26,22,18,0.2)' }}
      data-cursor-hover
    >
      <div
        className="absolute top-0 right-0 w-3 h-3"
        style={{ backgroundColor: '#F5A623' }}
      />
      <div
        className="text-[9px] tracking-wider mb-1.5"
        style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}
      >
        {label}
      </div>
      <div
        className="text-xl sm:text-2xl font-black tracking-tight"
        style={{ color: '#F5A623', fontFamily: 'var(--font-display)', lineHeight: 1 }}
      >
        {value}
      </div>
    </motion.div>
  );
}

function FilterInput({ placeholder, value, onChange }: { placeholder: string; value: string; onChange: (v: string) => void }) {
  return (
    <input
      type="text"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => e.key === 'Enter' && (e.currentTarget as HTMLInputElement).blur()}
      className="px-2 py-1.5 text-xs outline-none w-28 sm:w-36"
      style={{
        color: '#1A1612',
        fontFamily: 'var(--font-body)',
        backgroundColor: 'rgba(255,255,255,0.4)',
        border: '1px solid rgba(26,22,18,0.2)',
      }}
      data-cursor-hover
    />
  );
}

/* ============================================================
   用户卡片 — 深棕黑底，左侧暖金竖条，hover跃起
   ============================================================ */
function UserCard({ user, index, onRefresh }: { user: UserResponse; index: number; onRefresh: () => void }) {
  const [showDetail, setShowDetail] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'soft' | 'hard' | null>(null);

  const permissionColor: Record<number, string> = {
    0: '#FFF8EE',
    1: '#7FE6EF',
    2: '#FFE52C',
  };

  return (
    <>
      <motion.div
        className="relative flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 px-4 py-3"
        style={{
          backgroundColor: 'rgba(26, 22, 18, 0.85)',
          clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
        }}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.04, duration: 0.35 }}
        whileHover={{ x: 6, backgroundColor: 'rgba(26, 22, 18, 0.98)' }}
        data-cursor-hover
      >
        {/* 左侧暖金竖条 */}
        <div
          className="absolute left-0 top-2 bottom-2 w-1"
          style={{ backgroundColor: '#F5A623', opacity: 0.8 }}
        />

        {/* ID */}
        <div className="sm:w-12 shrink-0">
          <span className="text-[10px] tabular-nums" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
            #{user.id}
          </span>
        </div>

        {/* 用户名 */}
        <div className="sm:w-32 shrink-0">
          <span className="text-sm font-medium" style={{ color: '#FFF8EE' }}>
            {user.username}
          </span>
        </div>

        {/* 邮箱 */}
        <div className="sm:w-40 shrink-0 flex-1 min-w-0">
          <span className="text-xs truncate block" style={{ color: 'rgba(255,248,238,0.6)' }}>
            {user.email}
          </span>
        </div>

        {/* 权限 */}
        <div className="sm:w-24 shrink-0">
          <span
            className="text-[10px] font-bold tracking-wider px-2 py-0.5"
            style={{
              color: permissionColor[user.permission] || '#FFF8EE',
              backgroundColor: permissionColor[user.permission] ? `${permissionColor[user.permission]}18` : 'transparent',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {getPermissionInfo(user.permission).label}
          </span>
        </div>

        {/* 状态 */}
        <div className="sm:w-16 shrink-0">
          <span
            className="text-[10px] font-bold tracking-wider"
            style={{
              color: user.is_deleted ? '#FF4D4D' : '#C4D70C',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {user.is_deleted ? '已注销' : '正常'}
          </span>
        </div>

        {/* 创建时间 */}
        <div className="sm:w-24 shrink-0 hidden lg:block">
          <span className="text-[10px]" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
            {formatDate(user.created_at)}
          </span>
        </div>

        {/* 操作 */}
        <div className="flex items-center gap-1.5 shrink-0 ml-auto">
          <ActionButton label="详情" bg="transparent" color="#7FE6EF" onClick={() => setShowDetail(true)} />
          <ActionButton label="编辑" bg="transparent" color="#F5A623" onClick={() => setShowEdit(true)} />
          {!user.is_deleted && (
            <ActionButton label="注销" bg="transparent" color="#FF4D4D" onClick={() => setConfirmAction('soft')} />
          )}
          <ActionButton label="删除" bg="transparent" color="#C22303" onClick={() => setConfirmAction('hard')} />
        </div>
      </motion.div>

      {/* 详情弹窗 */}
      <UserDetailDialog user={user} open={showDetail} onClose={() => setShowDetail(false)} />

      {/* 编辑弹窗 */}
      <UserEditDialog user={user} open={showEdit} onClose={() => setShowEdit(false)} onSuccess={onRefresh} />

      <ConfirmDialog
        open={confirmAction === 'soft'}
        title="注销用户"
        message={`确定要注销用户 "${user.username}" 吗？此操作可逆（逻辑删除）。`}
        onConfirm={async () => {
          try {
            await softDeleteUser(user.id);
            onRefresh();
          } catch {
            /* error handled by api client */
          } finally {
            setConfirmAction(null);
          }
        }}
        onCancel={() => setConfirmAction(null)}
      />
      <ConfirmDialog
        open={confirmAction === 'hard'}
        title="硬删除用户"
        message={`确定要彻底删除用户 "${user.username}" 吗？此操作不可恢复！`}
        danger
        confirmText="彻底删除"
        onConfirm={async () => {
          try {
            await hardDeleteUser(user.id);
            onRefresh();
          } catch {
            /* error handled by api client */
          } finally {
            setConfirmAction(null);
          }
        }}
        onCancel={() => setConfirmAction(null)}
      />
    </>
  );
}

function ActionButton({
  label,
  bg,
  color,
  onClick,
  disabled = false,
}: {
  label: string;
  bg: string;
  color: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      className="text-[9px] font-bold tracking-wider px-2 py-1 transition-opacity duration-150"
      style={{
        backgroundColor: bg,
        color,
        border: bg === 'transparent' ? `1px solid ${color}` : 'none',
        opacity: disabled ? 0.4 : 1,
        fontFamily: 'var(--font-mono)',
      }}
      onClick={onClick}
      disabled={disabled}
      data-cursor-hover={!disabled ? true : undefined}
    >
      {label}
    </button>
  );
}

/* ============================================================
   用户详情弹窗
   ============================================================ */
function UserDetailDialog({ user, open, onClose }: { user: UserResponse; open: boolean; onClose: () => void }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[9990] flex items-center justify-center px-4"
          style={{ backgroundColor: 'rgba(10, 8, 6, 0.85)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-lg relative overflow-hidden"
            style={{
              backgroundColor: 'rgba(26, 22, 18, 0.98)',
              border: '2px solid rgba(245, 166, 35, 0.3)',
              boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
              clipPath: 'polygon(16px 0%, 100% 0%, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0% 100%, 0% 16px)',
            }}
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 22, stiffness: 400 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 顶部彩条 */}
            <div className="absolute top-0 left-0 right-0 h-1" style={{ background: 'linear-gradient(90deg, #7FE6EF, #F5A623)' }} />

            <div className="p-6">
              {/* 标题 */}
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: '#7FE6EF' }}>
                  用户详情
                </h3>
                <button
                  className="text-xs font-bold tracking-wider px-3 py-1"
                  style={{ color: 'rgba(255,248,238,0.4)', border: '1px solid rgba(255,248,238,0.15)', fontFamily: 'var(--font-mono)' }}
                  onClick={onClose}
                  data-cursor-hover
                >
                  关闭
                </button>
              </div>

              {/* 内容 */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <DetailItem label="用户ID" value={String(user.id)} />
                <DetailItem label="用户名" value={user.username} />
                <DetailItem label="邮箱" value={user.email} />
                <DetailItem label="权限" value={getPermissionInfo(user.permission).label} />
                <DetailItem label="状态" value={user.is_deleted ? '已注销' : '正常'} />
                <DetailItem label="注册时间" value={formatDate(user.created_at)} />

                {/* 头像 */}
                <div className="sm:col-span-2">
                  <span className="text-[9px] tracking-widest block mb-2" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
                    头像
                  </span>
                  {user.avatar_url ? (
                    <img
                      src={user.avatar_url}
                      alt=""
                      className="w-16 h-16 object-cover"
                      style={{ border: '2px solid rgba(245,166,35,0.35)', clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)' }}
                    />
                  ) : (
                    <div
                      className="w-16 h-16 flex items-center justify-center text-xs font-bold"
                      style={{ color: 'rgba(255,248,238,0.25)', border: '2px solid rgba(245,166,35,0.15)', backgroundColor: 'rgba(255,255,255,0.03)' }}
                    >
                      无头像
                    </div>
                  )}
                </div>

                {/* 个人简介 */}
                <div className="sm:col-span-2">
                  <span className="text-[9px] tracking-widest block mb-1" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
                    个人简介
                  </span>
                  {user.personal_profile ? (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'rgba(255,248,238,0.8)' }}>
                      {user.personal_profile}
                    </p>
                  ) : (
                    <span className="text-xs" style={{ color: 'rgba(255,248,238,0.3)' }}>未填写</span>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ============================================================
   用户编辑弹窗
   ============================================================ */
function UserEditDialog({ user, open, onClose, onSuccess }: { user: UserResponse; open: boolean; onClose: () => void; onSuccess: () => void }) {
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [username, setUsername] = useState(user.username);
  const [email, setEmail] = useState(user.email);
  const [permission, setPermission] = useState(String(user.permission));
  const [personalProfile, setPersonalProfile] = useState(user.personal_profile ?? '');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(user.avatar_url);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setUsername(user.username);
      setEmail(user.email);
      setPermission(String(user.permission));
      setPersonalProfile(user.personal_profile ?? '');
      setAvatarFile(null);
      setAvatarPreview(user.avatar_url);
    }
  }, [open, user]);

  const handleFileChange = (file: File) => {
    if (file.size > 2 * 1024 * 1024) {
      showToast('头像文件不能超过 2MB', 'error');
      return;
    }
    setAvatarFile(file);
    const reader = new FileReader();
    reader.onloadend = () => setAvatarPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updateData: {
        username: string;
        email: string;
        permission: number;
        personal_profile?: string;
      } = {
        username,
        email,
        permission: Number(permission),
      };
      if (personalProfile.trim()) updateData.personal_profile = personalProfile.trim();
      await updateUser(user.id, updateData, avatarFile ?? undefined);
      showToast('用户信息已更新', 'success');
      onClose();
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '更新失败';
      showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[9990] flex items-center justify-center px-4"
          style={{ backgroundColor: 'rgba(10, 8, 6, 0.85)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-lg relative overflow-hidden"
            style={{
              backgroundColor: 'rgba(26, 22, 18, 0.98)',
              border: '2px solid rgba(245, 166, 35, 0.3)',
              boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
              clipPath: 'polygon(16px 0%, 100% 0%, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0% 100%, 0% 16px)',
            }}
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 22, stiffness: 400 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 顶部彩条 */}
            <div className="absolute top-0 left-0 right-0 h-1" style={{ background: 'linear-gradient(90deg, #F5A623, #FFE52C)' }} />

            <div className="p-6">
              {/* 标题 */}
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: '#F5A623' }}>
                  编辑用户
                </h3>
                <button
                  className="text-xs font-bold tracking-wider px-3 py-1"
                  style={{ color: 'rgba(255,248,238,0.4)', border: '1px solid rgba(255,248,238,0.15)', fontFamily: 'var(--font-mono)' }}
                  onClick={onClose}
                  data-cursor-hover
                >
                  取消
                </button>
              </div>

              {/* 表单 */}
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <EditField label="用户名" value={username} onChange={setUsername} />
                  <EditField label="邮箱" value={email} onChange={setEmail} />
                </div>

                <div>
                  <label className="block text-[9px] tracking-widest mb-1.5" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
                    权限
                  </label>
                  <select
                    value={permission}
                    onChange={(e) => setPermission(e.target.value)}
                    className="w-full px-3 py-2 text-xs outline-none"
                    style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.08)', border: '1px solid rgba(245,166,35,0.25)', fontFamily: 'var(--font-body)' }}
                  >
                    <option value="0" style={{ backgroundColor: '#1A1612' }}>普通用户</option>
                    <option value="1" style={{ backgroundColor: '#1A1612' }}>管理员</option>
                    <option value="2" style={{ backgroundColor: '#1A1612' }}>超级管理员</option>
                  </select>
                </div>

                {/* 头像上传 */}
                <div>
                  <label className="block text-[9px] tracking-widest mb-2" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
                    头像
                  </label>
                  <div className="flex items-center gap-3">
                    {avatarPreview ? (
                      <img
                        src={avatarPreview}
                        alt=""
                        className="w-12 h-12 object-cover"
                        style={{ border: '2px solid rgba(245,166,35,0.35)', clipPath: 'polygon(3px 0%, 100% 0%, 100% calc(100% - 3px), calc(100% - 3px) 100%, 0% 100%, 0% 3px)' }}
                      />
                    ) : (
                      <div
                        className="w-12 h-12 flex items-center justify-center text-[10px] font-bold"
                        style={{ color: 'rgba(255,248,238,0.2)', border: '2px solid rgba(245,166,35,0.15)', backgroundColor: 'rgba(255,255,255,0.03)' }}
                      >
                        无
                      </div>
                    )}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileChange(file);
                      }}
                    />
                    <motion.button
                      className="px-3 py-1.5 text-[10px] font-bold tracking-wider"
                      style={{
                        color: '#F5A623',
                        border: '1px solid rgba(245,166,35,0.3)',
                        fontFamily: 'var(--font-mono)',
                      }}
                      whileHover={{ backgroundColor: 'rgba(245,166,35,0.1)' }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => fileInputRef.current?.click()}
                      data-cursor-hover
                    >
                      {avatarFile ? '更换头像' : '上传头像'}
                    </motion.button>
                    {avatarFile && (
                      <span className="text-[9px]" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
                        {avatarFile.name}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-[9px] tracking-widest mb-1.5" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
                    个人简介
                  </label>
                  <textarea
                    value={personalProfile}
                    onChange={(e) => setPersonalProfile(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 text-xs outline-none resize-none"
                    style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.08)', border: '1px solid rgba(245,166,35,0.25)', fontFamily: 'var(--font-body)' }}
                    placeholder="个人简介..."
                  />
                </div>

                {/* 保存按钮 */}
                <motion.button
                  className="w-full py-2.5 text-sm font-bold tracking-widest"
                  style={{
                    backgroundColor: '#F5A623',
                    color: '#1A1612',
                    fontFamily: 'var(--font-display)',
                    clipPath: 'polygon(10px 0%, 100% 0%, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0% 100%, 0% 10px)',
                  }}
                  whileHover={{ scale: 1.02, backgroundColor: '#FFE52C' }}
                  whileTap={{ scale: 0.96 }}
                  onClick={handleSave}
                  disabled={saving}
                  data-cursor-hover
                >
                  {saving ? '保存中...' : '保存更改'}
                </motion.button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function EditField({ label, value, onChange, placeholder = '' }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <div>
      <label className="block text-[9px] tracking-widest mb-1.5" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
        {label}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 text-xs outline-none"
        style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.08)', border: '1px solid rgba(245,166,35,0.25)', fontFamily: 'var(--font-body)' }}
      />
    </div>
  );
}

/* ============================================================
   详情项组件
   ============================================================ */
function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[9px] tracking-widest mb-1" style={{ color: 'rgba(255,248,238,0.4)', fontFamily: 'var(--font-mono)' }}>
        {label}
      </span>
      <span className="text-sm font-semibold tracking-tight truncate" style={{ color: '#FFF8EE', fontFamily: 'var(--font-mono)' }}>
        {value}
      </span>
    </div>
  );
}

/* ============================================================
   创建用户弹窗
   ============================================================ */
function CreateUserDialog({ open, onClose, onSuccess }: { open: boolean; onClose: () => void; onSuccess: () => void }) {
  const { showToast } = useToast();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [permission, setPermission] = useState('0');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [personalProfile, setPersonalProfile] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) {
      setUsername('');
      setEmail('');
      setPassword('');
      setPermission('0');
      setAvatarUrl('');
      setPersonalProfile('');
      setErrors({});
      setSubmitting(false);
    }
  }, [open]);

  const validate = () => {
    const e: Record<string, string> = {};
    if (username.length < 3 || username.length > 64) e.username = '用户名 3~64 字符';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = '邮箱格式错误';
    if (password.length < 6 || password.length > 128) e.password = '密码 6~128 字符';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setSubmitting(true);
    try {
      const createData: {
        username: string;
        email: string;
        password: string;
        permission: number;
        avatar_url?: string;
        personal_profile?: string;
      } = {
        username,
        email,
        password,
        permission: Number(permission),
      };
      if (avatarUrl.trim()) createData.avatar_url = avatarUrl.trim();
      if (personalProfile.trim()) createData.personal_profile = personalProfile.trim();
      await createUser(createData);
      showToast('用户创建成功', 'success');
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '创建失败';
      showToast(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const fieldBase = 'w-full px-3 py-2 text-xs outline-none';
  const fieldStyle: React.CSSProperties = {
    color: '#FFF8EE',
    fontFamily: 'var(--font-body)',
    backgroundColor: 'rgba(255,255,255,0.08)',
    border: '1px solid rgba(245,166,35,0.25)',
  };

  const labelStyle: React.CSSProperties = {
    color: 'rgba(255,248,238,0.4)',
    fontFamily: 'var(--font-mono)',
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[9990] flex items-center justify-center px-4"
          style={{ backgroundColor: 'rgba(10, 8, 6, 0.85)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-lg relative overflow-hidden"
            style={{
              backgroundColor: 'rgba(26, 22, 18, 0.98)',
              border: '2px solid rgba(245, 166, 35, 0.3)',
              boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
              clipPath: 'polygon(16px 0%, 100% 0%, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0% 100%, 0% 16px)',
            }}
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 22, stiffness: 400 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 顶部彩条 */}
            <div className="absolute top-0 left-0 right-0 h-1" style={{ background: 'linear-gradient(90deg, #F5A623, #FFE52C)' }} />

            <div className="p-6">
              {/* 标题 */}
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-lg font-bold" style={{ fontFamily: 'var(--font-display)', color: '#F5A623' }}>
                  新建用户
                </h3>
                <button
                  className="text-xs font-bold tracking-wider px-3 py-1"
                  style={{ color: 'rgba(255,248,238,0.4)', border: '1px solid rgba(255,248,238,0.15)', fontFamily: 'var(--font-mono)' }}
                  onClick={onClose}
                  data-cursor-hover
                >
                  取消
                </button>
              </div>

              {/* 表单 */}
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[9px] tracking-widest mb-1.5" style={labelStyle}>用户名</label>
                    <input
                      className={fieldBase}
                      style={{ ...fieldStyle, borderColor: errors.username ? '#C22303' : 'rgba(245,166,35,0.25)' }}
                      value={username}
                      onChange={(e) => { setUsername(e.target.value); setErrors((p) => ({ ...p, username: '' })); }}
                      placeholder="3~64 字符"
                    />
                  </div>
                  <div>
                    <label className="block text-[9px] tracking-widest mb-1.5" style={labelStyle}>邮箱</label>
                    <input
                      className={fieldBase}
                      style={{ ...fieldStyle, borderColor: errors.email ? '#C22303' : 'rgba(245,166,35,0.25)' }}
                      value={email}
                      onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: '' })); }}
                      placeholder="有效邮箱"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[9px] tracking-widest mb-1.5" style={labelStyle}>密码</label>
                    <input
                      type="password"
                      className={fieldBase}
                      style={{ ...fieldStyle, borderColor: errors.password ? '#C22303' : 'rgba(245,166,35,0.25)' }}
                      value={password}
                      onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: '' })); }}
                      placeholder="6~128 字符"
                    />
                  </div>
                  <div>
                    <label className="block text-[9px] tracking-widest mb-1.5" style={labelStyle}>权限</label>
                    <select
                      className="w-full px-3 py-2 text-xs outline-none"
                      style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.08)', border: '1px solid rgba(245,166,35,0.25)', fontFamily: 'var(--font-body)' }}
                      value={permission}
                      onChange={(e) => setPermission(e.target.value)}
                    >
                      <option value="0" style={{ backgroundColor: '#1A1612' }}>普通用户</option>
                      <option value="1" style={{ backgroundColor: '#1A1612' }}>管理员</option>
                      <option value="2" style={{ backgroundColor: '#1A1612' }}>超级管理员</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-[9px] tracking-widest mb-1.5" style={labelStyle}>头像链接</label>
                  <input
                    className={fieldBase}
                    style={{ ...fieldStyle, borderColor: errors.avatar_url ? '#C22303' : 'rgba(245,166,35,0.25)' }}
                    value={avatarUrl}
                    onChange={(e) => { setAvatarUrl(e.target.value); setErrors((p) => ({ ...p, avatar_url: '' })); }}
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-[9px] tracking-widest mb-1.5" style={labelStyle}>个人简介</label>
                  <textarea
                    value={personalProfile}
                    onChange={(e) => { setPersonalProfile(e.target.value); setErrors((p) => ({ ...p, personal_profile: '' })); }}
                    rows={3}
                    className="w-full px-3 py-2 text-xs outline-none resize-none"
                    style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.08)', border: '1px solid rgba(245,166,35,0.25)', fontFamily: 'var(--font-body)' }}
                    placeholder="个人简介..."
                  />
                </div>

                {/* 按钮 */}
                <div className="flex gap-3 pt-2">
                  <motion.button
                    className="flex-1 py-2.5 text-sm font-bold tracking-widest"
                    style={{
                      backgroundColor: '#F5A623',
                      color: '#1A1612',
                      fontFamily: 'var(--font-display)',
                      clipPath: 'polygon(10px 0%, 100% 0%, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0% 100%, 0% 10px)',
                    }}
                    whileHover={{ scale: 1.02, backgroundColor: '#FFE52C' }}
                    whileTap={{ scale: 0.96 }}
                    onClick={handleSubmit}
                    disabled={submitting}
                    data-cursor-hover
                  >
                    {submitting ? '创建中...' : '创建'}
                  </motion.button>
                  <button
                    className="px-4 py-2.5 text-xs font-bold tracking-widest"
                    style={{
                      backgroundColor: 'transparent',
                      color: 'rgba(255,248,238,0.5)',
                      border: '1px solid rgba(255,248,238,0.15)',
                      fontFamily: 'var(--font-display)',
                    }}
                    onClick={onClose}
                    data-cursor-hover
                  >
                    取消
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
