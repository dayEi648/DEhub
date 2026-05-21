import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { MessageSquare, Eye, Heart, ArrowLeft, Trash2, Edit3 } from 'lucide-react';
import { getForumPostById, deleteForumPost, createForumReply, listForumReplies, deleteForumReply } from '../api/forum';
import { listComments, createComment, deleteComment, likeComment, unlikeComment } from '../api/comments';
import { favoriteForumPost, unfavoriteForumPost, listForumPostFavorites } from '../api/favorites';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';
import Pagination from '../components/ui/Pagination';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import type {
  ForumPostResponse,
  ForumReplyResponse,
  CommentResponse,
} from '../api/types';

const REPLY_PAGE_SIZE = 10;
const COMMENT_PAGE_SIZE = 10;

export default function ForumPostDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAdmin, user } = useAuth();
  const { showToast } = useToast();

  const [post, setPost] = useState<ForumPostResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFavorited, setIsFavorited] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);

  // 回复相关
  const [replies, setReplies] = useState<ForumReplyResponse[]>([]);
  const [repliesTotal, setRepliesTotal] = useState(0);
  const [replyPage, setReplyPage] = useState(1);
  const [loadingReplies, setLoadingReplies] = useState(false);
  const [replyContent, setReplyContent] = useState('');

  // 评论相关（对回复的评论）
  const [commentsMap, setCommentsMap] = useState<Record<number, CommentResponse[]>>({});
  const [commentsTotalMap, setCommentsTotalMap] = useState<Record<number, number>>({});
  const [expandedComments, setExpandedComments] = useState<Set<number>>(new Set());
  const [loadingCommentsMap, setLoadingCommentsMap] = useState<Record<number, boolean>>({});
  const [commentPageMap, setCommentPageMap] = useState<Record<number, number>>({});
  const [commentContentMap, setCommentContentMap] = useState<Record<number, string>>({});

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{ type: 'post' | 'reply'; id: number } | null>(null);

  const fetchPost = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError('');
    try {
      const data = await getForumPostById(Number(id));
      setPost(data);
      try {
        const favRes = await listForumPostFavorites(0, 100);
        setIsFavorited(favRes.items.some((item) => item.id === data.id));
      } catch {
        // 静默
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '帖子加载失败');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const fetchReplies = useCallback(async () => {
    if (!post) return;
    setLoadingReplies(true);
    try {
      const res = await listForumReplies(post.id, (replyPage - 1) * REPLY_PAGE_SIZE, REPLY_PAGE_SIZE);
      setReplies(res.items);
      setRepliesTotal(res.total);
    } catch {
      // 静默
    } finally {
      setLoadingReplies(false);
    }
  }, [post, replyPage]);

  useEffect(() => {
    fetchPost();
  }, [fetchPost]);

  useEffect(() => {
    fetchReplies();
  }, [fetchReplies]);

  const fetchCommentsForReply = useCallback(async (replyId: number) => {
    const page = commentPageMap[replyId] || 1;
    setLoadingCommentsMap((prev) => ({ ...prev, [replyId]: true }));
    try {
      const res = await listComments({
        target_type: 'forum_reply',
        target_id: replyId,
        parent_id: 0,
        sort_by: 'time',
        skip: (page - 1) * COMMENT_PAGE_SIZE,
        limit: COMMENT_PAGE_SIZE,
      });
      setCommentsMap((prev) => ({ ...prev, [replyId]: res.items }));
      setCommentsTotalMap((prev) => ({ ...prev, [replyId]: res.total }));
    } catch {
      // 静默
    } finally {
      setLoadingCommentsMap((prev) => ({ ...prev, [replyId]: false }));
    }
  }, [commentPageMap]);

  const handleFavorite = async () => {
    if (!post || favoriteLoading) return;
    setFavoriteLoading(true);
    const nextState = !isFavorited;
    setIsFavorited(nextState);
    try {
      if (nextState) {
        await favoriteForumPost(post.id);
        showToast('已收藏帖子', 'success');
      } else {
        await unfavoriteForumPost(post.id);
        showToast('已取消收藏', 'info');
      }
    } catch (err: unknown) {
      setIsFavorited(!nextState);
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    } finally {
      setFavoriteLoading(false);
    }
  };

  const handleSubmitReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!post || !replyContent.trim()) return;
    try {
      await createForumReply(post.id, { content: replyContent.trim() });
      setReplyContent('');
      fetchReplies();
      showToast('回复已发送', 'success');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '回复发送失败';
      showToast(msg, 'error');
    }
  };

  const handleSubmitComment = async (replyId: number) => {
    const content = commentContentMap[replyId] || '';
    if (!content.trim()) return;
    try {
      await createComment({
        target_type: 'forum_reply',
        target_id: replyId,
        content: content.trim(),
      });
      setCommentContentMap((prev) => ({ ...prev, [replyId]: '' }));
      fetchCommentsForReply(replyId);
      showToast('评论已发送', 'success');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '评论发送失败';
      showToast(msg, 'error');
    }
  };

  const toggleComments = (replyId: number) => {
    setExpandedComments((prev) => {
      const next = new Set(prev);
      if (next.has(replyId)) {
        next.delete(replyId);
      } else {
        next.add(replyId);
        if (!commentsMap[replyId]) {
          fetchCommentsForReply(replyId);
        }
      }
      return next;
    });
  };

  const handleLikeComment = async (comment: CommentResponse, replyId: number) => {
    try {
      if (comment.is_liked) {
        await unlikeComment(comment.id);
      } else {
        await likeComment(comment.id);
      }
      fetchCommentsForReply(replyId);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    }
  };

  const handleDeleteComment = async (commentId: number, replyId: number) => {
    try {
      await deleteComment(commentId);
      fetchCommentsForReply(replyId);
      showToast('评论已删除', 'success');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '删除失败';
      showToast(msg, 'error');
    }
  };

  const canManagePost = () => {
    if (!post || !user) return false;
    return isAdmin || user.id === post.user_id;
  };

  const canManageReply = (reply: ForumReplyResponse) => {
    if (!user) return false;
    return isAdmin || user.id === reply.user_id;
  };

  const openDeleteDialog = (type: 'post' | 'reply', id: number) => {
    setDeleteTarget({ type, id });
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (deleteTarget.type === 'post') {
        await deleteForumPost(deleteTarget.id);
        showToast('帖子已删除', 'success');
        navigate(`/forum/zones/${post?.zone_id}`);
      } else {
        await deleteForumReply(deleteTarget.id);
        showToast('回复已删除', 'success');
        fetchReplies();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '删除失败';
      showToast(msg, 'error');
    } finally {
      setDeleteDialogOpen(false);
      setDeleteTarget(null);
    }
  };

  if (loading) {
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
            加载话题中...
          </span>
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" style={{ backgroundColor: '#0D0A07' }}>
        <p style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }} className="text-sm">
          {error || '话题不存在'}
        </p>
        <button
          onClick={() => navigate('/forum')}
          className="px-4 py-2 text-xs font-bold tracking-wider chamfer-sm"
          style={{ backgroundColor: '#7FE6EF', color: '#1A1612', fontFamily: 'var(--font-mono)' }}
          data-cursor-hover
        >
          返回论坛
        </button>
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
          <span className="text-xs font-bold tracking-wider hidden sm:inline truncate max-w-[200px] lg:max-w-[400px]" style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}>
            {post.title}
          </span>
        </div>
        <span className="text-[9px] tracking-wider font-bold" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          TALK SHOW
        </span>
      </header>

      {/* 主内容区域 */}
      <main className="flex-1 px-4 sm:px-6 lg:px-8 pb-8" style={{ marginTop: 80, marginBottom: 40 }}>
        <div className="max-w-4xl mx-auto pt-6">
          {/* 帖子头部 */}
          <motion.div
            className="mb-6 p-5 sm:p-6"
            style={{
              backgroundColor: 'rgba(42, 33, 24, 0.6)',
              border: '1px solid rgba(127, 230, 239, 0.15)',
              clipPath: 'polygon(12px 0%, 100% 0%, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0% 100%, 0% 12px)',
            }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-start justify-between gap-4 mb-4">
              <div className="flex-1 min-w-0">
                <h1
                  className="text-lg sm:text-xl font-black leading-snug mb-3"
                  style={{ color: '#FFF8EE', fontFamily: 'var(--font-display)' }}
                >
                  {post.title}
                </h1>
                <div className="flex flex-wrap items-center gap-3">
                  <div
                    className="w-6 h-6 flex items-center justify-center text-[10px] font-bold"
                    style={{
                      backgroundColor: 'rgba(127, 230, 239, 0.1)',
                      color: '#7FE6EF',
                      fontFamily: 'var(--font-mono)',
                      clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                    }}
                  >
                    {post.user.username.slice(0, 2).toUpperCase()}
                  </div>
                  <span className="text-[10px]" style={{ color: '#FFF8EE', opacity: 0.6, fontFamily: 'var(--font-mono)' }}>
                    {post.user.username}
                  </span>
                  <span className="text-[9px]" style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-mono)' }}>
                    {new Date(post.created_at).toLocaleDateString('zh-CN')}
                  </span>
                  <span className="flex items-center gap-1">
                    <Eye size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                    <span className="text-[9px]" style={{ color: '#7FE6EF', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>
                      {post.view_count}
                    </span>
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageSquare size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                    <span className="text-[9px]" style={{ color: '#7FE6EF', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>
                      {post.reply_count}
                    </span>
                  </span>
                </div>
              </div>

              <div className="flex flex-col gap-2 shrink-0">
                <motion.button
                  onClick={handleFavorite}
                  disabled={favoriteLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                  style={{
                    backgroundColor: isFavorited ? 'rgba(127, 230, 239, 0.15)' : 'transparent',
                    color: isFavorited ? '#7FE6EF' : '#FFF8EE',
                    border: '1px solid rgba(127, 230, 239, 0.25)',
                    fontFamily: 'var(--font-mono)',
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  data-cursor-hover
                >
                  <Heart size={12} fill={isFavorited ? '#7FE6EF' : 'none'} />
                  {isFavorited ? '已收藏' : '收藏'}
                </motion.button>
                {canManagePost() && (
                  <>
                    <motion.button
                      onClick={() => navigate(`/forum/edit/${post.id}`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                      style={{
                        backgroundColor: '#F5A623',
                        color: '#1A1612',
                        fontFamily: 'var(--font-mono)',
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      data-cursor-hover
                    >
                      <Edit3 size={12} />
                      编辑
                    </motion.button>
                    <motion.button
                      onClick={() => openDeleteDialog('post', post.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                      style={{
                        backgroundColor: 'transparent',
                        color: '#FF4D4D',
                        border: '1px solid rgba(255, 77, 77, 0.3)',
                        fontFamily: 'var(--font-mono)',
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      data-cursor-hover
                    >
                      <Trash2 size={12} />
                      删除
                    </motion.button>
                  </>
                )}
              </div>
            </div>

            {/* 帖子内容 */}
            <div
              className="text-sm leading-relaxed whitespace-pre-wrap"
              style={{ color: '#FFF8EE', opacity: 0.85, fontFamily: 'var(--font-body)' }}
            >
              {post.content}
            </div>
          </motion.div>

          {/* 回复输入框 */}
          <motion.div
            className="mb-6"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <MessageSquare size={14} style={{ color: '#7FE6EF' }} />
              <span className="text-[10px] tracking-[0.3em] font-bold" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
                发表回复
              </span>
              <div className="h-px flex-1 bg-[#7FE6EF]/15" />
            </div>
            <form onSubmit={handleSubmitReply}>
              <div className="flex gap-3">
                <textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder="写下你的回复..."
                  rows={4}
                  className="flex-1 px-3 py-2 text-sm resize-none outline-none"
                  style={{
                    backgroundColor: 'rgba(42, 33, 24, 0.8)',
                    color: '#FFF8EE',
                    fontFamily: 'var(--font-body)',
                    border: '1px solid rgba(127, 230, 239, 0.2)',
                  }}
                />
                <motion.button
                  type="submit"
                  className="px-4 py-2 text-xs font-bold tracking-wider chamfer-sm self-end"
                  style={{
                    backgroundColor: '#7FE6EF',
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
          </motion.div>

          {/* 回复列表 */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <MessageSquare size={14} style={{ color: '#7FE6EF' }} />
              <span className="text-[10px] tracking-[0.3em] font-bold" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
                全部回复
              </span>
              <span
                className="text-[10px] font-bold px-1.5 py-0.5"
                style={{
                  backgroundColor: '#7FE6EF',
                  color: '#1A1612',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {post.reply_count}
              </span>
              <div className="h-px flex-1 bg-[#7FE6EF]/15" />
            </div>

            {loadingReplies ? (
              <div className="flex items-center justify-center py-12">
                <motion.div
                  className="w-8 h-8 border-2 border-[#7FE6EF] border-t-transparent"
                  style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
              </div>
            ) : replies.length === 0 ? (
              <div className="text-center py-12">
                <p style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-mono)' }}>
                  暂无回复，来发表第一条吧
                </p>
              </div>
            ) : (
              <>
                <div className="space-y-4">
                  {replies.map((reply, index) => (
                    <motion.div
                      key={reply.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                    >
                      <div
                        className="p-4 sm:p-5"
                        style={{
                          backgroundColor: 'rgba(42, 33, 24, 0.6)',
                          border: '1px solid rgba(127, 230, 239, 0.08)',
                          clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
                        }}
                      >
                        {/* 回复头部 */}
                        <div className="flex items-start justify-between gap-3 mb-3">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-7 h-7 flex items-center justify-center text-[9px] font-bold"
                              style={{
                                backgroundColor: 'rgba(127, 230, 239, 0.1)',
                                color: '#7FE6EF',
                                fontFamily: 'var(--font-mono)',
                                clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                              }}
                            >
                              {reply.user.username.slice(0, 2).toUpperCase()}
                            </div>
                            <div>
                              <span className="text-[10px] font-bold block" style={{ color: '#FFF8EE', fontFamily: 'var(--font-mono)' }}>
                                {reply.user.username}
                              </span>
                              <span className="text-[9px]" style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-mono)' }}>
                                {new Date(reply.created_at).toLocaleDateString('zh-CN')}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="flex items-center gap-1">
                              <Heart size={10} style={{ color: '#FF4D4D', opacity: 0.5 }} />
                              <span className="text-[9px]" style={{ color: '#FF4D4D', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>
                                {reply.likecount}
                              </span>
                            </span>
                            {canManageReply(reply) && (
                              <button
                                onClick={() => openDeleteDialog('reply', reply.id)}
                                className="text-[9px] px-2 py-0.5 transition-colors"
                                style={{
                                  color: '#FF4D4D',
                                  border: '1px solid rgba(255, 77, 77, 0.2)',
                                  fontFamily: 'var(--font-mono)',
                                }}
                                data-cursor-hover
                              >
                                删除
                              </button>
                            )}
                          </div>
                        </div>

                        {/* 回复内容 */}
                        <div
                          className="text-sm leading-relaxed mb-3"
                          style={{ color: '#FFF8EE', opacity: 0.85, fontFamily: 'var(--font-body)' }}
                        >
                          {reply.content}
                        </div>

                        {/* 查看/发表评论 */}
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => toggleComments(reply.id)}
                            className="text-[9px] tracking-wider flex items-center gap-1 transition-all duration-200 hover:text-[#7FE6EF]"
                            style={{
                              color: expandedComments.has(reply.id) ? '#7FE6EF' : 'rgba(247, 243, 232, 0.4)',
                              fontFamily: 'var(--font-mono)',
                            }}
                            data-cursor-hover
                          >
                            <motion.span
                              animate={{ rotate: expandedComments.has(reply.id) ? 90 : 0 }}
                              transition={{ duration: 0.2 }}
                            >
                              ▶
                            </motion.span>
                            {expandedComments.has(reply.id)
                              ? '收起评论'
                              : `查看评论 (${reply.comment_count})`}
                          </button>
                        </div>

                        {/* 评论展开区域 */}
                        <AnimatePresence>
                          {expandedComments.has(reply.id) && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.3 }}
                              className="overflow-hidden"
                            >
                              <div className="mt-3 pt-3" style={{ borderTop: '1px solid rgba(127, 230, 239, 0.08)' }}>
                                {/* 评论输入 */}
                                <div className="flex gap-2 mb-3">
                                  <textarea
                                    value={commentContentMap[reply.id] || ''}
                                    onChange={(e) =>
                                      setCommentContentMap((prev) => ({ ...prev, [reply.id]: e.target.value }))
                                    }
                                    placeholder="对此回复发表评论..."
                                    rows={2}
                                    className="flex-1 px-3 py-2 text-xs resize-none outline-none"
                                    style={{
                                      backgroundColor: 'rgba(42, 33, 24, 0.6)',
                                      color: '#FFF8EE',
                                      fontFamily: 'var(--font-body)',
                                      border: '1px solid rgba(127, 230, 239, 0.1)',
                                    }}
                                  />
                                  <motion.button
                                    onClick={() => handleSubmitComment(reply.id)}
                                    className="px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm self-end"
                                    style={{
                                      backgroundColor: '#7FE6EF',
                                      color: '#1A1612',
                                      fontFamily: 'var(--font-mono)',
                                    }}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    data-cursor-hover
                                  >
                                    评论
                                  </motion.button>
                                </div>

                                {/* 评论列表 */}
                                {loadingCommentsMap[reply.id] ? (
                                  <div className="text-center py-4">
                                    <motion.div
                                      className="w-5 h-5 border-2 border-[#7FE6EF] border-t-transparent mx-auto"
                                      style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                                      animate={{ rotate: 360 }}
                                      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                                    />
                                  </div>
                                ) : (commentsMap[reply.id]?.length || 0) === 0 ? (
                                  <p className="text-[10px] py-2" style={{ color: '#FFF8EE', opacity: 0.2, fontFamily: 'var(--font-mono)' }}>
                                    暂无评论
                                  </p>
                                ) : (
                                  <div className="space-y-2">
                                    {commentsMap[reply.id]?.map((comment) => (
                                      <div
                                        key={comment.id}
                                        className="p-2.5"
                                        style={{
                                          backgroundColor: 'rgba(26, 22, 18, 0.5)',
                                          border: '1px solid rgba(127, 230, 239, 0.05)',
                                          clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
                                        }}
                                      >
                                        <div className="flex items-start justify-between gap-2">
                                          <div className="flex items-center gap-1.5 mb-1">
                                            <span className="text-[10px] font-bold" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
                                              {comment.user.username}
                                            </span>
                                            <span className="text-[9px]" style={{ color: '#FFF8EE', opacity: 0.25, fontFamily: 'var(--font-mono)' }}>
                                              {new Date(comment.created_at).toLocaleDateString('zh-CN')}
                                            </span>
                                          </div>
                                          <div className="flex items-center gap-2 shrink-0">
                                            <button
                                              onClick={() => handleLikeComment(comment, reply.id)}
                                              className="flex items-center gap-0.5 text-[9px] transition-colors"
                                              style={{
                                                color: comment.is_liked ? '#FF4D4D' : 'rgba(247, 243, 232, 0.3)',
                                                fontFamily: 'var(--font-mono)',
                                              }}
                                              data-cursor-hover
                                            >
                                              <Heart size={10} fill={comment.is_liked ? '#FF4D4D' : 'none'} />
                                              {comment.likecount}
                                            </button>
                                            {user && (user.id === comment.user_id || isAdmin) && (
                                              <button
                                                onClick={() => handleDeleteComment(comment.id, reply.id)}
                                                className="text-[9px] hover:text-[#FF4D4D] transition-colors"
                                                style={{ color: 'rgba(247, 243, 232, 0.25)', fontFamily: 'var(--font-mono)' }}
                                                data-cursor-hover
                                              >
                                                删除
                                              </button>
                                            )}
                                          </div>
                                        </div>
                                        <p className="text-xs leading-relaxed" style={{ color: '#FFF8EE', opacity: 0.7, fontFamily: 'var(--font-body)' }}>
                                          {comment.content}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                )}

                                {/* 评论分页 */}
                                {(commentsTotalMap[reply.id] || 0) > COMMENT_PAGE_SIZE && (
                                  <div className="flex justify-center mt-3">
                                    <Pagination
                                      current={commentPageMap[reply.id] || 1}
                                      total={commentsTotalMap[reply.id] || 0}
                                      pageSize={COMMENT_PAGE_SIZE}
                                      onChange={(p) => {
                                        setCommentPageMap((prev) => ({ ...prev, [reply.id]: p }));
                                        setTimeout(() => fetchCommentsForReply(reply.id), 0);
                                      }}
                                    />
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {repliesTotal > REPLY_PAGE_SIZE && (
                  <motion.div className="flex justify-center py-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
                    <Pagination current={replyPage} total={repliesTotal} pageSize={REPLY_PAGE_SIZE} onChange={setReplyPage} />
                  </motion.div>
                )}
              </>
            )}
          </motion.div>

          {/* 底部装饰 */}
          <div className="py-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[#7FE6EF]/10" />
              <span className="text-[9px] tracking-[0.3em] opacity-25" style={{ fontFamily: 'var(--font-mono)', color: '#7FE6EF' }}>
                话题结束
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
          {post.title.slice(0, 20)}{post.title.length > 20 ? '...' : ''}
        </span>
        <span className="text-[9px] tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          CH.02
        </span>
        <span className="text-[9px] tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          {post.reply_count} 回复
        </span>
      </footer>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="确认删除"
        message={deleteTarget?.type === 'post' ? '确定删除这个帖子吗？此操作不可撤销。' : '确定删除这条回复吗？'}
        danger
        onConfirm={handleConfirmDelete}
        onCancel={() => {
          setDeleteDialogOpen(false);
          setDeleteTarget(null);
        }}
      />
    </div>
  );
}
