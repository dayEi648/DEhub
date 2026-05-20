import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import type { BlogPostListItem } from '../../api/types';

interface FolderCardProps {
  post: BlogPostListItem;
  index: number;
}

/**
 * 文件夹卡片
 * 档案柜风格的博客文章卡片，像真实的文件夹标签
 */
export default function FolderCard({ post, index }: FolderCardProps) {
  const navigate = useNavigate();
  const fileNumber = `FL-${String(index + 1).padStart(3, '0')}`;

  return (
    <motion.div
      className="relative cursor-pointer overflow-hidden"
      style={{
        width: 280,
        height: 200,
        backgroundColor: 'rgba(26, 22, 18, 0.9)',
        border: '1px solid rgba(245, 166, 35, 0.2)',
        clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.05 }}
      whileHover={{
        x: 12,
        scale: 1.02,
        backgroundColor: '#F5A623',
        boxShadow: '0 8px 24px rgba(245, 166, 35, 0.2)',
      }}
      onClick={() => navigate(`/blog/${post.slug}`)}
      data-cursor-hover
    >
      {/* 内层高光描边 */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          clipPath: 'polygon(8px 0%, 100% 0%, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%, 0% 8px)',
          border: '1px solid rgba(247, 243, 232, 0.06)',
          margin: 2,
        }}
      />

      <div className="relative z-10 flex flex-col h-full">
        {/* 顶部 60%: 封面图区域 */}
        <div
          className="relative overflow-hidden flex-shrink-0"
          style={{ height: '60%' }}
        >
          {post.cover_image_url ? (
            <motion.img
              src={post.cover_image_url}
              alt={post.title}
              className="w-full h-full object-cover"
              loading="lazy"
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
              style={{
                border: '1px solid rgba(245, 166, 35, 0.3)',
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span
                className="text-[9px] tracking-wider"
                style={{ fontFamily: 'var(--font-mono)', color: '#F5A623', opacity: 0.3 }}
              >
                NO SIGNAL
              </span>
            </div>
          )}
          
          {/* 分类标签 */}
          <div className="absolute top-2 left-2">
            <span
              className="text-[8px] tracking-wider px-1.5 py-0.5 font-bold"
              style={{
                backgroundColor: 'rgba(245, 166, 35, 0.85)',
                color: '#1A1612',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {post.category.name}
            </span>
          </div>
        </div>

        {/* 底部 40%: 信息区域 */}
        <div className="flex-1 p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span
                className="text-[9px] tracking-wider"
                style={{ fontFamily: 'var(--font-mono)', color: '#F5A623', opacity: 0.6 }}
              >
                {fileNumber}
              </span>
              <span
                className="text-[8px]"
                style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE', opacity: 0.4 }}
              >
                {new Date(post.created_at).toLocaleDateString('zh-CN')}
              </span>
            </div>
            <h3
              className="text-sm font-bold leading-snug line-clamp-2"
              style={{ color: '#FFF8EE', fontFamily: 'var(--font-body)' }}
            >
              {post.title}
            </h3>
          </div>
          
          <div className="flex items-center justify-between">
            <span
              className="text-[8px]"
              style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE', opacity: 0.4 }}
            >
              {post.view_count} 阅读
            </span>
            <div className="flex gap-1">
              {post.tags.slice(0, 2).map((tag) => (
                <span
                  key={tag}
                  className="text-[7px] tracking-wider px-1 py-0.5"
                  style={{
                    border: '1px solid rgba(245, 166, 35, 0.15)',
                    color: '#F5A623',
                    opacity: 0.5,
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Hover 时的彩色条纹 */}
      <motion.div
        className="absolute bottom-0 left-0 right-0 flex"
        initial={{ scaleX: 0 }}
        whileHover={{ scaleX: 1 }}
        transition={{ duration: 0.2 }}
        style={{ originX: 0 }}
      >
        <div className="flex-1 h-0.5" style={{ backgroundColor: '#FFE52C' }} />
        <div className="flex-1 h-0.5" style={{ backgroundColor: '#7FE6EF' }} />
        <div className="flex-1 h-0.5" style={{ backgroundColor: '#C4D70C' }} />
      </motion.div>
    </motion.div>
  );
}
