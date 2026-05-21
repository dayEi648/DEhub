import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { ArrowLeft, Send, Loader2 } from 'lucide-react';
import { createForumPost, updateForumPost, getForumPostById, listForumZones } from '../api/forum';
import { useToast } from '../components/ui/Toast';
import type { ForumZoneResponse } from '../api/types';

export default function ForumPostEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const isEdit = !!id;

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [zoneId, setZoneId] = useState('');
  const [zones, setZones] = useState<ForumZoneResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [errors, setErrors] = useState<{ title?: string; content?: string; zoneId?: string }>({});

  const stateZoneId = (location.state as { zoneId?: number } | null)?.zoneId;

  const fetchZones = useCallback(async () => {
    try {
      const res = await listForumZones();
      setZones(res);
      if (stateZoneId) {
        setZoneId(String(stateZoneId));
      } else if (res.length > 0 && !isEdit) {
        setZoneId(String(res[0].id));
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载分区失败';
      showToast(msg, 'error');
    }
  }, [stateZoneId, isEdit, showToast]);

  const fetchPost = useCallback(async () => {
    if (!id) return;
    setFetching(true);
    try {
      const data = await getForumPostById(Number(id));
      setTitle(data.title);
      setContent(data.content);
      setZoneId(String(data.zone_id));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '加载帖子失败';
      showToast(msg, 'error');
      navigate('/forum');
    } finally {
      setFetching(false);
    }
  }, [id, navigate, showToast]);

  useEffect(() => {
    fetchZones();
  }, [fetchZones]);

  useEffect(() => {
    if (isEdit) {
      fetchPost();
    }
  }, [isEdit, fetchPost]);

  const validate = () => {
    const newErrors: { title?: string; content?: string; zoneId?: string } = {};
    if (!title.trim()) newErrors.title = '请输入标题';
    else if (title.trim().length > 128) newErrors.title = '标题不能超过128字符';
    if (!content.trim()) newErrors.content = '请输入内容';
    if (!zoneId) newErrors.zoneId = '请选择分区';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      if (isEdit) {
        await updateForumPost(Number(id), {
          title: title.trim(),
          content: content.trim(),
          zone_id: Number(zoneId),
        });
        showToast('帖子已更新', 'success');
        navigate(`/forum/posts/${id}`);
      } else {
        const res = await createForumPost({
          title: title.trim(),
          content: content.trim(),
          zone_id: Number(zoneId),
        });
        showToast('帖子已发布', 'success');
        navigate(`/forum/posts/${res.id}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#0D0A07' }}>
        <div className="flex flex-col items-center gap-4">
          <motion.div
            className="w-10 h-10 border-2 border-[#7FE6EF] border-t-transparent"
            style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          <span className="text-[10px] tracking-wider animate-pulse" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
            加载中...
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0D0A07' }}>
      {/* 顶部框架 */}
      <header
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8"
        style={{
          height: 80,
          background: 'linear-gradient(180deg, #7FE6EF 0%, #5BC4CE 50%, #7FE6EF 100%)',
          borderBottom: '2px solid #1A1612',
        }}
      >
        <div className="absolute top-2 left-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="absolute top-2 right-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="text-[10px] font-bold tracking-widest flex items-center gap-1"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
            data-cursor-hover
          >
            <ArrowLeft size={12} />
            返回
          </button>
          <div className="h-4 w-px" style={{ backgroundColor: 'rgba(26,22,18,0.3)' }} />
          <span className="text-xs font-bold tracking-wider hidden sm:inline" style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}>
            {isEdit ? '编辑话题' : '发布话题'}
          </span>
        </div>
        <span className="text-[9px] tracking-wider font-bold" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          EDITOR
        </span>
      </header>

      {/* 主内容区域 */}
      <main className="flex-1 px-4 sm:px-6 lg:px-8 pb-8" style={{ marginTop: 80, marginBottom: 40 }}>
        <div className="max-w-3xl mx-auto pt-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#7FE6EF' }} />
              <span className="text-[10px] tracking-[0.3em] font-bold" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
                {isEdit ? 'EDIT TOPIC' : 'NEW TOPIC'}
              </span>
              <div className="h-px flex-1 bg-[#7FE6EF]/15" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* 标题 */}
              <div>
                <label className="block text-[10px] font-bold tracking-wider mb-1.5" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
                  标题
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="输入话题标题..."
                  maxLength={128}
                  className="w-full px-3 py-2.5 text-sm outline-none transition-colors"
                  style={{
                    backgroundColor: 'rgba(42, 33, 24, 0.8)',
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                    border: `1px solid ${errors.title ? 'rgba(255, 77, 77, 0.5)' : 'rgba(127, 230, 239, 0.2)'}`,
                    clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
                  }}
                />
                {errors.title && (
                  <p className="text-[10px] mt-1" style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}>
                    {errors.title}
                  </p>
                )}
              </div>

              {/* 分区选择 */}
              <div>
                <label className="block text-[10px] font-bold tracking-wider mb-1.5" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
                  分区
                </label>
                <select
                  value={zoneId}
                  onChange={(e) => setZoneId(e.target.value)}
                  className="w-full px-3 py-2.5 text-sm outline-none appearance-none cursor-pointer"
                  style={{
                    backgroundColor: 'rgba(42, 33, 24, 0.8)',
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                    border: `1px solid ${errors.zoneId ? 'rgba(255, 77, 77, 0.5)' : 'rgba(127, 230, 239, 0.2)'}`,
                    clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
                  }}
                >
                  <option value="" style={{ backgroundColor: '#1A1612' }}>请选择分区</option>
                  {zones.map((z) => (
                    <option key={z.id} value={z.id} style={{ backgroundColor: '#1A1612' }}>
                      {z.zone_name}
                    </option>
                  ))}
                </select>
                {errors.zoneId && (
                  <p className="text-[10px] mt-1" style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}>
                    {errors.zoneId}
                  </p>
                )}
              </div>

              {/* 内容 */}
              <div>
                <label className="block text-[10px] font-bold tracking-wider mb-1.5" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
                  内容
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="写下话题内容..."
                  rows={12}
                  className="w-full px-3 py-2.5 text-sm resize-none outline-none"
                  style={{
                    backgroundColor: 'rgba(42, 33, 24, 0.8)',
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                    border: `1px solid ${errors.content ? 'rgba(255, 77, 77, 0.5)' : 'rgba(127, 230, 239, 0.2)'}`,
                    clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
                  }}
                />
                {errors.content && (
                  <p className="text-[10px] mt-1" style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}>
                    {errors.content}
                  </p>
                )}
              </div>

              {/* 操作按钮 */}
              <div className="flex items-center gap-3 pt-2">
                <motion.button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 px-6 py-2.5 text-xs font-bold tracking-wider chamfer-sm"
                  style={{
                    backgroundColor: '#7FE6EF',
                    color: '#1A1612',
                    fontFamily: 'var(--font-mono)',
                    opacity: loading ? 0.6 : 1,
                  }}
                  whileHover={{ scale: loading ? 1 : 1.05 }}
                  whileTap={{ scale: loading ? 1 : 0.95 }}
                  data-cursor-hover
                >
                  {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                  {isEdit ? '保存修改' : '发布话题'}
                </motion.button>
                <button
                  type="button"
                  onClick={() => navigate(-1)}
                  className="px-4 py-2.5 text-xs font-bold tracking-wider chamfer-sm"
                  style={{
                    backgroundColor: 'transparent',
                    color: '#FFF8EE',
                    border: '1px solid rgba(247, 243, 232, 0.2)',
                    fontFamily: 'var(--font-mono)',
                  }}
                  data-cursor-hover
                >
                  取消
                </button>
              </div>
            </form>
          </motion.div>

          {/* 底部装饰 */}
          <div className="py-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[#7FE6EF]/10" />
              <span className="text-[9px] tracking-[0.3em] opacity-25" style={{ fontFamily: 'var(--font-mono)', color: '#7FE6EF' }}>
                编辑器
              </span>
              <div className="h-px flex-1 bg-[#7FE6EF]/10" />
            </div>
          </div>
        </div>
      </main>

      {/* 底部框架 */}
      <footer
        className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8"
        style={{
          height: 40,
          background: 'linear-gradient(180deg, #7FE6EF 0%, #5BC4CE 50%, #7FE6EF 100%)',
          borderTop: '2px solid #1A1612',
        }}
      >
        <div className="absolute top-2 left-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="absolute top-2 right-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <span className="text-[9px] tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          {isEdit ? '编辑模式' : '新建模式'}
        </span>
        <span className="text-[9px] tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          EDITOR
        </span>
        <span className="text-[9px] tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          CH.02
        </span>
      </footer>
    </div>
  );
}
