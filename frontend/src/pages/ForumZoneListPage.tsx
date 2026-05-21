import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Eye, Flame, Users } from 'lucide-react';
import { listForumZones, listForumPosts } from '../api/forum';
import type { ForumZoneResponse, ForumPostResponse } from '../api/types';
import Pagination from '../components/ui/Pagination';

const POST_PAGE_SIZE = 10;

export default function ForumZoneListPage() {
  const navigate = useNavigate();
  const [zones, setZones] = useState<ForumZoneResponse[]>([]);
  const [hotPosts, setHotPosts] = useState<ForumPostResponse[]>([]);
  const [hotTotal, setHotTotal] = useState(0);
  const [hotPage, setHotPage] = useState(1);
  const [loadingZones, setLoadingZones] = useState(true);
  const [loadingPosts, setLoadingPosts] = useState(true);
  const [error, setError] = useState('');

  const fetchZones = useCallback(async () => {
    setLoadingZones(true);
    try {
      const res = await listForumZones();
      setZones(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoadingZones(false);
    }
  }, []);

  const fetchHotPosts = useCallback(async () => {
    setLoadingPosts(true);
    try {
      const res = await listForumPosts({
        sort_by: 'view',
        skip: (hotPage - 1) * POST_PAGE_SIZE,
        limit: POST_PAGE_SIZE,
      });
      setHotPosts(res.items);
      setHotTotal(res.total);
    } catch (err) {
      // 热门帖子加载失败静默处理
    } finally {
      setLoadingPosts(false);
    }
  }, [hotPage]);

  useEffect(() => {
    fetchZones();
  }, [fetchZones]);

  useEffect(() => {
    fetchHotPosts();
  }, [fetchHotPosts]);

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
            onClick={() => navigate('/')}
            className="text-[10px] font-bold tracking-widest flex items-center gap-1"
            style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
            data-cursor-hover
          >
            <span>←</span> 返回
          </button>
          <div className="h-4 w-px" style={{ backgroundColor: 'rgba(26,22,18,0.3)' }} />
          <span
            className="text-xs font-bold tracking-wider hidden sm:inline"
            style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
          >
            DE hub 论坛中心
          </span>
        </div>
        <span
          className="text-[9px] tracking-wider font-bold"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          FORUM CENTER
        </span>
      </header>

      {/* 主内容区域 */}
      <main
        className="flex-1 px-4 sm:px-6 lg:px-8 pb-8"
        style={{
          marginTop: 80,
          marginBottom: 40,
        }}
      >
        <div className="max-w-5xl mx-auto pt-6">
          {/* 频道标识 */}
          <motion.div
            className="mb-8 flex items-center gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#7FE6EF' }} />
            <span
              className="text-[10px] tracking-[0.3em] font-bold"
              style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}
            >
              TALK SHOW CHANNEL
            </span>
            <div className="h-px flex-1 bg-[#7FE6EF]/15" />
          </motion.div>

          {error && (
            <div className="text-center py-12">
              <p style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }} className="text-sm">
                {error}
              </p>
            </div>
          )}

          {/* 分区卡片网格 */}
          <motion.div
            className="mb-10"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <Users size={14} style={{ color: '#7FE6EF' }} />
              <span
                className="text-[10px] tracking-[0.3em] font-bold"
                style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}
              >
                讨论分区
              </span>
              <div className="h-px flex-1 bg-[#7FE6EF]/15" />
            </div>

            {loadingZones ? (
              <div className="flex items-center justify-center py-12">
                <motion.div
                  className="w-8 h-8 border-2 border-[#7FE6EF] border-t-transparent"
                  style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
              </div>
            ) : zones.length === 0 ? (
              <div className="text-center py-12">
                <p style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-mono)' }}>
                  暂无分区
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {zones.map((zone, index) => (
                  <motion.div
                    key={zone.id}
                    className="cursor-pointer group"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: index * 0.08 }}
                    onClick={() => navigate(`/forum/zones/${zone.slug}`)}
                    data-cursor-hover
                  >
                    <div
                      className="p-4 sm:p-5 h-full transition-all duration-200"
                      style={{
                        backgroundColor: 'rgba(42, 33, 24, 0.6)',
                        border: '1px solid rgba(127, 230, 239, 0.1)',
                        clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(127, 230, 239, 0.06)';
                        e.currentTarget.style.borderColor = 'rgba(127, 230, 239, 0.3)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(42, 33, 24, 0.6)';
                        e.currentTarget.style.borderColor = 'rgba(127, 230, 239, 0.1)';
                      }}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3
                          className="text-sm font-bold leading-snug"
                          style={{ color: '#FFF8EE', fontFamily: 'var(--font-display)' }}
                        >
                          {zone.zone_name}
                        </h3>
                        <span
                          className="text-[9px] tracking-wider px-1.5 py-0.5 shrink-0 ml-2"
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
                        <p
                          className="text-xs mb-3 line-clamp-2"
                          style={{ color: '#FFF8EE', opacity: 0.5, fontFamily: 'var(--font-body)' }}
                        >
                          {zone.description}
                        </p>
                      )}
                      <div className="flex items-center gap-3 mt-auto">
                        <div className="flex items-center gap-1">
                          <Eye size={10} style={{ color: '#7FE6EF', opacity: 0.6 }} />
                          <span
                            className="text-[9px]"
                            style={{ color: '#7FE6EF', opacity: 0.7, fontFamily: 'var(--font-mono)' }}
                          >
                            {zone.view_count}
                          </span>
                        </div>
                        <span
                          className="text-[9px]"
                          style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-mono)' }}
                        >
                          区主: {zone.manager.username}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>

          {/* 热门帖子 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <Flame size={14} style={{ color: '#FF4D4D' }} />
              <span
                className="text-[10px] tracking-[0.3em] font-bold"
                style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}
              >
                热门话题
              </span>
              <div className="h-px flex-1 bg-[#FF4D4D]/15" />
            </div>

            {loadingPosts ? (
              <div className="flex items-center justify-center py-12">
                <motion.div
                  className="w-8 h-8 border-2 border-[#FF4D4D] border-t-transparent"
                  style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
              </div>
            ) : hotPosts.length === 0 ? (
              <div className="text-center py-12">
                <p style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-mono)' }}>
                  暂无话题
                </p>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  {hotPosts.map((post, index) => (
                    <motion.div
                      key={post.id}
                      className="cursor-pointer"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
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
                          <h3
                            className="text-sm sm:text-base font-medium leading-snug mb-1"
                            style={{ color: '#FFF8EE' }}
                          >
                            {post.title}
                          </h3>
                          <div className="flex items-center gap-3">
                            <span
                              className="text-[9px] tracking-wider"
                              style={{ color: '#FFF8EE', opacity: 0.4, fontFamily: 'var(--font-mono)' }}
                            >
                              BY {post.user.username}
                            </span>
                            <span className="flex items-center gap-1">
                              <Eye size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                              <span
                                className="text-[9px]"
                                style={{ color: '#7FE6EF', opacity: 0.6, fontFamily: 'var(--font-mono)' }}
                              >
                                {post.view_count}
                              </span>
                            </span>
                            <span className="flex items-center gap-1">
                              <MessageSquare size={10} style={{ color: '#7FE6EF', opacity: 0.5 }} />
                              <span
                                className="text-[9px]"
                                style={{ color: '#7FE6EF', opacity: 0.6, fontFamily: 'var(--font-mono)' }}
                              >
                                {post.reply_count}
                              </span>
                            </span>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>

                {hotTotal > POST_PAGE_SIZE && (
                  <motion.div
                    className="flex justify-center py-8"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    <Pagination
                      current={hotPage}
                      total={hotTotal}
                      pageSize={POST_PAGE_SIZE}
                      onChange={setHotPage}
                    />
                  </motion.div>
                )}
              </>
            )}
          </motion.div>

          {/* 底部装饰 */}
          <div className="py-8">
            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-[#7FE6EF]/10" />
              <span
                className="text-[9px] tracking-[0.3em] opacity-25"
                style={{ fontFamily: 'var(--font-mono)', color: '#7FE6EF' }}
              >
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
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          DE hub 论坛中心
        </span>
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          CH.02
        </span>
        <span
          className="text-[9px] tracking-wider"
          style={{ color: '#1A1612', fontFamily: 'var(--font-mono)' }}
        >
          实时互动
        </span>
      </footer>
    </div>
  );
}
