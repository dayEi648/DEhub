import { motion } from 'framer-motion';
import type { CommentResponse } from '../../api/types';

interface NoteCardProps {
  comment: CommentResponse;
  onLike?: () => void;
  onDelete?: () => void;
  index?: number;
}

/**
 * 便签卡片（评论）
 * 像贴在文件夹上的便签
 */
export default function NoteCard({ comment, onLike, onDelete, index = 0 }: NoteCardProps) {
  return (
    <motion.div
      className="relative p-4"
      style={{
        backgroundColor: 'rgba(42, 33, 24, 0.8)',
        borderLeft: '2px solid #F5A623',
        clipPath: 'polygon(6px 0%, 100% 0%, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0% 100%, 0% 6px)',
      }}
      initial={{ opacity: 0, y: -20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.5,
        delay: index * 0.05,
        ease: [0.34, 1.56, 0.64, 1],
      }}
    >
      <div className="flex items-start gap-3">
        {/* 头像（印章效果） */}
        <div
          className="w-8 h-8 shrink-0 flex items-center justify-center text-[10px] font-bold rounded-full"
          style={{
            backgroundColor: '#1A1612',
            color: '#F5A623',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {comment.user.username.charAt(0).toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className="text-xs font-bold"
              style={{ color: '#F5A623', fontFamily: 'var(--font-body)' }}
            >
              {comment.user.username}
            </span>
            <span
              className="text-[9px]"
              style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE', opacity: 0.3 }}
            >
              {new Date(comment.created_at).toLocaleDateString('zh-CN')}
            </span>
          </div>

          <p
            className="text-sm leading-relaxed mb-2"
            style={{ color: '#FFF8EE', opacity: 0.85, fontFamily: 'var(--font-body)' }}
          >
            {comment.content}
          </p>

          <div className="flex items-center gap-3">
            <button
              onClick={onLike}
              className="text-[9px] tracking-wider flex items-center gap-1 transition-all duration-200"
              style={{
                color: comment.is_liked ? '#F5A623' : 'rgba(247, 243, 232, 0.4)',
                fontFamily: 'var(--font-mono)',
              }}
              data-cursor-hover
            >
              {comment.is_liked ? '★' : '☆'} {comment.likecount}
            </button>

            {onDelete && (
              <button
                onClick={onDelete}
                className="text-[9px] tracking-wider transition-all duration-200 hover:text-[#FF4D4D]"
                style={{
                  color: 'rgba(247, 243, 232, 0.3)',
                  fontFamily: 'var(--font-mono)',
                }}
                data-cursor-hover
              >
                删除
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
