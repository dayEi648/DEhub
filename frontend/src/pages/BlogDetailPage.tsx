import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { getBlogPostBySlug, getBlogPostById } from '../api/blog';
import {
  listComments,
  createComment,
  deleteComment,
  likeComment,
  unlikeComment,
} from '../api/comments';
import { favoriteBlogPost, unfavoriteBlogPost } from '../api/favorites';
import type { BlogPostDetailResponse, CommentResponse } from '../api/types';
import ArchiveHeader from '../components/archive/ArchiveHeader';
import FileHeader from '../components/archive/FileHeader';
import NoteCard from '../components/archive/NoteCard';

export default function BlogDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [post, setPost] = useState<BlogPostDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFavorited, setIsFavorited] = useState(false);

  // 评论相关状态
  const [comments, setComments] = useState<CommentResponse[]>([]);
  const [commentsTotal, setCommentsTotal] = useState(0);
  const [commentLoading, setCommentLoading] = useState(false);
  const [commentContent, setCommentContent] = useState('');
  const [commentPage, setCommentPage] = useState(1);
  const COMMENT_PAGE_SIZE = 10;

  const fetchPost = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError('');
    try {
      let data: BlogPostDetailResponse;
      if (/^\d+$/.test(slug)) {
        data = await getBlogPostById(Number(slug));
      } else {
        try {
          data = await getBlogPostBySlug(slug);
        } catch {
          data = await getBlogPostById(Number(slug));
        }
      }
      setPost(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '文章加载失败');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  const fetchComments = useCallback(async () => {
    if (!post) return;
    setCommentLoading(true);
    try {
      const res = await listComments({
        target_type: 'blog_post',
        target_id: post.id,
        sort_by: 'time',
        skip: (commentPage - 1) * COMMENT_PAGE_SIZE,
        limit: COMMENT_PAGE_SIZE,
      });
      setComments(res.items);
      setCommentsTotal(res.total);
    } catch {
      // 评论加载失败静默处理
    } finally {
      setCommentLoading(false);
    }
  }, [post, commentPage]);

  useEffect(() => {
    fetchPost();
  }, [fetchPost]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const handleFavorite = async () => {
    if (!post) return;
    try {
      if (isFavorited) {
        await unfavoriteBlogPost(post.id);
        setIsFavorited(false);
      } else {
        await favoriteBlogPost(post.id);
        setIsFavorited(true);
      }
    } catch {
      // 收藏操作失败静默处理
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!post || !commentContent.trim()) return;
    try {
      await createComment({
        target_type: 'blog_post',
        target_id: post.id,
        content: commentContent.trim(),
      });
      setCommentContent('');
      fetchComments();
    } catch {
      // 评论提交失败静默处理
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!window.confirm('确定删除这条评论吗？')) return;
    try {
      await deleteComment(commentId);
      fetchComments();
    } catch {
      // 删除失败静默处理
    }
  };

  const handleLikeComment = async (commentId: number, isLiked: boolean) => {
    try {
      if (isLiked) {
        await unlikeComment(commentId);
      } else {
        await likeComment(commentId);
      }
      fetchComments();
    } catch {
      // 点赞操作失败静默处理
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
            档案检索中...
          </span>
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" style={{ backgroundColor: '#0D0A07' }}>
        <p style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }} className="text-sm">
          {error || '档案不存在'}
        </p>
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 text-xs font-bold tracking-wider chamfer-sm"
          style={{
            backgroundColor: '#F5A623',
            color: '#1A1612',
            fontFamily: 'var(--font-mono)',
          }}
          data-cursor-hover
        >
          返回
        </button>
      </div>
    );
  }

  const fileNumber = `FL-${String(post.id).padStart(3, '0')}`;

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
        <ArchiveHeader mode="detail" fileNumber={fileNumber} />
      </header>

      {/* 主内容区域 */}
      <main
        className="flex-1 px-4 sm:px-6 lg:px-8 pb-8"
        style={{
          marginTop: 80,
          marginBottom: 40,
        }}
      >
        <div className="max-w-4xl mx-auto pt-6">
          {/* 文件夹头部 */}
          <FileHeader
            post={post}
            fileNumber={fileNumber}
            isFavorited={isFavorited}
            onFavorite={handleFavorite}
          />

          {/* 封面图 */}
          {post.cover_image_url && (
            <motion.div
              className="mb-6 relative overflow-hidden"
              style={{
                border: '3px solid #F5A623',
                boxShadow: '2px 2px 0px #F7F3E8',
              }}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <img
                src={post.cover_image_url}
                alt={post.title}
                className="w-full h-auto max-h-[400px] object-cover"
              />
            </motion.div>
          )}

          {/* 摘要 */}
          {post.summary && (
            <motion.div
              className="mb-8 p-5"
              style={{
                backgroundColor: 'rgba(42, 33, 24, 0.8)',
                borderLeft: '3px solid #F5A623',
              }}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <p
                className="text-sm leading-relaxed italic"
                style={{ color: '#FFF8EE', opacity: 0.75, fontFamily: 'var(--font-body)' }}
              >
                {post.summary}
              </p>
            </motion.div>
          )}

          {/* 正文内容 */}
          <motion.article
            className="prose prose-invert max-w-none mb-12"
            style={{
              color: '#FFF8EE',
              fontFamily: 'var(--font-body)',
              lineHeight: 1.9,
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(post.content_md) }}
          />

          {/* 上一篇/下一篇导航 */}
          <div className="flex flex-col sm:flex-row gap-4 mb-12">
            {post.prev_post && (
              <motion.div
                className="flex-1 p-4 cursor-pointer"
                style={{
                  backgroundColor: 'rgba(26, 22, 18, 0.9)',
                  border: '1px solid rgba(245, 166, 35, 0.2)',
                  clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
                }}
                whileHover={{
                  backgroundColor: '#F5A623',
                  x: -8,
                }}
                onClick={() => navigate(`/blog/${post.prev_post!.slug}`)}
                data-cursor-hover
              >
                <span
                  className="text-[9px] tracking-wider block mb-1"
                  style={{ fontFamily: 'var(--font-mono)', color: '#F5A623', opacity: 0.6 }}
                >
                  ← PREV FILE
                </span>
                <span
                  className="text-sm font-bold line-clamp-2"
                  style={{ color: '#FFF8EE', fontFamily: 'var(--font-body)' }}
                >
                  {post.prev_post.title}
                </span>
              </motion.div>
            )}
            {post.next_post && (
              <motion.div
                className="flex-1 p-4 cursor-pointer"
                style={{
                  backgroundColor: 'rgba(26, 22, 18, 0.9)',
                  border: '1px solid rgba(245, 166, 35, 0.2)',
                  clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
                }}
                whileHover={{
                  backgroundColor: '#F5A623',
                  x: 8,
                }}
                onClick={() => navigate(`/blog/${post.next_post!.slug}`)}
                data-cursor-hover
              >
                <span
                  className="text-[9px] tracking-wider block mb-1 text-right"
                  style={{ fontFamily: 'var(--font-mono)', color: '#F5A623', opacity: 0.6 }}
                >
                  NEXT FILE →
                </span>
                <span
                  className="text-sm font-bold line-clamp-2 text-right"
                  style={{ color: '#FFF8EE', fontFamily: 'var(--font-body)' }}
                >
                  {post.next_post.title}
                </span>
              </motion.div>
            )}
          </div>

          {/* 评论区域（便签墙） */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#F5A623' }} />
              <span
                className="text-[10px] tracking-[0.3em] font-bold"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                FIELD NOTES ({commentsTotal})
              </span>
              <div className="h-px flex-1 bg-[#F5A623]/15" />
            </div>

            {/* 评论输入框 */}
            <form onSubmit={handleSubmitComment} className="mb-6">
              <div className="flex gap-3">
                <textarea
                  value={commentContent}
                  onChange={(e) => setCommentContent(e.target.value)}
                  placeholder="添加便签..."
                  rows={3}
                  className="flex-1 px-3 py-2 text-sm resize-none outline-none"
                  style={{
                    backgroundColor: 'rgba(42, 33, 24, 0.8)',
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                    border: '1px solid rgba(245, 166, 35, 0.2)',
                  }}
                />
                <motion.button
                  type="submit"
                  className="px-4 py-2 text-xs font-bold tracking-wider chamfer-sm self-end"
                  style={{
                    backgroundColor: '#F5A623',
                    color: '#1A1612',
                    fontFamily: 'var(--font-mono)',
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  data-cursor-hover
                >
                  PIN
                </motion.button>
              </div>
            </form>

            {/* 评论列表 */}
            <div className="space-y-3">
              {commentLoading ? (
                <div className="text-center py-8">
                  <motion.div
                    className="w-6 h-6 border-2 border-[#F5A623] border-t-transparent mx-auto"
                    style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                </div>
              ) : comments.length === 0 ? (
                <div className="text-center py-8">
                  <p style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-body)' }}>
                    暂无便签，来添加第一条吧
                  </p>
                </div>
              ) : (
                comments.map((comment, index) => (
                  <NoteCard
                    key={comment.id}
                    comment={comment}
                    index={index}
                    onLike={() => handleLikeComment(comment.id, comment.is_liked)}
                    onDelete={() => handleDeleteComment(comment.id)}
                  />
                ))
              )}
            </div>

            {/* 评论分页 */}
            {commentsTotal > COMMENT_PAGE_SIZE && (
              <div className="flex justify-center gap-2 mt-4">
                {Array.from({ length: Math.ceil(commentsTotal / COMMENT_PAGE_SIZE) }, (_, i) => i + 1).map(
                  (page) => (
                    <button
                      key={page}
                      onClick={() => setCommentPage(page)}
                      className="px-2.5 py-1 text-[10px] font-bold tracking-wider min-w-[28px]"
                      style={{
                        backgroundColor: commentPage === page ? '#F5A623' : 'transparent',
                        color: commentPage === page ? '#1A1612' : '#FFF8EE',
                        fontFamily: 'var(--font-mono)',
                        border: commentPage === page ? 'none' : '1px solid rgba(245, 166, 35, 0.1)',
                      }}
                      data-cursor-hover
                    >
                      {page}
                    </button>
                  )
                )}
              </div>
            )}
          </motion.div>

          {/* 底部装饰 */}
          <div className="py-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[#F5A623]/10" />
              <span
                className="text-[9px] tracking-[0.3em] opacity-25"
                style={{ fontFamily: 'var(--font-mono)', color: '#F5A623' }}
              >
                END OF FILE
              </span>
              <div className="h-px flex-1 bg-[#F5A623]/10" />
            </div>
          </div>
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
          DE hub Documentary Archive
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
          SECURE STORAGE
        </span>
      </footer>
    </div>
  );
}

/** 简易 Markdown 渲染（仅支持基础语法） */
function renderMarkdown(md: string): string {
  if (!md) return '';

  return (
    md
      // 代码块
      .replace(/```([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>')
      // 行内代码
      .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
      // 标题
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // 粗体
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // 斜体
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // 删除线
      .replace(/~~(.*?)~~/g, '<del>$1</del>')
      // 链接
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
      // 无序列表
      .replace(/^\s*[-*+]\s+(.*$)/gim, '<li>$1</li>')
      // 有序列表
      .replace(/^\s*\d+\.\s+(.*$)/gim, '<li>$1</li>')
      // 引用
      .replace(/^\>\s+(.*$)/gim, '<blockquote>$1</blockquote>')
      // 水平线
      .replace(/^---+$/gim, '<hr />')
      // 段落（必须在最后）
      .replace(/\n\n/g, '</p><p>')
      .replace(/^(.+)$/gim, '<p>$1</p>')
      // 清理空标签
      .replace(/<p><\/p>/g, '')
      .replace(/<li>/g, '<ul><li>')
      .replace(/<\/li>\n(?!<li>)/g, '</li></ul>\n')
      .replace(/<blockquote>/g, '<blockquote><p>')
      .replace(/<\/blockquote>/g, '</p></blockquote>')
  );
}
