import { useState, useEffect, useCallback } from 'react';
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
          USER MANAGEMENT
        </h2>
        <p className="text-xs mt-1" style={{ color: 'rgba(26,22,18,0.5)', fontFamily: 'var(--font-body)' }}>
          用户管理
        </p>
        <div className="mt-3 h-px w-24" style={{ background: 'linear-gradient(90deg, #1A1612, transparent)', opacity: 0.3 }} />
      </div>

      {/* HUD 统计卡片 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <HudCard label="TOTAL USERS" value={String(total)} delay={0} />
        <HudCard label="THIS PAGE" value={String(users.length)} delay={0.05} />
        <HudCard label="ADMINS" value={String(users.filter((u) => u.permission >= 1).length)} delay={0.1} />
        <HudCard label="STATUS" value="ONLINE" delay={0.15} />
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
            SEARCH
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
          onClick={() => setShowCreate((v) => !v)}
          data-cursor-hover
        >
          {showCreate ? 'CLOSE' : 'NEW USER'}
        </motion.button>
      </div>

      {/* 创建用户表单 */}
      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <CreateUserForm onSuccess={() => { setShowCreate(false); fetchData(page); }} onCancel={() => setShowCreate(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 用户卡片流 */}
      <div className="space-y-3">
        {loading && users.length === 0 ? (
          <div className="py-12 text-center text-xs" style={{ color: 'rgba(26,22,18,0.4)' }}>
            LOADING...
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
  const { showToast } = useToast();
  const [editing, setEditing] = useState(false);
  const [editUsername, setEditUsername] = useState(user.username);
  const [editEmail, setEditEmail] = useState(user.email);
  const [editPermission, setEditPermission] = useState(String(user.permission));
  const [confirmAction, setConfirmAction] = useState<'soft' | 'hard' | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateUser(user.id, {
        username: editUsername,
        email: editEmail,
        permission: Number(editPermission),
      });
      showToast('用户信息已更新', 'success');
      setEditing(false);
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '更新失败';
      showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (hard: boolean) => {
    try {
      if (hard) {
        await hardDeleteUser(user.id);
        showToast('用户已硬删除', 'success');
      } else {
        await softDeleteUser(user.id);
        showToast('用户已注销', 'success');
      }
      onRefresh();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    } finally {
      setConfirmAction(null);
    }
  };

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
          backgroundColor: editing ? 'rgba(26, 22, 18, 0.95)' : 'rgba(26, 22, 18, 0.85)',
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
          style={{ backgroundColor: editing ? '#FFE52C' : '#F5A623', opacity: 0.8 }}
        />

        {/* ID */}
        <div className="sm:w-12 shrink-0">
          <span className="text-[10px] tabular-nums" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
            #{user.id}
          </span>
        </div>

        {/* 用户名 */}
        <div className="sm:w-32 shrink-0">
          {editing ? (
            <input
              value={editUsername}
              onChange={(e) => setEditUsername(e.target.value)}
              className="w-full px-2 py-1 text-xs outline-none"
              style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.1)', border: '1px solid rgba(245,166,35,0.4)' }}
            />
          ) : (
            <span className="text-sm font-medium" style={{ color: '#FFF8EE' }}>
              {user.username}
            </span>
          )}
        </div>

        {/* 邮箱 */}
        <div className="sm:w-40 shrink-0 flex-1 min-w-0">
          {editing ? (
            <input
              value={editEmail}
              onChange={(e) => setEditEmail(e.target.value)}
              className="w-full px-2 py-1 text-xs outline-none"
              style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.1)', border: '1px solid rgba(245,166,35,0.4)' }}
            />
          ) : (
            <span className="text-xs truncate block" style={{ color: 'rgba(255,248,238,0.6)' }}>
              {user.email}
            </span>
          )}
        </div>

        {/* 权限 */}
        <div className="sm:w-24 shrink-0">
          {editing ? (
            <select
              value={editPermission}
              onChange={(e) => setEditPermission(e.target.value)}
              className="text-xs outline-none px-2 py-1 w-full"
              style={{ color: '#FFF8EE', backgroundColor: 'rgba(255,255,255,0.1)', border: '1px solid rgba(245,166,35,0.4)' }}
            >
              <option value="0">普通</option>
              <option value="1">管理员</option>
              <option value="2">超级管理员</option>
            </select>
          ) : (
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
          )}
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
          {editing ? (
            <>
              <ActionButton label="保存" bg="#C4D70C" color="#1A1612" onClick={handleSave} disabled={saving} />
              <ActionButton label="取消" bg="transparent" color="rgba(255,248,238,0.5)" onClick={() => setEditing(false)} />
            </>
          ) : (
            <>
              <ActionButton label="编辑" bg="transparent" color="#F5A623" onClick={() => setEditing(true)} />
              {!user.is_deleted && (
                <ActionButton label="注销" bg="transparent" color="#FF4D4D" onClick={() => setConfirmAction('soft')} />
              )}
              <ActionButton label="删除" bg="transparent" color="#C22303" onClick={() => setConfirmAction('hard')} />
            </>
          )}
        </div>
      </motion.div>

      <ConfirmDialog
        open={confirmAction === 'soft'}
        title="注销用户"
        message={`确定要注销用户 "${user.username}" 吗？此操作可逆（逻辑删除）。`}
        onConfirm={() => handleDelete(false)}
        onCancel={() => setConfirmAction(null)}
      />
      <ConfirmDialog
        open={confirmAction === 'hard'}
        title="硬删除用户"
        message={`确定要彻底删除用户 "${user.username}" 吗？此操作不可恢复！`}
        danger
        confirmText="彻底删除"
        onConfirm={() => handleDelete(true)}
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
   创建用户表单
   ============================================================ */
function CreateUserForm({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) {
  const { showToast } = useToast();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [permission, setPermission] = useState('0');
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

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
      await createUser({
        username,
        email,
        password,
        permission: Number(permission),
      });
      showToast('用户创建成功', 'success');
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '创建失败';
      showToast(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = 'w-full px-2 py-1.5 text-xs outline-none';
  const inputStyle: React.CSSProperties = {
    color: '#1A1612',
    fontFamily: 'var(--font-body)',
    backgroundColor: 'rgba(255,255,255,0.4)',
    border: '1px solid rgba(26,22,18,0.2)',
  };

  return (
    <div
      className="mb-5 p-4"
      style={{
        backgroundColor: 'rgba(26, 22, 18, 0.08)',
        border: '1px solid rgba(26,22,18,0.15)',
      }}
    >
      <div className="flex items-center gap-2 mb-3">
        <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#1A1612' }} />
        <span className="text-xs font-bold tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}>
          NEW USER
        </span>
      </div>
      <div className="flex flex-wrap gap-3 items-end">
        <div className="w-32">
          <label className="block text-[9px] tracking-widest mb-1 opacity-60" style={{ fontFamily: 'var(--font-mono)', color: '#1A1612' }}>
            USERNAME
          </label>
          <input
            className={inputClass}
            style={{ ...inputStyle, borderColor: errors.username ? '#C22303' : 'rgba(26,22,18,0.2)' }}
            value={username}
            onChange={(e) => { setUsername(e.target.value); setErrors((p) => ({ ...p, username: '' })); }}
            placeholder="3~64 字符"
          />
        </div>
        <div className="w-40">
          <label className="block text-[9px] tracking-widest mb-1 opacity-60" style={{ fontFamily: 'var(--font-mono)', color: '#1A1612' }}>
            EMAIL
          </label>
          <input
            className={inputClass}
            style={{ ...inputStyle, borderColor: errors.email ? '#C22303' : 'rgba(26,22,18,0.2)' }}
            value={email}
            onChange={(e) => { setEmail(e.target.value); setErrors((p) => ({ ...p, email: '' })); }}
            placeholder="有效邮箱"
          />
        </div>
        <div className="w-32">
          <label className="block text-[9px] tracking-widest mb-1 opacity-60" style={{ fontFamily: 'var(--font-mono)', color: '#1A1612' }}>
            PASSWORD
          </label>
          <input
            type="password"
            className={inputClass}
            style={{ ...inputStyle, borderColor: errors.password ? '#C22303' : 'rgba(26,22,18,0.2)' }}
            value={password}
            onChange={(e) => { setPassword(e.target.value); setErrors((p) => ({ ...p, password: '' })); }}
            placeholder="6~128 字符"
          />
        </div>
        <div className="w-24">
          <label className="block text-[9px] tracking-widest mb-1 opacity-60" style={{ fontFamily: 'var(--font-mono)', color: '#1A1612' }}>
            PERMISSION
          </label>
          <select
            className="px-2 py-1.5 text-xs outline-none w-full"
            style={{ color: '#1A1612', backgroundColor: 'rgba(255,255,255,0.4)', border: '1px solid rgba(26,22,18,0.2)' }}
            value={permission}
            onChange={(e) => setPermission(e.target.value)}
          >
            <option value="0">普通</option>
            <option value="1">管理员</option>
            <option value="2">超级管理员</option>
          </select>
        </div>
        <div className="flex gap-2">
          <motion.button
            className="px-4 py-1.5 text-[10px] font-bold tracking-widest"
            style={{
              backgroundColor: '#1A1612',
              color: '#FFE52C',
              fontFamily: 'var(--font-display)',
              clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.92 }}
            onClick={handleSubmit}
            disabled={submitting}
            data-cursor-hover
          >
            {submitting ? '...' : 'CREATE'}
          </motion.button>
          <button
            className="px-3 py-1.5 text-[10px] font-bold tracking-widest"
            style={{
              backgroundColor: 'transparent',
              color: 'rgba(26,22,18,0.5)',
              border: '1px solid rgba(26,22,18,0.2)',
              fontFamily: 'var(--font-display)',
            }}
            onClick={onCancel}
            data-cursor-hover
          >
            CANCEL
          </button>
        </div>
      </div>
    </div>
  );
}
