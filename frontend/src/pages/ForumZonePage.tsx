import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { MessageSquare, Eye, Flame, Clock, Plus, Heart } from 'lucide-react';
import { getForumZoneBySlug, listForumPosts } from '../api/forum';
import { followZone, unfollowZone, listFollowedZones } from '../api/favorites';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/Toast';
import type { ForumZoneResponse, ForumPostResponse, ForumPostSortBy } from '../api/types';
import Pagination from '../components/ui/Pagination';

const PAGE_SIZE = 15;

export default function ForumZonePage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { showToast } = useToast();

  const [zone, setZone] = useState<ForumZoneResponse | null>(null);
  const [posts, setPosts] = useState<ForumPostResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<ForumPostSortBy>('created');
  const [loadingZone, setLoadingZone] = useState(true);
  const [loadingPosts, setLoadingPosts] = useState(true);
  const [error, setError] = useState('');
  const [isFollowed, setIsFollowed] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  const fetchZone = useCallback(async () => {
    if (!slug) return;
    setLoadingZone(true);
    setError('');
    try {
      const data = await getForumZoneBySlug(slug);
      setZone(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '分区加载失败');
    } finally {
      setLoadingZone(false);
    }
  }, [slug]);

  const fetchPosts = useCallback(async () => {
    if (!zone) return;
    setLoadingPosts(true);
    try {
      const res = await listForumPosts({
        zone_id: zone.id,
        sort_by: sortBy,
        skip: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setPosts(res.items);
      setTotal(res.total);
    } catch (err) {
      // 静默处理
    } finally {
      setLoadingPosts(false);
    }
  }, [zone, sortBy, page]);

  const checkFollowStatus = useCallback(async () => {
    if (!zone || !user) return;
    try {
      const res = await listFollowedZones(0, 100);
      setIsFollowed(res.items.some((z) => z.id === zone.id));
    } catch {
      // 静默处理
    }
  }, [zone, user]);

  useEffect(() => {
    fetchZone();
  }, [fetchZone]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  useEffect(() => {
    checkFollowStatus();
  }, [checkFollowStatus]);

  const handleFollow = async () => {
    if (!zone || followLoading) return;
    setFollowLoading(true);
    const nextState = !isFollowed;
    setIsFollowed(nextState);
    try {
      if (nextState) {
        await followZone(zone.id);
        showToast('已关注分区', 'success');
      } else {
        await unfollowZone(zone.id);
        showToast('已取消关注', 'info');
      }
    } catch (err: unknown) {
      setIsFollowed(!nextState);
      const msg = err instanceof Error ? err.message : '操作失败';
      showToast(msg, 'error');
    } finally {
      setFollowLoading(false);
    }
  };

  const handleSortChange = (sort: ForumPostSortBy) => {
    setSortBy(sort);
    setPage(1);
  };

  if (loadingZone) {
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
            加载分区中...
          </span>
        </div>
      </div>
    );
  }

  if (error || !zone) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4" style={{ backgroundColor: '#0D0A07' }}>
        <p style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }} className="text-sm">
          {error || '分区不存在'}
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
            onClick={() => navigate('/forum')}
            className="text-[10px] font-bold tracking-widest flex items-center gap-1"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
            data-cursor-hover
          >
            <span>←</span> 论坛
          </button>
          <div className="h-4 w-px" style={{ backgroundColor: 'rgba(26,22,18,0.3)' }} />
          <span className="text-xs font-bold tracking-wider hidden sm:inline" style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}>
            {zone.zone_name}
          </span>
        </div>
        <span className="text-[9px] tracking-wider font-bold" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          {zone.slug.toUpperCase()}
        </span>
      </header>

      {/* 主内容区域 */}
      <main className="flex-1 px-4 sm:px-6 lg:px-8 pb-8" style={{ marginTop: 80, marginBottom: 40 }}>
        <div className="max-w-4xl mx-auto pt-6">
          {/* 分区信息卡片 */}
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
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <h1
                    className="text-lg sm:text-xl font-black"
                    style={{ color: '#FFF8EE', fontFamily: 'var(--font-display)' }}
                  >
                    {zone.zone_name}
                  </h1>
                  <span
                    className="text-[9px] tracking-wider px-1.5 py-0.5"
                    style={{
                      backgroundColor: 'rgba(127, 230, 239, 0.1)',
                      color: '#7FE6EF',
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {zone.slug}
                  </span>
                </div>
                {zone.description && (
                  <p className="text-sm mb-3" style={{ color: '#FFF8EE', opacity: 0.6, fontFamily: 'var(--font-body)' }}>
                    {zone.description}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-[9px]" style={{ color: '#FFF8EE', opacity: 0.4, fontFamily: 'var(--font-mono)' }}>
                    区主: {zone.manager.username}
                  </span>
                  <span className="flex items-center gap-1">
                    <Eye size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                    <span className="text-[9px]" style={{ color: '#7FE6EF', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>
                      {zone.view_count}
                    </span>
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageSquare size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                    <span className="text-[9px]" style={{ color: '#7FE6EF', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>
                      {total}
                    </span>
                  </span>
                </div>
              </div>

              <div className="flex flex-col gap-2 shrink-0">
                <motion.button
                  onClick={handleFollow}
                  disabled={followLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                  style={{
                    backgroundColor: isFollowed ? 'rgba(127, 230, 239, 0.15)' : '#7FE6EF',
                    color: isFollowed ? '#7FE6EF' : '#1A1612',
                    border: isFollowed ? '1px solid rgba(127, 230, 239, 0.3)' : 'none',
                    fontFamily: 'var(--font-mono)',
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  data-cursor-hover
                >
                  <Heart size={12} fill={isFollowed ? '#7FE6EF' : 'none'} />
                  {isFollowed ? '已关注' : '关注'}
                </motion.button>
                <motion.button
                  onClick={() => navigate('/forum/create', { state: { zoneId: zone.id } })}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold tracking-wider chamfer-sm"
                  style={{
                    backgroundColor: '#C4D70C',
                    color: '#1A1612',
                    fontFamily: 'var(--font-mono)',
                  }}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  data-cursor-hover
                >
                  <Plus size={12} />
                  发帖
                </motion.button>
              </div>
            </div>
          </motion.div>

          {/* 排序栏 */}
          <motion.div
            className="flex items-center gap-3 mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: 0.1 }}
          >
            <span className="text-[10px] tracking-[0.3em] font-bold" style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}>
              话题列表
            </span>
            <div className="h-px flex-1 bg-[#7FE6EF]/15" />
            <div className="flex items-center gap-1">
              <SortButton
                active={sortBy === 'created'}
                onClick={() => handleSortChange('created')}
                icon={<Clock size={10} />}
                label="最新"
              />
              <SortButton
                active={sortBy === 'view'}
                onClick={() => handleSortChange('view')}
                icon={<Flame size={10} />}
                label="热门"
              />
            </div>
          </motion.div>

          {/* 帖子列表 */}
          {loadingPosts ? (
            <div className="flex items-center justify-center py-16">
              <motion.div
                className="w-8 h-8 border-2 border-[#7FE6EF] border-t-transparent"
                style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
            </div>
          ) : posts.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-base mb-2" style={{ color: '#7FE6EF', opacity: 0.5, fontFamily: 'var(--font-mono)' }}>
                空频道
              </p>
              <p className="text-sm" style={{ color: '#FFF8EE', opacity: 0.4, fontFamily: 'var(--font-body)' }}>
                该分区暂无话题，来发布第一条吧
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-3">
                {posts.map((post, index) => (
                  <motion.div
                    key={post.id}
                    className="cursor-pointer"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.04 }}
                    onClick={() => navigate(`/forum/posts/${post.id}`)}
                    data-cursor-hover
                  >
                    <div
                      className="flex items-start gap-3 sm:gap-4 p-4 transition-all duration-200"
                      style={{
                        backgroundColor: 'rgba(42, 33, 24, 0.6)',
                        border: '1px solid rgba(127, 230, 239, 0.06)',
                        clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(127, 230, 239, 0.04)';
                        e.currentTarget.style.borderColor = 'rgba(127, 230, 239, 0.2)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(42, 33, 24, 0.6)';
                        e.currentTarget.style.borderColor = 'rgba(127, 230, 239, 0.06)';
                      }}
                    >
                      <div className="flex flex-col items-center gap-1 shrink-0 pt-1">
                        <div
                          className="w-8 h-8 sm:w-9 sm:h-9 flex items-center justify-center text-xs font-bold"
                          style={{
                            backgroundColor: 'rgba(127, 230, 239, 0.1)',
                            color: '#7FE6EF',
                            fontFamily: 'var(--font-mono)',
                            clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                          }}
                        >
                          {post.user.username.slice(0, 2).toUpperCase()}
                        </div>
                      </div>

                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm sm:text-base font-medium leading-snug mb-1" style={{ color: '#FFF8EE' }}>
                          {post.title}
                        </h3>
                        <div className="flex flex-wrap items-center gap-3">
                          <span className="text-[9px]" style={{ color: '#FFF8EE', opacity: 0.4, fontFamily: 'var(--font-mono)' }}>
                            BY {post.user.username}
                          </span>
                          <span className="flex items-center gap-1">
                            <Eye size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                            <span className="text-[9px]" style={{ color: '#7FE6EF', opacity: 0.6, fontFamily: 'var(--font-mono)' }}>
                              {post.view_count}
                            </span>
                          </span>
                          <span className="flex items-center gap-1">
                            <MessageSquare size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                            <span className="text-[9px]" style={{ color: '#7FE6EF', opacity: 0.6, fontFamily: 'var(--font-mono)' }}>
                              {post.reply_count}
                            </span>
                          </span>
                          <span className="text-[9px]" style={{ color: '#FFF8EE', opacity: 0.25, fontFamily: 'var(--font-mono)' }}>
                            {new Date(post.created_at).toLocaleDateString('zh-CN')}
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {total > PAGE_SIZE && (
                <motion.div className="flex justify-center py-8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
                  <Pagination current={page} total={total} pageSize={PAGE_SIZE} onChange={setPage} />
                </motion.div>
              )}
            </>
          )}

          {/* 底部装饰 */}
          <div className="py-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[#7FE6EF]/10" />
              <span className="text-[9px] tracking-[0.3em] opacity-25" style={{ fontFamily: 'var(--font-mono)', color: '#7FE6EF' }}>
                频道结束
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
          {zone.zone_name}
        </span>
        <span className="text-[9px] tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          CH.02
        </span>
        <span className="text-[9px] tracking-wider" style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}>
          {total} 个话题
        </span>
      </footer>
    </div>
  );
}

function SortButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold tracking-wider chamfer-sm"
      style={{
        backgroundColor: active ? '#7FE6EF' : 'transparent',
        color: active ? '#1A1612' : '#FFF8EE',
        border: active ? 'none' : '1px solid rgba(127, 230, 239, 0.2)',
        fontFamily: 'var(--font-mono)',
      }}
      data-cursor-hover
    >
      {icon}
      {label}
    </button>
  );
}
