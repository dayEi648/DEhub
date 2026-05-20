import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import ChannelNav, { channels } from './ChannelNav';
import ChannelSwitchEffect from '../effects/ChannelSwitchEffect';
import type { ReactNode } from 'react';

interface TVFrameProps {
  children: ReactNode;
  activeChannel: string;
  onChannelChange: (id: string) => void;
}

function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const glowColors: Record<string, string> = Object.fromEntries(
  channels.map((c) => [c.id, hexToRgba(c.color, 0.30)])
);

const glowCoreColors: Record<string, string> = Object.fromEntries(
  channels.map((c) => [c.id, hexToRgba(c.color, 0.12)])
);

export default function TVFrame({ children, activeChannel, onChannelChange }: TVFrameProps) {
  const screenRef = useRef<HTMLDivElement>(null);
  const switchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [time, setTime] = useState('');
  const [switchKey, setSwitchKey] = useState(0);
  const [isSwitching, setIsSwitching] = useState(false);

  useEffect(() => {
    return () => {
      if (switchTimeoutRef.current) {
        clearTimeout(switchTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      setTime(`${h}:${m}`);
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const handleChannelChange = (id: string) => {
    if (id === activeChannel || isSwitching) return;
    setIsSwitching(true);
    setSwitchKey((k) => k + 1);
    onChannelChange(id);
    if (screenRef.current) screenRef.current.scrollTop = 0;
    if (switchTimeoutRef.current) clearTimeout(switchTimeoutRef.current);
    switchTimeoutRef.current = setTimeout(() => {
      setIsSwitching(false);
      switchTimeoutRef.current = null;
    }, 900);
  };

  const activeCh = channels.find((c) => c.id === activeChannel);
  const glowColor = glowColors[activeChannel] || glowColors.home;
  const glowCore = glowCoreColors[activeChannel] || glowCoreColors.home;

  return (
    <div className="relative z-[1] h-[100dvh] overflow-hidden flex flex-col items-center pt-3 sm:pt-4 pb-10 sm:pb-12 px-2 sm:px-4">
      {/* ========== 环境光晕：从页面中央向四周扩散，电视机边缘会透出颜色 ========== */}
      <motion.div
        className="fixed inset-0 pointer-events-none z-0"
        animate={{ background: `radial-gradient(ellipse 95% 80% at 50% 45%, ${glowCore} 0%, transparent 50%)` }}
        transition={{ duration: 0.8, ease: 'easeInOut' }}
      />

      {/* ========== 电视天线 ========== */}
      <div className="relative w-full max-w-6xl flex justify-center mb-1 z-10">
        <div className="relative w-32 h-10">
          <div className="absolute left-1/2 bottom-0 w-0.5 h-6 -translate-x-1/2" style={{ backgroundColor: '#3A3028' }} />
          <motion.div
            className="absolute left-1/2 bottom-5 w-20 h-0.5 origin-left"
            style={{ backgroundColor: '#3A3028' }}
            animate={{ rotate: [-25, -20, -25] }}
            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            className="absolute left-1/2 bottom-5 w-20 h-0.5 origin-right"
            style={{ backgroundColor: '#3A3028' }}
            animate={{ rotate: [25, 20, 25] }}
            transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
          />
          <div className="absolute top-0 left-3 w-2 h-2 rounded-full" style={{ backgroundColor: '#F5A623', opacity: 0.6 }} />
          <div className="absolute top-0 right-3 w-2 h-2 rounded-full" style={{ backgroundColor: '#F5A623', opacity: 0.6 }} />
        </div>
      </div>

      {/* ========== 电视机外壳 ========== */}
      <div
        className="relative w-full max-w-6xl flex-1 flex flex-col z-10"
        style={{
          backgroundColor: '#1A1612',
          border: '4px solid #2A2118',
          boxShadow: 'inset 0 0 60px rgba(0,0,0,0.6), 0 0 0 2px #3A3028, 0 0 0 6px #1A1612, 0 0 0 8px #2A2118, 0 12px 40px rgba(0,0,0,0.7)',
          borderRadius: '4px 4px 12px 12px',
        }}
      >
        {/* 品牌标识 */}
        <div
          className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-0.5"
          style={{
            backgroundColor: '#2A2118',
            border: '1px solid rgba(245, 166, 35, 0.3)',
            boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 2px 8px rgba(0,0,0,0.4)',
          }}
        >
          <span
            className="text-[9px] tracking-[0.4em] font-bold"
            style={{ color: '#F5A623', fontFamily: 'var(--font-mono)', textShadow: '0 0 4px rgba(245, 166, 35, 0.3)' }}
          >
            DE-TV
          </span>
        </div>

        <ChannelNav activeId={activeChannel} onChange={handleChannelChange} />

        {/* 当前频道信息条 */}
        <div className="flex items-center justify-between px-3 py-1" style={{ backgroundColor: 'rgba(10, 8, 6, 0.6)' }}>
          <div className="flex items-center gap-2">
            <span className="text-[9px] tracking-wider opacity-50" style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE' }}>
              NOW PLAYING
            </span>
            <div className="w-1 h-1 rotate-45" style={{ backgroundColor: activeCh?.color || '#F5A623' }} />
            <span className="text-[10px] font-bold tracking-wider" style={{ color: activeCh?.color || '#F5A623', fontFamily: 'var(--font-mono)' }}>
              {activeCh?.number} {activeCh?.labelEn}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="w-1" style={{ height: 3 + i * 2, backgroundColor: i <= 4 ? '#C4D70C' : 'rgba(247, 243, 232, 0.15)' }} />
            ))}
          </div>
        </div>

        {/* 屏幕区域 */}
        <div
          ref={screenRef}
          className="relative flex-1 overflow-y-auto overflow-x-hidden"
          style={{ backgroundColor: '#0a0806', boxShadow: 'inset 0 0 40px rgba(0,0,0,0.8)', borderRadius: '2px 2px 0 0' }}
        >
          <ChannelSwitchEffect trigger={switchKey} channelNumber={activeCh?.number} channelColor={activeCh?.color} />

          <div
            className="absolute inset-0 pointer-events-none z-40"
            style={{
              background: 'linear-gradient(135deg, rgba(255,255,255,0.02) 0%, transparent 40%, transparent 60%, rgba(255,255,255,0.01) 100%)',
              borderRadius: 'inherit',
            }}
          />

          <div
            className="absolute inset-0 pointer-events-none z-40"
            style={{ boxShadow: `inset 0 0 24px ${glowCore}`, borderRadius: 'inherit' }}
          />

          <div className="relative z-10 min-h-full flex flex-col">
            {children}
          </div>
        </div>

        {activeChannel === 'home' && (
          <div className="relative overflow-hidden py-1" style={{ backgroundColor: 'rgba(10, 8, 6, 0.9)', borderTop: '1px solid rgba(245, 166, 35, 0.15)' }}>
            <TickerText />
          </div>
        )}

        {/* 底部控制面板 */}
        <div className="flex items-center justify-between px-3 sm:px-5 py-2 sm:py-2.5 gap-3" style={{ backgroundColor: '#1A1612', borderTop: '2px solid #2A2118' }}>
          <div className="flex items-center gap-3">
            <motion.div
              className="relative w-5 h-5 rounded-full flex items-center justify-center"
              style={{ backgroundColor: '#C22303' }}
              animate={{
                boxShadow: [
                  'inset 0 1px 2px rgba(0,0,0,0.5), 0 0 4px rgba(194, 35, 3, 0.3)',
                  'inset 0 1px 2px rgba(0,0,0,0.5), 0 0 12px rgba(194, 35, 3, 0.6)',
                  'inset 0 1px 2px rgba(0,0,0,0.5), 0 0 4px rgba(194, 35, 3, 0.3)',
                ],
              }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            >
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: '#FF4D4D' }} />
            </motion.div>
            <span className="text-[9px] tracking-wider opacity-40 hidden sm:block" style={{ fontFamily: 'var(--font-mono)' }}>
              POWER
            </span>
          </div>

          <div className="flex items-center gap-2">
            {channels.map((ch) => (
              <button
                key={ch.id}
                className="w-2 h-2 transition-all duration-200"
                style={{
                  backgroundColor: activeChannel === ch.id ? ch.color : 'rgba(247, 243, 232, 0.1)',
                  transform: activeChannel === ch.id ? 'scale(1.3)' : 'scale(1)',
                  clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
                }}
                onClick={() => handleChannelChange(ch.id)}
                data-cursor-hover
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[9px] tracking-wider opacity-40 hidden sm:block" style={{ fontFamily: 'var(--font-mono)' }}>
              TIME
            </span>
            <span className="text-xs font-bold tabular-nums" style={{ color: '#C4D70C', fontFamily: 'var(--font-mono)' }}>
              {time}
            </span>
          </div>
        </div>

        {/* ========== 台面倒影：紧贴底部的一条极扁彩色光带 ========== */}
        <motion.div
          className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-[75%] h-2.5 pointer-events-none"
          animate={{ background: `radial-gradient(ellipse 70% 35% at 50% 0%, ${glowColor} 0%, transparent 75%)` }}
          transition={{ duration: 0.8, ease: 'easeInOut' }}
          style={{ filter: 'blur(5px)' }}
        />
      </div>
    </div>
  );
}

function TickerText() {
  const items = [
    'LANGGRAPH 多 AGENT 工作流已上线',
    'POSTGRESQL + PGVECTOR 向量检索实战',
    'FASTAPI 项目结构最佳实践',
    'REACT 19 + TAILWIND CSS v4 前端架构',
    'SYSTEM STATUS: ALL SERVICES NORMAL',
  ];

  return (
    <div className="flex items-center whitespace-nowrap">
      <span className="text-[10px] tracking-wider px-2 shrink-0" style={{ color: '#F5A623', fontFamily: 'var(--font-mono)', borderRight: '1px solid rgba(245, 166, 35, 0.3)' }}>
        BREAKING
      </span>
      <div className="overflow-hidden flex-1 relative">
        <motion.div className="flex items-center gap-8 whitespace-nowrap" animate={{ x: ['0%', '-50%'] }} transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}>
          {[...items, ...items].map((text, i) => (
            <span key={i} className="text-[10px] tracking-wider opacity-70" style={{ color: '#FFF8EE', fontFamily: 'var(--font-mono)' }}>
              {text}
            </span>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
