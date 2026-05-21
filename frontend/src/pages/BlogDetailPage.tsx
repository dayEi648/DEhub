import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getBlogPostBySlug, getBlogPostById, deleteBlogPost, publishBlogPost, unpublishBlogPost } from '../api/blog';
import {
  listComments,
  createComment,
  deleteComment,
  likeComment,
  unlikeComment,
} from '../api/comments';
import { favoriteBlogPost, unfavoriteBlogPost, listBlogPostFavorites } from '../api/favorites';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';
import type { BlogPostDetailResponse, CommentResponse } from '../api/types';
import ArchiveHeader from '../components/archive/ArchiveHeader';
import FileHeader from '../components/archive/FileHeader';
import NoteCard from '../components/archive/NoteCard';
import Pagination from '../components/ui/Pagination';

export default function BlogDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { isAdmin, user } = useAuth();
  const { showToast } = useToast();
  const [post, setPost] = useState<BlogPostDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFavorited, setIsFavorited] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);

  // 评论相关状态
  const [commentsExpanded, setCommentsExpanded] = useState(false);
  const [topComments, setTopComments] = useState<CommentResponse[]>([]);
  const [topCommentsTotal, setTopCommentsTotal] = useState(0);
  const [commentLoading, setCommentLoading] = useState(false);
  const [topCommentContent, setTopCommentContent] = useState('');
  const [commentPage, setCommentPage] = useState(1);
  const COMMENT_PAGE_SIZE = 10;

  // 回复相关状态
  const [repliesMap, setRepliesMap] = useState<Record<number, CommentResponse[]>>({});
  const [expandedReplies, setExpandedReplies] = useState<Set<number>>(new Set());
  const [replyLoadingMap, setReplyLoadingMap] = useState<Record<number, boolean>>({});
  const [replyingTo, setReplyingTo] = useState<{
    topCommentId: number;
    nestedParentId?: number;
    username: string;
  } | null>(null);
  const [replyContentMap, setReplyContentMap] = useState<Record<number, string>>({});

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
      // 查询当前文章收藏状态
      try {
        const favRes = await listBlogPostFavorites(0, 100);
        setIsFavorited(favRes.items.some((item) => item.id === data.id));
      } catch {
        // 收藏状态查询失败不影响文章展示
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '文章加载失败');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  const fetchTopComments = useCallback(async () => {
    if (!post) return;
    setCommentLoading(true);
    try {
      const res = await listComments({
        target_type: 'blog_post',
        target_id: post.id,
        parent_id: 0,
        sort_by: 'time',
        skip: (commentPage - 1) * COMMENT_PAGE_SIZE,
        limit: COMMENT_PAGE_SIZE,
      });
      setTopComments(res.items);
      setTopCommentsTotal(res.total);
    } catch {
      // 评论加载失败静默处理
    } finally {
      setCommentLoading(false);
    }
  }, [post, commentPage]);

  const fetchReplies = useCallback(async (topCommentId: number) => {
    if (!post) return;
    setReplyLoadingMap((prev) => ({ ...prev, [topCommentId]: true }));
    try {
      const res = await listComments({
        target_type: 'blog_post',
        target_id: post.id,
        parent_id: topCommentId,
        sort_by: 'time',
        skip: 0,
        limit: 100,
      });
      setRepliesMap((prev) => ({ ...prev, [topCommentId]: res.items }));
    } catch {
      // 回复加载失败静默处理
    } finally {
      setReplyLoadingMap((prev) => ({ ...prev, [topCommentId]: false }));
    }
  }, [post]);

  useEffect(() => {
    fetchPost();
  }, [fetchPost]);

  useEffect(() => {
    if (commentsExpanded) {
      fetchTopComments();
    }
  }, [fetchTopComments, commentsExpanded]);

  const handleFavorite = async () => {
    if (!post || favoriteLoading) return;
    setFavoriteLoading(true);
    const nextState = !isFavorited;
    setIsFavorited(nextState); // 乐观更新
    try {
      if (nextState) {
        await favoriteBlogPost(post.id);
        showToast('已归档', 'success');
      } else {
        await unfavoriteBlogPost(post.id);
        showToast('已取消归档', 'info');
      }
    } catch (err: unknown) {
      setIsFavorited(!nextState); // 回滚
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    } finally {
      setFavoriteLoading(false);
    }
  };

  const handleSubmitTopComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!post || !topCommentContent.trim()) return;
    try {
      await createComment({
        target_type: 'blog_post',
        target_id: post.id,
        content: topCommentContent.trim(),
      });
      setTopCommentContent('');
      fetchTopComments();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '评论发送失败';
      showToast(msg, 'error');
    }
  };

  const handleSubmitReply = async (topCommentId: number) => {
    const rawContent = replyContentMap[topCommentId] || '';
    if (!post || !rawContent.trim()) return;
    try {
      let content = rawContent.trim();
      // 嵌套回复：在内容前拼接 @对方的用户名：
      if (replyingTo?.nestedParentId) {
        content = `@${replyingTo.username}：${content}`;
      }
      await createComment({
        target_type: 'blog_post',
        target_id: post.id,
        parent_id: topCommentId,
        is_nested: !!replyingTo?.nestedParentId,
        nested_parent_id: replyingTo?.nestedParentId,
        content,
      });
      setReplyContentMap((prev) => ({ ...prev, [topCommentId]: '' }));
      setReplyingTo(null);
      fetchReplies(topCommentId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '回复发送失败';
      showToast(msg, 'error');
    }
  };

  const handleDeleteComment = async (commentId: number, topCommentId?: number) => {
    if (!window.confirm('确定删除这条评论吗？')) return;
    try {
      await deleteComment(commentId);
      if (topCommentId) {
        fetchReplies(topCommentId);
      } else {
        fetchTopComments();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '删除失败';
      showToast(msg, 'error');
    }
  };

  const handleLikeComment = async (commentId: number, isLiked: boolean, topCommentId?: number) => {
    try {
      if (isLiked) {
        await unlikeComment(commentId);
      } else {
        await likeComment(commentId);
      }
      if (topCommentId) {
        fetchReplies(topCommentId);
      } else {
        fetchTopComments();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    }
  };

  const toggleReplies = (topCommentId: number) => {
    setExpandedReplies((prev) => {
      const next = new Set(prev);
      if (next.has(topCommentId)) {
        next.delete(topCommentId);
        setReplyingTo(null);
      } else {
        next.add(topCommentId);
        if (!repliesMap[topCommentId]) {
          fetchReplies(topCommentId);
        }
      }
      return next;
    });
  };

  const startReply = (topCommentId: number, reply: CommentResponse) => {
    // 嵌套回复只能回复里层回复（is_nested=false 的评论）
    if (reply.is_nested) return;
    setReplyingTo({
      topCommentId,
      nestedParentId: reply.id,
      username: reply.user.username,
    });
  };

  const cancelReply = () => {
    setReplyingTo(null);
  };

  // 管理员操作
  const handleDeletePost = async () => {
    if (!post) return;
    if (!window.confirm('确定删除这篇文章吗？此操作不可撤销。')) return;
    try {
      await deleteBlogPost(post.id);
      showToast('文章已删除', 'success');
      navigate('/blog');
    } catch {
      showToast('删除失败', 'error');
    }
  };

  const handleTogglePublish = async () => {
    if (!post) return;
    try {
      if (post.status === 'published') {
        await unpublishBlogPost(post.id);
        showToast('文章已下线', 'info');
      } else {
        await publishBlogPost(post.id);
        showToast('文章已发布', 'success');
      }
      fetchPost();
    } catch {
      showToast('操作失败', 'error');
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

          {/* 管理员操作栏 */}
          {isAdmin && (
            <motion.div
              className="flex flex-wrap gap-2 mb-4 p-3"
              style={{
                backgroundColor: 'rgba(194, 35, 3, 0.1)',
                border: '1px solid rgba(194, 35, 3, 0.2)',
                clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
              }}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
            >
              <span
                className="text-[9px] tracking-wider font-bold mr-2 self-center"
                style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}
              >
                管理员
              </span>
              <button
                onClick={() => navigate(`/blog/edit/${post.id}`)}
                className="px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                style={{
                  backgroundColor: '#F5A623',
                  color: '#1A1612',
                  fontFamily: 'var(--font-mono)',
                }}
                data-cursor-hover
              >
                编辑
              </button>
              <button
                onClick={handleTogglePublish}
                className="px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                style={{
                  backgroundColor: post.status === 'published' ? '#C22303' : '#C4D70C',
                  color: '#FFF8EE',
                  fontFamily: 'var(--font-mono)',
                }}
                data-cursor-hover
              >
                {post.status === 'published' ? '下线' : '发布'}
              </button>
              <button
                onClick={handleDeletePost}
                className="px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                style={{
                  backgroundColor: 'transparent',
                  color: '#FF4D4D',
                  border: '1px solid rgba(255, 77, 77, 0.3)',
                  fontFamily: 'var(--font-mono)',
                }}
                data-cursor-hover
              >
                删除
              </button>
            </motion.div>
          )}

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
            className="markdown-body max-w-none mb-12"
            style={{
              color: '#FFF8EE',
              fontFamily: 'var(--font-body)',
              lineHeight: 1.9,
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {post.content_md}
            </ReactMarkdown>
          </motion.article>

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
                  ← 上一篇
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
                  下一篇 →
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

          {/* 查找更多博客 */}
          <motion.div
            className="mb-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: 0.35 }}
          >
            <button
              onClick={() => navigate('/blog')}
              className="w-full flex items-center justify-center gap-3 p-4 cursor-pointer group"
              style={{
                backgroundColor: 'rgba(26, 22, 18, 0.9)',
                border: '1px solid rgba(245, 166, 35, 0.2)',
                clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
              }}
              data-cursor-hover
            >
              <span
                className="text-[10px] tracking-[0.3em] font-bold"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                查找更多博客
              </span>
              <span style={{ color: '#F5A623' }}>→</span>
            </button>
          </motion.div>

          {/* 评论区域（便签墙） */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            {/* 评论区头部 - 可点击展开/收起 */}
            <button
              onClick={() => setCommentsExpanded((prev) => !prev)}
              className="w-full flex items-center gap-3 mb-6 cursor-pointer group p-3"
              style={{
                backgroundColor: commentsExpanded ? 'transparent' : 'rgba(42, 33, 24, 0.6)',
                border: '1px solid rgba(245, 166, 35, 0.25)',
                clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
              }}
              data-cursor-hover
            >
              <div className="w-1.5 h-1.5 rotate-45 shrink-0" style={{ backgroundColor: '#F5A623' }} />
              <span
                className="text-[10px] tracking-[0.3em] font-bold shrink-0"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
              >
                评论
              </span>
              <span
                className="text-[10px] font-bold px-1.5 py-0.5 shrink-0"
                style={{
                  backgroundColor: '#F5A623',
                  color: '#1A1612',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {post.comment_count}
              </span>
              <div className="h-px flex-1 bg-[#F5A623]/20 group-hover:bg-[#F5A623]/40 transition-colors min-w-[20px]" />
              <motion.span
                className="text-[10px] shrink-0"
                style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
                animate={{ rotate: commentsExpanded ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                ▼
              </motion.span>
            </button>

            <AnimatePresence>
              {commentsExpanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* 表层评论输入框 */}
                  <form onSubmit={handleSubmitTopComment} className="mb-6">
                    <div className="flex gap-3">
                      <textarea
                        value={topCommentContent}
                        onChange={(e) => setTopCommentContent(e.target.value)}
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
                        发送
                      </motion.button>
                    </div>
                  </form>

                  {/* 表层评论列表 */}
                  <div className="space-y-4">
                    {commentLoading ? (
                      <div className="text-center py-8">
                        <motion.div
                          className="w-6 h-6 border-2 border-[#F5A623] border-t-transparent mx-auto"
                          style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        />
                      </div>
                    ) : topComments.length === 0 ? (
                      <div className="text-center py-8">
                        <p style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-body)' }}>
                          暂无便签，来添加第一条吧
                        </p>
                      </div>
                    ) : (
                      topComments.map((topComment, index) => (
                        <div key={topComment.id} className="space-y-2">
                          <NoteCard
                            comment={topComment}
                            index={index}
                            onLike={() => handleLikeComment(topComment.id, topComment.is_liked)}
                            onDelete={
                              user && (user.id === topComment.user_id || isAdmin)
                                ? () => handleDeleteComment(topComment.id)
                                : undefined
                            }
                          />

                          {/* 查看/收起回复 */}
                          <div className="pl-4">
                            <button
                              onClick={() => toggleReplies(topComment.id)}
                              className="text-[9px] tracking-wider flex items-center gap-1 transition-all duration-200 hover:text-[#F5A623]"
                              style={{
                                color: 'rgba(247, 243, 232, 0.4)',
                                fontFamily: 'var(--font-mono)',
                              }}
                              data-cursor-hover
                            >
                              <motion.span
                                animate={{ rotate: expandedReplies.has(topComment.id) ? 90 : 0 }}
                                transition={{ duration: 0.2 }}
                              >
                                ▶
                              </motion.span>
                              {expandedReplies.has(topComment.id)
                                ? '收起回复'
                                : `点击查看回复 (${repliesMap[topComment.id]?.length ?? '...'})`}
                            </button>
                          </div>

                          {/* 回复列表 */}
                          <AnimatePresence>
                            {expandedReplies.has(topComment.id) && (
                              <motion.div
                                className="pl-4 space-y-2"
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.3 }}
                              >
                                {replyLoadingMap[topComment.id] ? (
                                  <div className="text-center py-4">
                                    <motion.div
                                      className="w-4 h-4 border-2 border-[#F5A623] border-t-transparent mx-auto"
                                      style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                                      animate={{ rotate: 360 }}
                                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                    />
                                  </div>
                                ) : repliesMap[topComment.id]?.length === 0 ? (
                                  <p
                                    className="text-[10px] py-2"
                                    style={{ color: '#FFF8EE', opacity: 0.2, fontFamily: 'var(--font-mono)' }}
                                  >
                                    暂无回复
                                  </p>
                                ) : (
                                  repliesMap[topComment.id]?.map((reply, rIndex) => (
                                    <NoteCard
                                      key={reply.id}
                                      comment={reply}
                                      index={rIndex}
                                      isReply
                                      showReplyButton={!reply.is_nested}
                                      onLike={() =>
                                        handleLikeComment(reply.id, reply.is_liked, topComment.id)
                                      }
                                      onDelete={
                                        user && (user.id === reply.user_id || isAdmin)
                                          ? () => handleDeleteComment(reply.id, topComment.id)
                                          : undefined
                                      }
                                      onReply={() => startReply(topComment.id, reply)}
                                    />
                                  ))
                                )}

                                {/* 回复输入框 */}
                                <div className="pt-2">
                                  {replyingTo?.topCommentId === topComment.id && (
                                    <div
                                      className="flex items-center gap-2 mb-2 px-1"
                                      style={{ fontFamily: 'var(--font-mono)' }}
                                    >
                                      <span className="text-[9px]" style={{ color: '#C4D70C' }}>
                                        回复 @{replyingTo.username}
                                      </span>
                                      <button
                                        onClick={cancelReply}
                                        className="text-[9px] hover:text-[#FF4D4D] transition-colors"
                                        style={{ color: 'rgba(247, 243, 232, 0.4)' }}
                                        data-cursor-hover
                                      >
                                        取消
                                      </button>
                                    </div>
                                  )}
                                  <div className="flex gap-3">
                                    <textarea
                                      value={replyContentMap[topComment.id] || ''}
                                      onChange={(e) => {
                                        setReplyContentMap((prev) => ({
                                          ...prev,
                                          [topComment.id]: e.target.value,
                                        }));
                                      }}
                                      placeholder="写回复..."
                                      rows={2}
                                      className="flex-1 px-3 py-2 text-sm resize-none outline-none"
                                      style={{
                                        backgroundColor: 'rgba(42, 33, 24, 0.6)',
                                        color: '#FFF8EE',
                                        fontFamily: 'var(--font-body)',
                                        border: '1px solid rgba(245, 166, 35, 0.15)',
                                      }}
                                    />
                                    <motion.button
                                      onClick={() => handleSubmitReply(topComment.id)}
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
                                      回复
                                    </motion.button>
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      ))
                    )}
                  </div>

                  {/* 表层评论分页 */}
                  {topCommentsTotal > COMMENT_PAGE_SIZE && (
                    <div className="flex justify-center mt-4">
                      <Pagination
                        current={commentPage}
                        total={topCommentsTotal}
                        pageSize={COMMENT_PAGE_SIZE}
                        onChange={setCommentPage}
                      />
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* 底部装饰 */}
          <div className="py-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[#F5A623]/10" />
              <span
                className="text-[9px] tracking-[0.3em] opacity-25"
                style={{ fontFamily: 'var(--font-mono)', color: '#F5A623' }}
              >
                文件结束
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
