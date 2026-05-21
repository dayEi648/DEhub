import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { createBlogPost, updateBlogPost, getBlogPostById, generateSummary, listBlogCategories } from '../api/blog';
import { useToast } from '../components/ui/Toast';
import { useAuth } from '../contexts/AuthContext';
import type { BlogPostDetailResponse, BlogCategoryWithPostCount } from '../api/types';

interface BlogFormData {
  title: string;
  slug: string;
  summary: string;
  content_md: string;
  cover_image_url: string;
  category_id: number;
  tags: string;
  status: 'draft' | 'published';
}

const initialFormData: BlogFormData = {
  title: '',
  slug: '',
  summary: '',
  content_md: '',
  cover_image_url: '',
  category_id: 0,
  tags: '',
  status: 'draft',
};

export default function BlogEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const { isAdmin } = useAuth();
  const isEditMode = Boolean(id);
  const postId = id ? Number(id) : 0;

  const [formData, setFormData] = useState<BlogFormData>(initialFormData);
  const [categories, setCategories] = useState<BlogCategoryWithPostCount[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [fetchingSummary, setFetchingSummary] = useState(false);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverPreview, setCoverPreview] = useState('');

  // 权限检查
  useEffect(() => {
    if (!isAdmin) {
      showToast('权限不足', 'error');
      navigate('/blog');
    }
  }, [isAdmin, navigate, showToast]);

  // 加载分类列表
  const fetchCategories = useCallback(async () => {
    try {
      const res = await listBlogCategories();
      setCategories(res);
      // 如果有分类且是创建模式，默认选中第一个
      if (res.length > 0 && !isEditMode) {
        setFormData((prev) => ({ ...prev, category_id: res[0].id }));
      }
    } catch {
      showToast('分类加载失败', 'error');
    }
  }, [isEditMode, showToast]);

  // 加载文章详情（编辑模式）
  const fetchPost = useCallback(async () => {
    if (!isEditMode) return;
    setLoading(true);
    try {
      const data: BlogPostDetailResponse = await getBlogPostById(postId);
      setFormData({
        title: data.title,
        slug: data.slug,
        summary: data.summary || '',
        content_md: data.content_md,
        cover_image_url: data.cover_image_url || '',
        category_id: data.category_id,
        tags: data.tags.join(', '),
        status: data.status,
      });
      if (data.cover_image_url) {
        setCoverPreview(data.cover_image_url);
      }
    } catch {
      showToast('文章加载失败', 'error');
      navigate('/blog');
    } finally {
      setLoading(false);
    }
  }, [isEditMode, postId, navigate, showToast]);

  useEffect(() => {
    fetchCategories();
    fetchPost();
  }, [fetchCategories, fetchPost]);

  const handleChange = (field: keyof BlogFormData, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setCoverFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setCoverPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleGenerateSummary = async () => {
    if (!formData.content_md || formData.content_md.length < 100) {
      showToast('正文至少需要 100 字符才能生成摘要', 'error');
      return;
    }
    setFetchingSummary(true);
    try {
      const res = await generateSummary({ content_md: formData.content_md });
      setFormData((prev) => ({ ...prev, summary: res.summary }));
      showToast('摘要生成成功', 'success');
    } catch {
      showToast('摘要生成失败', 'error');
    } finally {
      setFetchingSummary(false);
    }
  };

  const validateForm = (): boolean => {
    if (!formData.title.trim()) {
      showToast('标题不能为空', 'error');
      return false;
    }
    if (formData.title.trim().length > 64) {
      showToast('标题不能超过 64 字符', 'error');
      return false;
    }
    if (!formData.content_md.trim()) {
      showToast('正文不能为空', 'error');
      return false;
    }
    if (formData.category_id <= 0) {
      showToast('请选择分类', 'error');
      return false;
    }
    if (formData.slug && formData.slug.length > 255) {
      showToast('slug 不能超过 255 字符', 'error');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSaving(true);
    try {
      const basePostIn = {
        title: formData.title.trim(),
        summary: formData.summary.trim() || undefined,
        content_md: formData.content_md,
        category_id: formData.category_id,
        tags: formData.tags
          .split(/[,，]/)
          .map((t) => t.trim())
          .filter(Boolean),
        status: formData.status,
      };

      if (isEditMode) {
        await updateBlogPost(postId, basePostIn, coverFile || undefined);
        showToast('文章更新成功', 'success');
      } else {
        const postIn = {
          ...basePostIn,
          slug: formData.slug.trim() || undefined,
        };
        await createBlogPost(postIn, coverFile || undefined);
        showToast('文章创建成功', 'success');
      }
      navigate('/blog');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '操作失败';
      showToast(message, 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#0D0A07' }}>
        <div className="flex flex-col items-center gap-4">
          <motion.div
            className="w-10 h-10 border-2 border-[#F5A623] border-t-transparent"
            style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          <span
            className="text-[10px] tracking-wider animate-pulse"
            style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
          >
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
          background: 'linear-gradient(180deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderBottom: '2px solid #1A1612',
        }}
      >
        <div className="absolute top-2 left-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="absolute top-2 right-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/blog')}
            className="text-xs font-bold tracking-wider"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
            data-cursor-hover
          >
            ← 返回
          </button>
          <span
            className="text-sm font-bold tracking-wider"
            style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
          >
            {isEditMode ? '编辑文章' : '新建文章'}
          </span>
        </div>
        <span
          className="text-[9px] tracking-wider font-bold"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          管理员
        </span>
      </header>

      {/* 主内容 */}
      <main
        className="flex-1 px-4 sm:px-6 lg:px-8 pb-8"
        style={{ marginTop: 80, marginBottom: 40 }}
      >
        <div className="max-w-4xl mx-auto pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 标题 */}
            <div>
              <label
                className="block text-[10px] tracking-wider font-bold mb-2"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                标题 *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => handleChange('title', e.target.value)}
                placeholder="输入文章标题"
                maxLength={64}
                className="w-full px-4 py-3 text-sm outline-none"
                style={{
                  backgroundColor: 'rgba(26, 22, 18, 0.8)',
                  border: '1px solid rgba(245, 166, 35, 0.2)',
                  color: '#FFF8EE',
                  fontFamily: 'var(--font-body)',
                }}
                required
              />
            </div>

            {/* slug — 仅创建模式可编辑 */}
            {isEditMode ? (
              <div>
                <label
                  className="block text-[10px] tracking-wider font-bold mb-2"
                  style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
                >
                  URL 标识 (slug)
                </label>
                <div
                  className="w-full px-4 py-3 text-sm"
                  style={{
                    backgroundColor: 'rgba(26, 22, 18, 0.5)',
                    border: '1px solid rgba(245, 166, 35, 0.1)',
                    color: 'rgba(255, 248, 238, 0.4)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {formData.slug}
                </div>
              </div>
            ) : (
              <div>
                <label
                  className="block text-[10px] tracking-wider font-bold mb-2"
                  style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
                >
                  URL 标识 (slug)
                </label>
                <input
                  type="text"
                  value={formData.slug}
                  onChange={(e) => handleChange('slug', e.target.value)}
                  placeholder="留空将自动生成"
                  maxLength={255}
                  className="w-full px-4 py-3 text-sm outline-none"
                  style={{
                    backgroundColor: 'rgba(26, 22, 18, 0.8)',
                    border: '1px solid rgba(245, 166, 35, 0.2)',
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                  }}
                />
              </div>
            )}

            {/* 分类 */}
            <div>
              <label
                className="block text-[10px] tracking-wider font-bold mb-2"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                分类 *
              </label>
              {categories.length === 0 ? (
                <div
                  className="w-full px-4 py-3 text-sm"
                  style={{
                    backgroundColor: 'rgba(26, 22, 18, 0.5)',
                    border: '1px solid rgba(245, 166, 35, 0.1)',
                    color: 'rgba(255, 248, 238, 0.3)',
                    fontFamily: 'var(--font-body)',
                  }}
                >
                  暂无可用分类
                </div>
              ) : (
                <select
                  value={formData.category_id}
                  onChange={(e) => handleChange('category_id', Number(e.target.value))}
                  className="w-full px-4 py-3 text-sm outline-none"
                  style={{
                    backgroundColor: 'rgba(26, 22, 18, 0.8)',
                    border: '1px solid rgba(245, 166, 35, 0.2)',
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                  }}
                  required
                >
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* 标签 */}
            <div>
              <label
                className="block text-[10px] tracking-wider font-bold mb-2"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                标签
              </label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => handleChange('tags', e.target.value)}
                placeholder="用逗号分隔，如：Python, FastAPI, 教程"
                className="w-full px-4 py-3 text-sm outline-none"
                style={{
                  backgroundColor: 'rgba(26, 22, 18, 0.8)',
                  border: '1px solid rgba(245, 166, 35, 0.2)',
                  color: '#FFF8EE',
                  fontFamily: 'var(--font-body)',
                }}
              />
            </div>

            {/* 封面图 — 仅允许上传 */}
            <div>
              <label
                className="block text-[10px] tracking-wider font-bold mb-3"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                封面图
              </label>
              <div className="flex gap-4 items-center">
                {/* 上传按钮区 */}
                <label
                  className="relative flex items-center justify-center gap-2 px-6 py-4 text-xs font-bold tracking-wider cursor-pointer chamfer-sm min-w-[160px]"
                  style={{
                    backgroundColor: 'rgba(26, 22, 18, 0.8)',
                    border: '1px solid rgba(245, 166, 35, 0.35)',
                    color: '#F5A623',
                    fontFamily: 'var(--font-mono)',
                  }}
                  data-cursor-hover
                >
                  <span style={{ fontSize: 14 }}>📎</span>
                  <span>{coverFile ? '已选择' : (isEditMode && coverPreview ? '更换封面' : '选择图片')}</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>

                {/* 文件名 / 操作 */}
                <div className="flex-1 min-w-0">
                  {coverFile ? (
                    <div className="flex items-center gap-3">
                      <span
                        className="text-xs truncate"
                        style={{ color: '#FFF8EE', fontFamily: 'var(--font-body)', opacity: 0.8 }}
                      >
                        {coverFile.name}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setCoverFile(null);
                          setCoverPreview('');
                        }}
                        className="text-[9px] tracking-wider hover:text-[#FF4D4D] transition-colors shrink-0"
                        style={{ color: 'rgba(247, 243, 232, 0.4)', fontFamily: 'var(--font-mono)' }}
                        data-cursor-hover
                      >
                        清除
                      </button>
                    </div>
                  ) : isEditMode && coverPreview ? (
                    <span
                      className="text-[9px] tracking-wider"
                      style={{ color: 'rgba(247, 243, 232, 0.35)', fontFamily: 'var(--font-mono)' }}
                    >
                      已设置封面，点击左侧更换
                    </span>
                  ) : (
                    <span
                      className="text-[9px] tracking-wider"
                      style={{ color: 'rgba(247, 243, 232, 0.25)', fontFamily: 'var(--font-mono)' }}
                    >
                      支持 JPG / PNG / WebP，建议 1200×600
                    </span>
                  )}
                </div>

                {/* 预览图 */}
                {coverPreview && (
                  <div
                    className="w-36 h-24 flex-shrink-0 overflow-hidden"
                    style={{ border: '2px solid rgba(245, 166, 35, 0.4)' }}
                  >
                    <img src={coverPreview} alt="封面预览" className="w-full h-full object-cover" />
                  </div>
                )}
              </div>
            </div>

            {/* 摘要 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label
                  className="block text-[10px] tracking-wider font-bold"
                  style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
                >
                  摘要
                </label>
                <button
                  type="button"
                  onClick={handleGenerateSummary}
                  disabled={fetchingSummary}
                  className="text-[10px] font-bold tracking-wider px-3 py-1"
                  style={{
                    backgroundColor: fetchingSummary ? 'rgba(127, 230, 239, 0.2)' : '#7FE6EF',
                    color: '#1A1612',
                    fontFamily: 'var(--font-mono)',
                    opacity: fetchingSummary ? 0.5 : 1,
                  }}
                  data-cursor-hover
                >
                  {fetchingSummary ? '生成中...' : 'AI 生成摘要'}
                </button>
              </div>
              <textarea
                value={formData.summary}
                onChange={(e) => handleChange('summary', e.target.value)}
                placeholder="文章摘要，留空可点击 AI 生成"
                rows={3}
                className="w-full px-4 py-3 text-sm resize-none outline-none"
                style={{
                  backgroundColor: 'rgba(26, 22, 18, 0.8)',
                  border: '1px solid rgba(245, 166, 35, 0.2)',
                  color: '#FFF8EE',
                  fontFamily: 'var(--font-body)',
                }}
              />
            </div>

            {/* 正文 */}
            <div>
              <label
                className="block text-[10px] tracking-wider font-bold mb-2"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                正文 (Markdown) *
              </label>
              <textarea
                value={formData.content_md}
                onChange={(e) => handleChange('content_md', e.target.value)}
                placeholder="使用 Markdown 格式编写文章正文..."
                rows={20}
                className="w-full px-4 py-3 text-sm resize-none outline-none font-mono"
                style={{
                  backgroundColor: 'rgba(26, 22, 18, 0.8)',
                  border: '1px solid rgba(245, 166, 35, 0.2)',
                  color: '#FFF8EE',
                  fontFamily: 'var(--font-mono)',
                  lineHeight: 1.6,
                }}
                required
              />
            </div>

            {/* 状态 */}
            <div>
              <label
                className="block text-[10px] tracking-wider font-bold mb-2"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                状态
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
                    value="draft"
                    checked={formData.status === 'draft'}
                    onChange={(e) => handleChange('status', e.target.value)}
                    className="accent-[#F5A623]"
                  />
                  <span className="text-sm" style={{ color: '#FFF8EE' }}>
                    草稿
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="status"
                    value="published"
                    checked={formData.status === 'published'}
                    onChange={(e) => handleChange('status', e.target.value)}
                    className="accent-[#F5A623]"
                  />
                  <span className="text-sm" style={{ color: '#FFF8EE' }}>
                    已发布
                  </span>
                </label>
              </div>
            </div>

            {/* 提交按钮 */}
            <div className="flex gap-4 pt-4">
              <motion.button
                type="submit"
                disabled={saving}
                className="flex-1 px-6 py-3 text-sm font-bold tracking-wider chamfer"
                style={{
                  backgroundColor: saving ? 'rgba(196, 215, 12, 0.5)' : '#C4D70C',
                  color: '#1A1612',
                  fontFamily: 'var(--font-display)',
                }}
                whileHover={{ scale: saving ? 1 : 1.02 }}
                whileTap={{ scale: saving ? 1 : 0.98 }}
                data-cursor-hover
              >
                {saving ? '保存中...' : isEditMode ? '更新文章' : '创建文章'}
              </motion.button>
              <button
                type="button"
                onClick={() => navigate('/blog')}
                className="px-6 py-3 text-sm font-bold tracking-wider chamfer-sm"
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
            </div>
          </form>
        </div>
      </main>

      {/* 底部框架 */}
      <footer
        className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between px-4 sm:px-6 lg:px-8"
        style={{
          height: 40,
          background: 'linear-gradient(180deg, #F5A623 0%, #FAA622 50%, #F5A623 100%)',
          borderTop: '2px solid #1A1612',
        }}
      >
        <div className="absolute top-2 left-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <div className="absolute top-2 right-2 w-1 h-1 rounded-full" style={{ backgroundColor: '#1A1612' }} />
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          DE hub 文献档案馆
        </span>
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          2026
        </span>
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          安全存储
        </span>
      </footer>
    </div>
  );
}
