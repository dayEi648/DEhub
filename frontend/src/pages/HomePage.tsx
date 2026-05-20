import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import TVFrame from '../components/layout/TVFrame';
import UserHud from '../components/layout/UserHud';
import HeroSection from '../components/sections/HeroSection';
import BlogPreview from '../components/sections/BlogPreview';
import ForumPreview from '../components/sections/ForumPreview';
import AIChatEntry from '../components/sections/AIChatEntry';
import SiteLinks from '../components/sections/SiteLinks';
import Footer from '../components/layout/Footer';
import { useAuth } from '../contexts/AuthContext';
import { useLogout } from '../hooks/useLogout';

export default function HomePage() {
  const [activeChannel, setActiveChannel] = useState('home');
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const channelContent = useMemo(() => {
    switch (activeChannel) {
      case 'home': return <HeroSection />;
      case 'blog': return <BlogPreview />;
      case 'forum': return <ForumPreview />;
      case 'ai': return <AIChatEntry />;
      case 'links': return <SiteLinks />;
      default: return <HeroSection />;
    }
  }, [activeChannel]);

  const { handleLogout } = useLogout();

  return (
    <>
      {/* 全局 HUD：右上角 OSD 用户入口 */}
      <UserHud
        user={user}
        isAdmin={isAdmin}
        onNavigate={navigate}
        onLogout={handleLogout}
      />

      {/* 胶片噪点 */}
      <FilmGrain />
      <SignalIndicator />
      <Timecode />
      <SafeFrameMarkers />

      <TVFrame activeChannel={activeChannel} onChannelChange={setActiveChannel}>
        {channelContent}
        {activeChannel === 'home' && <Footer />}
      </TVFrame>
    </>
  );
}

/** 胶片噪点 */
function FilmGrain() {
  return (
    <div
      className="fixed inset-0 pointer-events-none z-0"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        backgroundSize: '128px 128px',
        opacity: 0.1,
      }}
    />
  );
}

/** 左上角信号标记 */
function SignalIndicator() {
  const bars = [0.35, 0.55, 0.75, 1, 0.6];
  return (
    <div className="fixed top-5 left-5 sm:top-6 sm:left-6 pointer-events-none z-0">
      <div className="flex flex-col gap-1.5">
        <span
          className="text-[9px] tracking-[0.35em]"
          style={{ fontFamily: 'var(--font-mono)', color: 'rgba(247, 243, 232, 0.7)' }}
        >
          SIGNAL
        </span>
        <div className="flex items-end gap-[3px] h-3.5">
          {bars.map((h, i) => (
            <motion.div
              key={i}
              className="w-[3px] rounded-[1px]"
              style={{
                height: `${h * 100}%`,
                backgroundColor: i === 3 ? '#C4D70C' : 'rgba(247, 243, 232, 0.8)',
              }}
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{
                duration: 2 + i * 0.4,
                repeat: Infinity,
                ease: 'easeInOut',
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

/** 右下角录像时间码 */
function Timecode() {
  const [timecode, setTimecode] = useState('00:00:00:00');
  useEffect(() => {
    let frame = 0;
    const interval = setInterval(() => {
      frame = (frame + 1) % 30;
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      const f = String(frame).padStart(2, '0');
      setTimecode(`${h}:${m}:${s}:${f}`);
    }, 33);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-5 right-5 sm:bottom-6 sm:right-6 pointer-events-none z-0">
      <div className="flex items-center gap-2">
        <motion.div
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: '#FF4D4D' }}
          animate={{ opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
        />
        <span
          className="text-[10px] tabular-nums tracking-wider"
          style={{ fontFamily: 'var(--font-mono)', color: 'rgba(247, 243, 232, 0.7)' }}
        >
          {timecode}
        </span>
      </div>
    </div>
  );
}

/** 安全框标记 */
function SafeFrameMarkers() {
  return (
    <div className="fixed inset-4 sm:inset-6 pointer-events-none z-[5]">
      <div className="absolute top-0 left-0 w-8 sm:w-10 h-px bg-[#FFF8EE] opacity-35" />
      <div className="absolute top-0 left-0 w-px h-8 sm:h-10 bg-[#FFF8EE] opacity-35" />
      <div className="absolute top-0 right-0 w-8 sm:w-10 h-px bg-[#FFF8EE] opacity-35" />
      <div className="absolute top-0 right-0 w-px h-8 sm:h-10 bg-[#FFF8EE] opacity-35" />
      <div className="absolute bottom-0 left-0 w-8 sm:w-10 h-px bg-[#FFF8EE] opacity-35" />
      <div className="absolute bottom-0 left-0 w-px h-8 sm:h-10 bg-[#FFF8EE] opacity-35" />
      <div className="absolute bottom-0 right-0 w-8 sm:w-10 h-px bg-[#FFF8EE] opacity-35" />
      <div className="absolute bottom-0 right-0 w-px h-8 sm:h-10 bg-[#FFF8EE] opacity-35" />
    </div>
  );
}
