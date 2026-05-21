import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { listBlogPosts } from '../../api/blog';
import type { BlogPostListItem } from '../../api/types';
import ChamferCard from '../ui/ChamferCard';

export default function BlogPreview() {
  const navigate = useNavigate();
  const [hotPost, setHotPost] = useState<BlogPostListItem | null>(null);
  const [latestPosts, setLatestPosts] = useState<BlogPostListItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    try {
      // 获取最热1篇
      const hotRes = await listBlogPosts({ limit: 1, sort_by: 'hot' });
      const hot = hotRes.items[0] || null;
      setHotPost(hot);

      // 获取最新3篇，排除最热（避免重复）
      const latestRes = await listBlogPosts({ limit: 4, sort_by: 'latest' });
      const filteredLatest = hot
        ? latestRes.items.filter((p) => p.id !== hot.id).slice(0, 3)
        : latestRes.items.slice(0, 3);
      setLatestPosts(filteredLatest);
    } catch {
      // 静默处理，保持空状态
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  if (loading) {
    return (
      <section className="relative py-8 sm:py-10 px-4 sm:px-8 lg:px-14" id="blog">
        <div className="max-w-5xl mx-auto flex items-center justify-center py-16">
          <motion.div
            className="w-8 h-8 border-2 border-[#F5A623] border-t-transparent"
            style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
        </div>
      </section>
    );
  }

  if (!hotPost && latestPosts.length === 0) {
    return (
      <section className="relative py-8 sm:py-10 px-4 sm:px-8 lg:px-14" id="blog">
        <div className="max-w-5xl mx-auto text-center py-12">
          <p style={{ color: '#FFF8EE', opacity: 0.4, fontFamily: 'var(--font-body)' }}>
            暂无博客文章
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="relative py-8 sm:py-10 px-4 sm:px-8 lg:px-14" id="blog">
      {/* 顶部频道标识 */}
      <motion.div
        className="max-w-5xl mx-auto mb-8 flex items-center gap-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#FFE52C' }} />
        <span
          className="text-[10px] tracking-[0.3em] font-bold"
          style={{ color: '#FFE52C', fontFamily: 'var(--font-mono)' }}
        >
          DOCUMENTARY CHANNEL
        </span>
        <div className="h-px flex-1 bg-[#FFE52C]/15" />
        <button
          onClick={() => navigate('/blog')}
          className="text-[10px] tracking-wider font-bold px-2 py-1 transition-all duration-200 hover:bg-[#F5A623]/10"
          style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
          data-cursor-hover
        >
          VIEW ALL →
        </button>
      </motion.div>

      {/* 左右布局：左侧最热(大卡片) + 右侧最新(小卡片列表) */}
      <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* 左侧：最热文章（大卡片，占7列） */}
        {hotPost && (
          <div className="lg:col-span-7">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#FF4D4D' }} />
                <span
                  className="text-[10px] tracking-[0.3em] font-bold"
                  style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}
                >
                  TRENDING NOW
                </span>
                <div className="h-px flex-1 bg-[#FF4D4D]/15" />
              </div>

              <ChamferCard
                className="p-0 overflow-hidden cursor-pointer h-full"
                hoverable
                onClick={() => navigate(`/blog/${hotPost.slug}`)}
              >
                {/* 大图封面 */}
                <div
                  className="h-48 sm:h-56 relative overflow-hidden"
                  style={{ backgroundColor: 'rgba(255, 77, 77, 0.03)' }}
                >
                  {hotPost.cover_image_url ? (
                    <img
                      src={hotPost.cover_image_url}
                      alt={hotPost.title}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span
                        className="text-[10px] tracking-wider opacity-20"
                        style={{ fontFamily: 'var(--font-mono)', color: '#FF4D4D' }}
                      >
                        NO SIGNAL
                      </span>
                    </div>
                  )}
                  {/* HOT 标识 */}
                  <div className="absolute top-3 right-3">
                    <span
                      className="text-[10px] tracking-wider px-2 py-1 font-bold"
                      style={{
                        backgroundColor: 'rgba(255, 77, 77, 0.9)',
                        color: '#1A1612',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      HOT
                    </span>
                  </div>
                </div>

                {/* 内容 */}
                <div className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <span
                      className="text-[10px] tracking-wider"
                      style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE', opacity: 0.4 }}
                    >
                      {new Date(hotPost.created_at).toLocaleDateString('zh-CN')}
                    </span>
                    <span
                      className="text-[10px]"
                      style={{ fontFamily: 'var(--font-mono)', color: '#C4D70C', opacity: 0.5 }}
                    >
                      {hotPost.view_count} 阅读
                    </span>
                    <span
                      className="text-[10px]"
                      style={{ fontFamily: 'var(--font-mono)', color: '#7FE6EF', opacity: 0.5 }}
                    >
                      {hotPost.comment_count} 评论
                    </span>
                  </div>

                  <h3
                    className="text-lg font-black mb-2 leading-tight"
                    style={{ color: '#FFF8EE', fontFamily: 'var(--font-display)' }}
                  >
                    {hotPost.title}
                  </h3>

                  {hotPost.summary && (
                    <p
                      className="text-sm leading-relaxed line-clamp-2"
                      style={{ color: '#FFF8EE', opacity: 0.6 }}
                    >
                      {hotPost.summary}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-2 mt-3">
                    {hotPost.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[9px] tracking-wider px-1.5 py-0.5"
                        style={{
                          border: '1px solid rgba(247, 243, 232, 0.1)',
                          color: '#F7F3E8',
                          opacity: 0.5,
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </ChamferCard>
            </motion.div>
          </div>
        )}

        {/* 右侧：最新文章（小卡片，占5列） */}
        <div className={`${hotPost ? 'lg:col-span-5' : 'lg:col-span-12'}`}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#FFE52C' }} />
              <span
                className="text-[10px] tracking-[0.3em] font-bold"
                style={{ color: '#FFE52C', fontFamily: 'var(--font-mono)' }}
              >
                LATEST RELEASE
              </span>
              <div className="h-px flex-1 bg-[#FFE52C]/15" />
            </div>

            <div className="space-y-3">
              {latestPosts.map((post, index) => (
                <motion.div
                  key={post.id}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
                >
                  <ChamferCard
                    className="p-0 overflow-hidden cursor-pointer"
                    hoverable
                    onClick={() => navigate(`/blog/${post.slug}`)}
                  >
                    <div className="flex flex-row">
                      {/* 小图封面 */}
                      <div
                        className="w-20 h-20 shrink-0 relative overflow-hidden"
                        style={{ backgroundColor: 'rgba(255, 229, 44, 0.03)' }}
                      >
                        {post.cover_image_url ? (
                          <img
                            src={post.cover_image_url}
                            alt={post.title}
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <span
                              className="text-[9px] tracking-wider opacity-20"
                              style={{ fontFamily: 'var(--font-mono)', color: '#FFE52C' }}
                            >
                              NO SIGNAL
                            </span>
                          </div>
                        )}
                        {/* NEW 标识 */}
                        <div className="absolute top-1.5 right-1.5">
                          <span
                            className="text-[8px] tracking-wider px-1 py-0.5"
                            style={{
                              backgroundColor: 'rgba(255, 229, 44, 0.9)',
                              color: '#1A1612',
                              fontFamily: 'var(--font-mono)',
                            }}
                          >
                            NEW
                          </span>
                        </div>
                      </div>

                      {/* 内容 */}
                      <div className="flex-1 p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span
                            className="text-[9px] tracking-wider"
                            style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE', opacity: 0.4 }}
                          >
                            {new Date(post.created_at).toLocaleDateString('zh-CN')}
                          </span>
                        </div>

                        <h4
                          className="text-sm font-bold leading-snug line-clamp-2 mb-1"
                          style={{ color: '#FFF8EE', fontFamily: 'var(--font-body)' }}
                        >
                          {post.title}
                        </h4>

                        <div className="flex items-center gap-2">
                          <span
                            className="text-[9px]"
                            style={{ fontFamily: 'var(--font-mono)', color: '#C4D70C', opacity: 0.5 }}
                          >
                            {post.view_count} 阅读
                          </span>
                          <span
                            className="text-[9px]"
                            style={{ fontFamily: 'var(--font-mono)', color: '#7FE6EF', opacity: 0.5 }}
                          >
                            {post.comment_count} 评论
                          </span>
                        </div>
                      </div>
                    </div>
                  </ChamferCard>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
