import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, Eye, Flame, ArrowRight } from 'lucide-react';
import { listForumPosts } from '../../api/forum';
import type { ForumPostResponse } from '../../api/types';

export default function ForumPreview() {
  const navigate = useNavigate();
  const [posts, setPosts] = useState<ForumPostResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listForumPosts({ sort_by: 'view', skip: 0, limit: 5 });
      setPosts(res.items);
    } catch {
      // 静默处理
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  return (
    <section className="relative py-8 sm:py-10 px-4 sm:px-8 lg:px-14" id="forum">
      <div className="max-w-5xl mx-auto">
        {/* 顶部频道标识 */}
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
          <button
            onClick={() => navigate('/forum')}
            className="flex items-center gap-1 text-[10px] font-bold tracking-wider transition-colors hover:text-[#7FE6EF]"
            style={{ color: 'rgba(247, 243, 232, 0.4)', fontFamily: 'var(--font-mono)' }}
            data-cursor-hover
          >
            进入论坛
            <ArrowRight size={12} />
          </button>
        </motion.div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <motion.div
              className="w-8 h-8 border-2 border-[#7FE6EF] border-t-transparent"
              style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            />
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-12">
            <p style={{ color: '#FFF8EE', opacity: 0.3, fontFamily: 'var(--font-mono)' }}>
              暂无热门话题
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {posts.map((post, index) => (
              <motion.div
                key={post.id}
                className="relative cursor-pointer"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                onClick={() => navigate(`/forum/posts/${post.id}`)}
                data-cursor-hover
              >
                <div
                  className="flex items-start gap-3 sm:gap-4 p-4 sm:p-5 chamfer transition-all duration-200"
                  style={{
                    backgroundColor: index === 0 ? 'rgba(127, 230, 239, 0.04)' : 'rgba(42, 33, 24, 0.6)',
                    border: index === 0
                      ? '1px solid rgba(127, 230, 239, 0.2)'
                      : '1px solid rgba(247, 243, 232, 0.06)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(127, 230, 239, 0.08)';
                    e.currentTarget.style.borderColor = 'rgba(127, 230, 239, 0.3)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = index === 0 ? 'rgba(127, 230, 239, 0.04)' : 'rgba(42, 33, 24, 0.6)';
                    e.currentTarget.style.borderColor = index === 0
                      ? '1px solid rgba(127, 230, 239, 0.2)'
                      : '1px solid rgba(247, 243, 232, 0.06)';
                  }}
                >
                  <div className="flex flex-col items-center gap-1 shrink-0">
                    <div
                      className="w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center text-xs font-bold"
                      style={{
                        backgroundColor: index === 0 ? 'rgba(127, 230, 239, 0.15)' : 'rgba(247, 243, 232, 0.05)',
                        color: index === 0 ? '#7FE6EF' : '#FFF8EE',
                        fontFamily: 'var(--font-mono)',
                        clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                      }}
                    >
                      {post.user.username.slice(0, 2).toUpperCase()}
                    </div>
                    {index === 0 && (
                      <Flame size={12} style={{ color: '#FF4D4D' }} />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3
                      className="text-sm sm:text-base font-medium leading-snug mb-1"
                      style={{ color: '#FFF8EE' }}
                    >
                      {post.title}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-[9px] tracking-wider px-1.5 py-0.5"
                        style={{
                          backgroundColor: 'rgba(127, 230, 239, 0.08)',
                          color: '#7FE6EF',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        #{post.zone_id}
                      </span>
                      <span
                        className="text-[9px] tracking-wider opacity-40"
                        style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE' }}
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
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <MessageSquare size={12} style={{ color: '#7FE6EF', opacity: 0.6 }} />
                    <span
                      className="text-xs font-bold"
                      style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}
                    >
                      {post.reply_count}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
