import { useMemo } from 'react';
import { motion } from 'framer-motion';
import type { UserResponse } from '../../api/types';

interface UserHudProps {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  onNavigate: (path: string) => void;
  onLogout: () => void;
}

/* ============================================================
   用户 HUD —— 实体遥控器
   厚重塑料外壳 + 圆形实体按键 + 螺丝装饰 + 3D 厚度感。
   ============================================================ */

export default function UserHud({ user, isAuthenticated, isAdmin, onNavigate, onLogout }: UserHudProps) {
  const menuItems = useMemo(
    () => [
      { label: '空间', path: '/profile', color: '#F5A623' },
      ...(isAdmin ? [{ label: '后台', path: '/admin', color: '#FFE52C' }] : []),
      { label: '退出', path: null as string | null, color: '#FF4D4D' },
    ],
    [isAdmin]
  );

  return (
    <motion.div
      className="fixed top-4 right-4 sm:top-6 sm:right-6 z-[100] flex flex-col items-center"
      style={{ width: 128 }}
      initial={{ x: 100, opacity: 0, rotateZ: 5 }}
      animate={{ x: 0, opacity: 1, rotateZ: 1.5 }}
      transition={{ duration: 0.7, ease: [0.34, 1.56, 0.64, 1] }}
    >
      {/* ===== 遥控器外壳 ===== */}
      <div
        className="relative flex flex-col items-center w-full"
        style={{
          background: 'linear-gradient(160deg, #232018 0%, #1A1612 60%, #130f0c 100%)',
          border: '3px solid #3A3028',
          borderTopWidth: 2,
          borderLeftWidth: 2,
          borderRadius: '14px 14px 10px 10px',
          padding: '14px 10px 16px',
          boxShadow:
            'inset 1px 1px 0 rgba(255,255,255,0.06), inset -2px -2px 4px rgba(0,0,0,0.5), 6px 10px 0 #0a0806, 8px 12px 24px rgba(0,0,0,0.7)',
        }}
      >
        {/* 螺丝装饰 —— 四角 */}
        <Screw x={10} y={10} />
        <Screw x={110} y={10} />
        <Screw x={10} y={270} />
        <Screw x={110} y={270} />

        {/* ---- 屏幕区：头像 + 用户名 ---- */}
        <div
          className="relative flex flex-col items-center gap-2 mb-4 w-full"
          style={{
            backgroundColor: '#0d0b09',
            borderRadius: 8,
            border: '1.5px solid rgba(245, 166, 35, 0.15)',
            padding: '10px 0 8px',
            boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.7), 0 1px 0 rgba(255,255,255,0.03)',
          }}
        >
          {/* 屏幕反光 */}
          <div
            className="absolute inset-0 pointer-events-none rounded-lg"
            style={{
              background:
                'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, transparent 40%, transparent 70%, rgba(255,255,255,0.02) 100%)',
            }}
          />

          {/* 头像 */}
          <div
            className="relative w-14 h-14 rounded-full flex items-center justify-center overflow-hidden"
            style={{
              backgroundColor: '#1A1612',
              border: '2.5px solid #F5A623',
              boxShadow: '0 0 14px rgba(245,166,35,0.3), inset 0 0 10px rgba(0,0,0,0.6)',
            }}
          >
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="text-lg font-bold" style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}>
                {isAuthenticated ? user?.username?.charAt(0)?.toUpperCase() || '?' : '×'}
              </span>
            )}
          </div>

          {/* 用户名 */}
          <span
            className="text-[10px] font-bold truncate max-w-[90px]"
            style={{
              color: isAuthenticated ? '#F5A623' : 'rgba(247,243,232,0.25)',
              fontFamily: 'var(--font-mono)',
              letterSpacing: '0.1em',
            }}
          >
            {isAuthenticated ? user?.username || 'USER' : 'OFFLINE'}
          </span>
        </div>

        {/* ---- 条形实体按键区 ---- */}
        <div className="flex flex-col gap-2 items-center w-full px-1">
          {isAuthenticated ? (
            menuItems.map((item, i) => (
              <RemoteButton
                key={item.label}
                label={item.label}
                color={item.color}
                index={i}
                onClick={() => {
                  if (item.path) onNavigate(item.path);
                  else onLogout();
                }}
              />
            ))
          ) : (
            <RemoteButton label="进入系统" color="#F5A623" index={0} onClick={() => onNavigate('/login')} />
          )}
        </div>

        {/* 底部品牌刻字 */}
        <span
          className="mt-4 text-[7px] tracking-[0.3em] opacity-20"
          style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
        >
          DE-REMOTE
        </span>
      </div>
    </motion.div>
  );
}

/* ============================================================
   螺丝装饰
   ============================================================ */
function Screw({ x, y }: { x: number; y: number }) {
  return (
    <div
      className="absolute w-1.5 h-1.5 rounded-full"
      style={{
        left: x,
        top: y,
        backgroundColor: '#3A3028',
        boxShadow: 'inset 1px 1px 1px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.04)',
      }}
    />
  );
}

/* ============================================================
   条形实体按键 —— 3D 凸起/凹陷效果
   ============================================================ */

function RemoteButton({
  label,
  color,
  index,
  onClick,
}: {
  label: string;
  color: string;
  index: number;
  onClick: () => void;
}) {
  return (
    <motion.button
      className="relative w-full flex items-center gap-2.5 px-3 py-2.5 outline-none cursor-pointer overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, #232018 0%, #1A1612 100%)',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        borderBottom: '1px solid rgba(0,0,0,0.4)',
        borderRadius: 3,
        boxShadow:
          '0 3px 0 #0F0C09, 0 4px 6px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)',
      }}
      onClick={onClick}
      data-cursor-hover
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: 0.3 + index * 0.08,
        duration: 0.35,
        ease: [0.16, 1, 0.3, 1],
      }}
      whileHover={{
        background: `linear-gradient(180deg, ${color}22 0%, ${color}10 100%)`,
        borderTopColor: `${color}40`,
        y: 1,
        boxShadow: `0 2px 0 #0F0C09, 0 3px 8px ${color}25, inset 0 1px 0 ${color}20`,
        transition: { duration: 0.12 },
      }}
      whileTap={{
        y: 3,
        scale: 0.97,
        boxShadow: `0 0 0 #0F0C09, 0 1px 3px ${color}15, inset 0 2px 6px rgba(0,0,0,0.5)`,
        transition: { duration: 0.06 },
      }}
    >
      {/* 左侧菱形标识 */}
      <div
        className="shrink-0"
        style={{
          width: 7,
          height: 7,
          backgroundColor: color,
          clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
          boxShadow: `0 0 6px ${color}40`,
        }}
      />

      {/* 文字 */}
      <span
        className="relative z-10 text-[10px] font-bold tracking-wider"
        style={{ color: '#FFF8EE', fontFamily: 'var(--font-mono)' }}
      >
        {label}
      </span>

      {/* 右侧指示竖线 */}
      <div
        className="absolute right-2 top-1/2 -translate-y-1/2 w-[2px] h-3"
        style={{ backgroundColor: color, opacity: 0.6 }}
      />
    </motion.button>
  );
}
