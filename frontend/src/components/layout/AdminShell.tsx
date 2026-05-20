import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useLogout } from '../../hooks/useLogout';
import type { ReactNode } from 'react';

type AdminPage = 'users' | 'forum-zones' | 'logs';

interface Beacon {
  id: AdminPage;
  label: string;
  labelEn: string;
  path: string;
  icon: string;
  position: { top?: string; left?: string; right?: string; bottom?: string };
  curveFrom: { x: number; y: number };
}

const beacons: Beacon[] = [
  { id: 'users', label: '用户管理', labelEn: 'USERS', path: '/admin/users', icon: '👤', position: { top: '20%', left: '5%' }, curveFrom: { x: 5, y: 22 } },
  { id: 'forum-zones', label: '论坛分区', labelEn: 'FORUM', path: '/admin/forum-zones', icon: '🌐', position: { top: '20%', right: '5%' }, curveFrom: { x: 95, y: 22 } },
  { id: 'logs', label: '系统日志', labelEn: 'LOGS', path: '/admin/logs', icon: '📋', position: { bottom: '15%', left: '50%' }, curveFrom: { x: 50, y: 85 } },
];

const CENTER = { x: 50, y: 52 };

/* ============================================================
   条纹擦除转场 — 条纹从中心爆开，闪过之后内容显现
   ============================================================ */
function StripeWipe({ children, pageKey }: { children: ReactNode; pageKey: string }) {
  return (
    <AnimatePresence mode="wait">
      <motion.div key={pageKey} className="relative w-full">
        {/* 条纹遮罩层 — 扩展后迅速淡出，绝不遮挡内容 */}
        <motion.div
          className="absolute inset-0 z-20 pointer-events-none overflow-hidden"
          initial={{ clipPath: 'circle(0% at 50% 50%)', opacity: 1 }}
          animate={{ clipPath: 'circle(150% at 50% 50%)', opacity: [1, 1, 0] }}
          exit={{ clipPath: 'circle(0% at 50% 50%)', opacity: 1 }}
          transition={{ duration: 0.6, times: [0, 0.5, 1], ease: [0.87, 0, 0.13, 1] }}
        >
          <div
            className="absolute inset-0"
            style={{
              background: `repeating-linear-gradient(
                60deg,
                #FF4D4D 0px, #FF4D4D 20px,
                #FFE52C 20px, #FFE52C 40px,
                #C4D70C 40px, #C4D70C 60px,
                #7FE6EF 60px, #7FE6EF 80px,
                #1A1612 80px, #1A1612 100px
              )`,
            }}
          />
        </motion.div>
        {/* 实际内容 — 始终在最上层 */}
        <motion.div
          className="relative z-30"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.96 }}
          transition={{ duration: 0.35, delay: 0.15 }}
        >
          {children}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

/* ============================================================
   AdminShell
   ============================================================ */
export default function AdminShell({ activePage, children }: { activePage: AdminPage; children: ReactNode }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { handleLogout } = useLogout();
  const [hoveredBeacon, setHoveredBeacon] = useState<AdminPage | null>(null);

  return (
    <div className="min-h-[100dvh] relative" style={{ backgroundColor: '#0a0806' }}>
      {/* 右上角弱金色光斑 */}
      <motion.div
        className="absolute top-0 right-0 pointer-events-none"
        style={{
          width: '50vw',
          height: '50vh',
          background: 'radial-gradient(ellipse 60% 50% at 85% 15%, rgba(245,166,35,0.08) 0%, transparent 70%)',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6 }}
      />

      {/* ===== 顶部 HUD ===== */}
      <motion.header
        className="relative z-30 flex items-center justify-between px-4 sm:px-6 py-4"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <button
          className="text-[10px] font-bold tracking-widest flex items-center gap-1"
          style={{ color: '#F5A623', fontFamily: 'var(--font-mono)' }}
          onClick={() => navigate('/')}
          data-cursor-hover
        >
          <span>←</span> BACK
        </button>

        <div className="flex items-center gap-3">
          <span className="text-[10px] hidden md:inline" style={{ color: 'rgba(255,248,238,0.35)', fontFamily: 'var(--font-mono)' }}>
            {user?.username}
          </span>
          <motion.button
            className="text-[9px] font-bold tracking-widest px-3 py-1.5"
            style={{
              color: '#FF4D4D',
              border: '1px solid rgba(255, 77, 77, 0.25)',
              fontFamily: 'var(--font-display)',
              clipPath: 'polygon(4px 0%, 100% 0%, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0% 100%, 0% 4px)',
            }}
            whileHover={{ backgroundColor: 'rgba(194, 35, 3, 0.12)', borderColor: 'rgba(255, 77, 77, 0.5)' }}
            whileTap={{ scale: 0.92 }}
            onClick={handleLogout}
            data-cursor-hover
          >
            EXIT
          </motion.button>
        </div>
      </motion.header>

      {/* ===== 中央金色操作台 ===== */}
      <div className="relative z-20 flex items-center justify-center px-4 pb-8" style={{ minHeight: 'calc(100dvh - 64px)' }}>
        <motion.div
          className="relative w-full max-w-5xl"
          initial={{ scale: 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.25, duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }}
        >
          <div
            className="relative w-full"
            style={{
              backgroundColor: '#F5A623',
              clipPath: 'polygon(24px 0%, 100% 0%, 100% calc(100% - 24px), calc(100% - 24px) 100%, 0% 100%, 0% 24px)',
            }}
          >
            <div
              className="relative w-full p-6 sm:p-8 lg:p-10 overflow-y-auto"
              style={{ minHeight: '60vh', maxHeight: 'calc(100dvh - 80px)' }}
            >
              <div className="absolute top-0 left-6 right-6 h-1" style={{ background: 'linear-gradient(90deg, transparent, #1A1612, transparent)', opacity: 0.2 }} />
              <div className="relative z-10">
                <StripeWipe pageKey={activePage}>
                  {children}
                </StripeWipe>
              </div>
            </div>
          </div>

          <div
            className="absolute inset-0 hidden sm:block -z-10"
            style={{
              backgroundColor: '#2A2118',
              clipPath: 'polygon(24px 0%, 100% 0%, 100% calc(100% - 24px), calc(100% - 24px) 100%, 0% 100%, 0% 24px)',
              transform: 'translate(10px, 10px)',
              opacity: 0.5,
            }}
          />
        </motion.div>
      </div>

      {/* ===== 全屏光路层 ===== */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-10" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <filter id="glow-path">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {beacons.map((beacon) => {
          const isActive = activePage === beacon.id;
          const isHovered = hoveredBeacon === beacon.id;
          const from = beacon.curveFrom;
          const to = CENTER;
          const midX = (from.x + to.x) / 2;
          const midY = (from.y + to.y) / 2;
          const cx = midX + (to.y - from.y) * 0.12;
          const cy = midY - (to.x - from.x) * 0.12;
          const d = `M ${from.x} ${from.y} Q ${cx} ${cy} ${to.x} ${to.y}`;
          return (
            <motion.path
              key={beacon.id}
              d={d}
              fill="none"
              stroke={isActive ? '#FFE52C' : isHovered ? '#F5A623' : '#F5A623'}
              strokeWidth={isActive ? 3 : isHovered ? 2 : 1}
              filter={isActive || isHovered ? 'url(#glow-path)' : undefined}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: isActive || isHovered ? 0.85 : 0.15 }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              vectorEffect="non-scaling-stroke"
            />
          );
        })}
      </svg>

      {/* ===== 信号灯塔 ===== */}
      {beacons.map((beacon, i) => {
        const isActive = activePage === beacon.id;
        const pos = beacon.position;

        return (
          <motion.div
            key={beacon.id}
            className="absolute z-20"
            style={{
              top: pos.top,
              left: pos.left,
              right: pos.right,
              bottom: pos.bottom,
              transform: pos.left === '50%' ? 'translateX(-50%)' : undefined,
            }}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 + i * 0.15, duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
          >
            <motion.button
              className="relative flex flex-col items-center gap-1.5 px-4 py-2.5 sm:px-5 sm:py-3"
              style={{
                backgroundColor: isActive ? '#F5A623' : 'rgba(26, 22, 18, 0.9)',
                border: isActive ? '2px solid #FFE52C' : '1px solid rgba(245, 166, 35, 0.3)',
                clipPath: 'polygon(10px 0%, 100% 0%, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0% 100%, 0% 10px)',
              }}
              onClick={() => navigate(beacon.path)}
              onMouseEnter={() => setHoveredBeacon(beacon.id)}
              onMouseLeave={() => setHoveredBeacon(null)}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
              data-cursor-hover
            >
              {isActive && (
                <motion.div
                  className="absolute -top-1 -right-1 w-3 h-3"
                  style={{ backgroundColor: '#FFE52C', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 400 }}
                />
              )}
              <span className="text-lg sm:text-xl">{beacon.icon}</span>
              <span
                className="text-[9px] font-bold tracking-wider"
                style={{
                  color: isActive ? '#1A1612' : '#F5A623',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {beacon.labelEn}
              </span>
              <span className="text-[10px] hidden sm:inline" style={{ color: isActive ? 'rgba(26,22,18,0.7)' : 'rgba(255,248,238,0.5)' }}>
                {beacon.label}
              </span>
            </motion.button>
          </motion.div>
        );
      })}
    </div>
  );
}
