import { motion } from 'framer-motion';
import type { BlogPostDetailResponse } from '../../api/types';

interface FileHeaderProps {
  post: BlogPostDetailResponse;
  fileNumber: string;
  isFavorited: boolean;
  onFavorite: () => void;
}

/**
 * 文件夹头部（详情页）
 * 金色背景，像打开的文件夹封面
 */
export default function FileHeader({
  post,
  fileNumber,
  isFavorited,
  onFavorite,
}: FileHeaderProps) {
  return (
    <motion.div
      className="relative mb-6"
      style={{
        backgroundColor: '#F5A623',
        clipPath: 'polygon(0 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0% 100%)',
      }}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="p-6 sm:p-8">
        {/* 顶部行：分类 + 文件编号 + 分类名称 */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <span
            className="text-[10px] tracking-wider px-2 py-1 font-bold"
            style={{
              backgroundColor: '#1A1612',
              color: '#FFE52C',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {post.category.name}
          </span>
          <span
            className="text-[10px] tracking-wider"
            style={{ fontFamily: 'var(--font-mono)', color: '#1A1612', opacity: 0.7 }}
          >
            {fileNumber}
          </span>
          <span
            className="text-[9px] tracking-wider"
            style={{ fontFamily: 'var(--font-mono)', color: '#1A1612', opacity: 0.5 }}
          >
            {post.category.name}档案
          </span>
          
          {/* 档案柜标签装饰 */}
          <div className="ml-auto">
            <span
              className="text-[8px] tracking-wider px-1.5 py-0.5"
              style={{
                backgroundColor: '#1A1612',
                color: '#F5A623',
                fontFamily: 'var(--font-mono)',
              }}
            >
              原创
            </span>
          </div>
        </div>

        {/* 标题 */}
        <h1
          className="text-2xl sm:text-3xl font-black leading-tight mb-4"
          style={{ color: '#1A1612', fontFamily: 'var(--font-display)' }}
        >
          {post.title}
        </h1>

        {/* 作者 + 元信息行 */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {/* 作者头像+用户名 */}
          <div className="flex items-center gap-2 mr-2">
            <div
              className="w-6 h-6 rounded-full overflow-hidden flex items-center justify-center text-[9px] font-bold"
              style={{
                backgroundColor: '#1A1612',
                color: '#F5A623',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {post.author.avatar_url ? (
                <img
                  src={post.author.avatar_url}
                  alt={post.author.username}
                  className="w-full h-full object-cover"
                />
              ) : (
                post.author.username.charAt(0).toUpperCase()
              )}
            </div>
            <span
              className="text-[10px] font-bold"
              style={{ fontFamily: 'var(--font-body)', color: '#1A1612', opacity: 0.85 }}
            >
              {post.author.username}
            </span>
          </div>

          <span
            className="text-[10px] tracking-wider"
            style={{ fontFamily: 'var(--font-mono)', color: '#1A1612', opacity: 0.7 }}
          >
            {new Date(post.created_at).toLocaleDateString('zh-CN')}
          </span>
          <span
            className="text-[10px]"
            style={{ fontFamily: 'var(--font-mono)', color: '#1A1612', opacity: 0.6 }}
          >
            {post.view_count} 阅读
          </span>
          <span
            className="text-[10px]"
            style={{ fontFamily: 'var(--font-mono)', color: '#1A1612', opacity: 0.6 }}
          >
            {post.comment_count} 评论
          </span>
        </div>

        {/* 标签行 + 收藏按钮 */}
        <div className="flex flex-wrap items-center gap-2">
          {post.tags.map((tag) => (
            <span
              key={tag}
              className="text-[9px] tracking-wider px-1.5 py-0.5"
              style={{
                backgroundColor: '#1A1612',
                color: '#FFE52C',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {tag}
            </span>
          ))}
          <motion.button
            onClick={onFavorite}
            className="ml-auto px-3 py-1.5 text-[10px] font-bold tracking-wider flex items-center gap-1"
            style={{
              backgroundColor: isFavorited ? '#1A1612' : 'transparent',
              color: isFavorited ? '#FFE52C' : '#1A1612',
              fontFamily: 'var(--font-mono)',
              border: '1px solid rgba(26, 22, 18, 0.3)',
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            data-cursor-hover
          >
            {isFavorited ? '★ 已归档' : '☆ 标记'}
          </motion.button>
        </div>
      </div>

      {/* 折痕效果 */}
      <div className="absolute bottom-0 left-0 right-0 h-px" style={{ backgroundColor: '#1A1612', opacity: 0.2 }} />
    </motion.div>
  );
}
