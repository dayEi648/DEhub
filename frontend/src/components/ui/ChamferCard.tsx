import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface ChamferCardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

/**
 * 斜切角卡片
 * P4风格：拒绝圆角，使用锐角或小斜切角（Chamfer），像被精确裁剪的色纸
 */
export default function ChamferCard({
  children,
  className = '',
  hoverable = true,
  onClick,
  style,
}: ChamferCardProps) {
  return (
    <motion.div
      className={`chamfer relative bg-[#2A2118]/80 backdrop-blur-sm ${className}`}
      style={{
        border: '1px solid rgba(245, 166, 35, 0.15)',
        ...style,
      }}
      whileHover={
        hoverable
          ? {
              scale: 1.02,
              backgroundColor: 'rgba(42, 33, 24, 0.95)',
              borderColor: 'rgba(245, 166, 35, 0.5)',
            }
          : undefined
      }
      whileTap={hoverable ? { scale: 0.98 } : undefined}
      transition={{ type: 'spring', damping: 20, stiffness: 300 }}
      onClick={onClick}
      data-cursor-hover={hoverable ? true : undefined}
    >
      {/* 内层高光描边 */}
      <div
        className="absolute inset-0 chamfer pointer-events-none"
        style={{
          border: '1px solid rgba(247, 243, 232, 0.06)',
          margin: 2,
        }}
      />
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}
