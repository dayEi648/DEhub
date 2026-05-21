import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Pencil, Trash2, Users, Eye } from 'lucide-react';
import { listForumZones, createForumZone, updateForumZone, deleteForumZone } from '../../api/forum';
import { useToast } from '../../components/ui/Toast';
import ConfirmDialog from '../../components/ui/ConfirmDialog';
import AdminShell from '../../components/layout/AdminShell';
import type { ForumZoneResponse } from '../../api/types';

export default function AdminForumZonesPage() {
  return (
    <AdminShell activePage="forum-zones">
      <ZonesContent />
    </AdminShell>
  );
}

function ZonesContent() {
  const { showToast } = useToast();
  const [zones, setZones] = useState<ForumZoneResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingZone, setEditingZone] = useState<ForumZoneResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ForumZoneResponse | null>(null);

  const fetchZones = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listForumZones();
      setZones(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载失败';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchZones();
  }, [fetchZones]);

  const handleCreate = () => {
    setEditingZone(null);
    setShowForm(true);
  };

  const handleEdit = (zone: ForumZoneResponse) => {
    setEditingZone(zone);
    setShowForm(true);
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteForumZone(deleteTarget.id);
      showToast('分区已删除', 'success');
      fetchZones();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '删除失败';
      showToast(msg, 'error');
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingZone(null);
    fetchZones();
  };

  return (
    <div>
      {/* 标题区 */}
      <div className="mb-6">
        <h2
          className="text-xl sm:text-2xl font-black tracking-tight"
          style={{ fontFamily: 'var(--font-display)', color: '#1A1612', lineHeight: 1 }}
        >
          论坛分区管理
        </h2>
        <p className="text-xs mt-1" style={{ color: 'rgba(26,22,18,0.5)', fontFamily: 'var(--font-body)' }}>
          管理所有论坛讨论分区
        </p>
        <div className="mt-3 h-px w-24" style={{ background: 'linear-gradient(90deg, #1A1612, transparent)', opacity: 0.3 }} />
      </div>

      {/* HUD 统计 */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <HudCard label="分区总数" value={String(zones.length)} delay={0} />
        <HudCard label="总浏览量" value={String(zones.reduce((s, z) => s + z.view_count, 0))} delay={0.05} />
      </div>

      {/* 新建按钮 */}
      <div className="flex justify-end mb-4">
        <motion.button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 text-[10px] font-bold tracking-wider chamfer-sm"
          style={{
            backgroundColor: '#1A1612',
            color: '#F5A623',
            fontFamily: 'var(--font-mono)',
          }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          data-cursor-hover
        >
          <Plus size={12} />
          新建分区
        </motion.button>
      </div>

      {/* 分区表格 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <motion.div
            className="w-8 h-8 border-2 border-[#1A1612] border-t-transparent"
            style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
        </div>
      ) : zones.length === 0 ? (
        <div className="text-center py-12">
          <p style={{ color: 'rgba(26,22,18,0.4)', fontFamily: 'var(--font-mono)' }}>
            暂无分区
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {zones.map((zone, index) => (
            <motion.div
              key={zone.id}
              className="flex items-start gap-3 sm:gap-4 p-3 sm:p-4"
              style={{
                backgroundColor: 'rgba(26, 22, 18, 0.06)',
                border: '1px solid rgba(26, 22, 18, 0.1)',
                clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
              }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.04 }}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-bold" style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}>
                    {zone.zone_name}
                  </span>
                  <span
                    className="text-[9px] tracking-wider px-1.5 py-0.5"
                    style={{
                      backgroundColor: 'rgba(26, 22, 18, 0.1)',
                      color: '#1A1612',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {zone.slug}
                  </span>
                </div>
                {zone.description && (
                  <p className="text-xs mb-1.5 line-clamp-1" style={{ color: 'rgba(26,22,18,0.6)', fontFamily: 'var(--font-body)' }}>
                    {zone.description}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-3">
                  <span className="flex items-center gap-1 text-[9px]" style={{ color: 'rgba(26,22,18,0.5)', fontFamily: 'var(--font-mono)' }}>
                    <Users size={10} />
                    {zone.manager.username}
                  </span>
                  <span className="flex items-center gap-1 text-[9px]" style={{ color: 'rgba(26,22,18,0.5)', fontFamily: 'var(--font-mono)' }}>
                    <Eye size={10} />
                    {zone.view_count}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <motion.button
                  onClick={() => handleEdit(zone)}
                  className="p-1.5"
                  style={{ color: '#1A1612' }}
                  whileHover={{ scale: 1.15 }}
                  whileTap={{ scale: 0.9 }}
                  data-cursor-hover
                >
                  <Pencil size={14} />
                </motion.button>
                <motion.button
                  onClick={() => setDeleteTarget(zone)}
                  className="p-1.5"
                  style={{ color: '#C22303' }}
                  whileHover={{ scale: 1.15 }}
                  whileTap={{ scale: 0.9 }}
                  data-cursor-hover
                >
                  <Trash2 size={14} />
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* 表单弹窗 */}
      <AnimatePresence>
        {showForm && (
          <ZoneFormDialog
            zone={editingZone}
            onSuccess={handleFormSuccess}
            onCancel={() => {
              setShowForm(false);
              setEditingZone(null);
            }}
          />
        )}
      </AnimatePresence>

      <ConfirmDialog
        open={!!deleteTarget}
        title="确认删除分区"
        message={
          <>
            确定删除分区 <strong>{deleteTarget?.zone_name}</strong> 吗？
            <br />
            如果该分区下还有帖子，将无法删除。
          </>
        }
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}

function HudCard({ label, value, delay }: { label: string; value: string; delay: number }) {
  return (
    <motion.div
      className="p-3"
      style={{
        backgroundColor: 'rgba(26, 22, 18, 0.06)',
        border: '1px solid rgba(26, 22, 18, 0.1)',
        clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
      }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
    >
      <p className="text-[9px] tracking-wider mb-1" style={{ color: 'rgba(26,22,18,0.45)', fontFamily: 'var(--font-mono)' }}>
        {label}
      </p>
      <p className="text-lg font-black" style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}>
        {value}
      </p>
    </motion.div>
  );
}

function ZoneFormDialog({
  zone,
  onSuccess,
  onCancel,
}: {
  zone: ForumZoneResponse | null;
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const { showToast } = useToast();
  const isEdit = !!zone;
  const [zoneName, setZoneName] = useState(zone?.zone_name || '');
  const [slug, setSlug] = useState(zone?.slug || '');
  const [description, setDescription] = useState(zone?.description || '');
  const [managerId, setManagerId] = useState(zone ? String(zone.manager_id) : '');
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ zoneName?: string; slug?: string }>({});

  const validate = () => {
    const newErrors: { zoneName?: string; slug?: string } = {};
    if (!zoneName.trim()) newErrors.zoneName = '请输入分区名称';
    if (slug.trim() && !/^[a-z0-9_-]+$/i.test(slug.trim())) {
      newErrors.slug = 'slug 只能包含字母、数字、下划线和连字符';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      const data = {
        zone_name: zoneName.trim(),
        slug: slug.trim() || undefined,
        description: description.trim() || undefined,
        manager_id: managerId ? Number(managerId) : undefined,
      };

      if (isEdit && zone) {
        await updateForumZone(zone.id, data);
        showToast('分区已更新', 'success');
      } else {
        await createForumZone(data);
        showToast('分区已创建', 'success');
      }
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <motion.div
      className="fixed inset-0 z-[9990] flex items-center justify-center px-4"
      style={{ backgroundColor: 'rgba(10, 8, 6, 0.85)' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onCancel}
    >
      <motion.div
        className="chamfer w-full max-w-md p-6 relative"
        style={{
          backgroundColor: 'rgba(26, 22, 18, 0.98)',
          border: '1px solid rgba(245, 166, 35, 0.25)',
          boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
        }}
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        transition={{ type: 'spring', damping: 22, stiffness: 400 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="absolute top-0 left-0 right-0 h-1"
          style={{ background: 'linear-gradient(90deg, #F5A623, #FFE52C)' }}
        />

        <h3
          className="text-lg font-bold mb-4 mt-2"
          style={{ fontFamily: 'var(--font-display)', color: '#F5A623' }}
        >
          {isEdit ? '编辑分区' : '新建分区'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[9px] font-bold tracking-wider mb-1" style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}>
              分区名称 *
            </label>
            <input
              type="text"
              value={zoneName}
              onChange={(e) => setZoneName(e.target.value)}
              placeholder="输入分区名称"
              className="w-full px-3 py-2 text-sm outline-none"
              style={{
                backgroundColor: 'rgba(42, 33, 24, 0.8)',
                color: '#FFF8EE',
                fontFamily: 'var(--font-body)',
                border: `1px solid ${errors.zoneName ? 'rgba(255, 77, 77, 0.5)' : 'rgba(245, 166, 35, 0.2)'}`,
                clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
              }}
            />
            {errors.zoneName && (
              <p className="text-[9px] mt-1" style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}>
                {errors.zoneName}
              </p>
            )}
          </div>

          <div>
            <label className="block text-[9px] font-bold tracking-wider mb-1" style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}>
              URL 标识 (slug)
            </label>
            <input
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              placeholder="留空则自动生成"
              className="w-full px-3 py-2 text-sm outline-none"
              style={{
                backgroundColor: 'rgba(42, 33, 24, 0.8)',
                color: '#FFF8EE',
                fontFamily: 'var(--font-body)',
                border: `1px solid ${errors.slug ? 'rgba(255, 77, 77, 0.5)' : 'rgba(245, 166, 35, 0.2)'}`,
                clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
              }}
            />
            {errors.slug && (
              <p className="text-[9px] mt-1" style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}>
                {errors.slug}
              </p>
            )}
          </div>

          <div>
            <label className="block text-[9px] font-bold tracking-wider mb-1" style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}>
              描述
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="输入分区描述"
              rows={3}
              className="w-full px-3 py-2 text-sm resize-none outline-none"
              style={{
                backgroundColor: 'rgba(42, 33, 24, 0.8)',
                color: '#FFF8EE',
                fontFamily: 'var(--font-body)',
                border: '1px solid rgba(245, 166, 35, 0.2)',
                clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
              }}
            />
          </div>

          <div>
            <label className="block text-[9px] font-bold tracking-wider mb-1" style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}>
              区主 ID
            </label>
            <input
              type="number"
              value={managerId}
              onChange={(e) => setManagerId(e.target.value)}
              placeholder="留空则默认为当前用户"
              min={1}
              className="w-full px-3 py-2 text-sm outline-none"
              style={{
                backgroundColor: 'rgba(42, 33, 24, 0.8)',
                color: '#FFF8EE',
                fontFamily: 'var(--font-body)',
                border: '1px solid rgba(245, 166, 35, 0.2)',
                clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
              }}
            />
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="chamfer-sm px-4 py-2 text-xs font-bold tracking-wider"
              style={{
                backgroundColor: 'transparent',
                color: '#FFF8EE',
                border: '1px solid rgba(247, 243, 232, 0.2)',
                fontFamily: 'var(--font-display)',
              }}
              data-cursor-hover
            >
              取消
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="chamfer-sm px-4 py-2 text-xs font-bold tracking-wider"
              style={{
                backgroundColor: '#F5A623',
                color: '#1A1612',
                fontFamily: 'var(--font-display)',
                opacity: submitting ? 0.6 : 1,
              }}
              data-cursor-hover
            >
              {submitting ? '保存中...' : isEdit ? '保存' : '创建'}
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}
