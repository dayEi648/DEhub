import { useState } from 'react';
import { motion } from 'framer-motion';

export interface Channel {
  id: string;
  number: string;
  label: string;
  labelEn: string;
  color: string;
}

const channels: Channel[] = [
  { id: 'home', number: 'CH.00', label: '概览', labelEn: 'OVERVIEW', color: '#F5A623' },
  { id: 'blog', number: 'CH.01', label: '日志', labelEn: 'BLOG', color: '#FFE52C' },
  { id: 'forum', number: 'CH.02', label: '论坛', labelEn: 'FORUM', color: '#7FE6EF' },
  { id: 'ai', number: 'CH.03', label: 'AI', labelEn: 'AI CHAT', color: '#C4D70C' },
  { id: 'links', number: 'CH.04', label: '链接', labelEn: 'LINKS', color: '#FF4D4D' },
];

interface ChannelNavProps {
  activeId: string;
  onChange: (id: string) => void;
}

/**
 * 电视频道导航栏
 * P4风格：仿老式电视机顶部的频道切换栏
 */
export default function ChannelNav({ activeId, onChange }: ChannelNavProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="relative w-full">
      {/* 顶部彩条 */}
      <div className="h-1 w-full color-bars-flow opacity-80" />

      {/* 频道栏背景 */}
      <div
        className="flex items-center justify-center gap-1 sm:gap-2 px-2 py-2 sm:py-2.5"
        style={{ backgroundColor: 'rgba(10, 8, 6, 0.85)' }}
      >
        {channels.map((ch) => {
          const isActive = activeId === ch.id;
          const isHovered = hoveredId === ch.id;
          const isDimmed = hoveredId !== null && hoveredId !== ch.id && !isActive;

          return (
            <motion.button
              key={ch.id}
              className="relative flex flex-col items-center px-2 sm:px-4 py-1 sm:py-1.5 min-w-[56px] sm:min-w-[80px]"
              style={{
                backgroundColor: isActive ? ch.color : isHovered ? `${ch.color}15` : 'transparent',
                opacity: isDimmed ? 0.4 : 1,
              }}
              onClick={() => onChange(ch.id)}
              onMouseEnter={() => setHoveredId(ch.id)}
              onMouseLeave={() => setHoveredId(null)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              data-cursor-hover
            >
              {/* 频道编号 */}
              <span
                className="text-[9px] sm:text-[10px] tracking-wider font-bold"
                style={{
                  color: isActive ? '#1A1612' : ch.color,
                  fontFamily: 'var(--font-mono)',
                  lineHeight: 1,
                }}
              >
                {ch.number}
              </span>

              {/* 频道名称 */}
              <span
                className="text-[10px] sm:text-xs font-medium mt-0.5"
                style={{
                  color: isActive ? '#1A1612' : '#FFF8EE',
                  fontFamily: 'var(--font-body)',
                  lineHeight: 1.2,
                }}
              >
                {ch.label}
              </span>

              {/* 选中指示器：上下短线 */}
              {isActive && (
                <>
                  <motion.div
                    className="absolute top-0 left-1/4 right-1/4 h-0.5"
                    style={{ backgroundColor: ch.color }}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ duration: 0.2 }}
                  />
                  <motion.div
                    className="absolute bottom-0 left-1/4 right-1/4 h-0.5"
                    style={{ backgroundColor: '#1A1612' }}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ duration: 0.2 }}
                  />
                </>
              )}
            </motion.button>
          );
        })}
      </div>

      {/* 底部细线 */}
      <div className="h-px w-full bg-[#F5A623]/20" />
    </div>
  );
}

export { channels };
