import { motion } from 'framer-motion';
import type { CommentResponse } from '../../api/types';

interface NoteCardProps {
  comment: CommentResponse;
  onLike?: () => void;
  onDelete?: () => void;
  onReply?: () => void;
  index?: number;
  showReplyButton?: boolean;
  isReply?: boolean;
}

/**
 * 便签卡片（评论）
 * 像贴在文件夹上的便签
 */
export default function NoteCard({
  comment,
  onLike,
  onDelete,
  onReply,
  index = 0,
  showReplyButton = false,
  isReply = false,
}: NoteCardProps) {
  // 解析内容中的 @用户名：前缀
  const atPrefixMatch = comment.content.match(/^@([^：:]+)[：:]\s*/);
  const atPrefix = atPrefixMatch ? atPrefixMatch[0] : '';
  const displayContent = atPrefixMatch
    ? comment.content.slice(atPrefix.length)
    : comment.content;

  return (
    <motion.div
      className="relative p-4"
      style={{
        backgroundColor: 'rgba(42, 33, 24, 0.8)',
        borderLeft: `2px solid ${isReply ? '#C4D70C' : '#F5A623'}`,
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
        {/* 头像 */}
        <div
          className="w-8 h-8 shrink-0 flex items-center justify-center text-[10px] font-bold rounded-full overflow-hidden"
          style={{
            backgroundColor: '#1A1612',
            color: isReply ? '#C4D70C' : '#F5A623',
            fontFamily: 'var(--font-mono)',
          }}
        >
          {comment.user.avatar_url ? (
            <img
              src={comment.user.avatar_url}
              alt={comment.user.username}
              className="w-full h-full object-cover"
            />
          ) : (
            comment.user.username.charAt(0).toUpperCase()
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className="text-xs font-bold"
              style={{ color: isReply ? '#C4D70C' : '#F5A623', fontFamily: 'var(--font-body)' }}
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
            {atPrefix && (
              <span style={{ color: '#C4D70C', opacity: 0.9 }}>{atPrefix}</span>
            )}
            {displayContent}
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

            {showReplyButton && onReply && (
              <button
                onClick={onReply}
                className="text-[9px] tracking-wider transition-all duration-200 hover:text-[#F5A623]"
                style={{
                  color: 'rgba(247, 243, 232, 0.4)',
                  fontFamily: 'var(--font-mono)',
                }}
                data-cursor-hover
              >
                回复
              </button>
            )}

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
