import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { NOISE_SVG_URL } from '../../utils/noiseTexture';

interface ChannelSwitchEffectProps {
  trigger: string | number;
  channelNumber?: string;
  channelColor?: string;
  onComplete?: () => void;
}

type Phase = 'idle' | 'dim' | 'scanline' | 'flash' | 'reveal' | 'done';

/**
 * 电视换台效果 —— CRT 亮线展开式转场
 *
 * 动画阶段：
 * 1. dim      (0-120ms)   : 当前画面快速变暗，模拟电子枪关闭
 * 2. scanline (100-350ms) : 扫描线从上往下扫过，扫过处彻底黑屏
 * 3. flash    (300-550ms) : 中央黄色水平亮线出现并垂直展开填满屏幕
 * 4. reveal   (500-850ms) : 亮线收缩消失，新内容从模糊到清晰稳定显现
 * 5. done     (850ms)     : 动画结束
 *
 * 整体节奏模仿老式显像管电视换台时的物理感：
 * 不是生硬的"加载中"，而是有重量感的画面切换。
 */
export default function ChannelSwitchEffect({
  trigger,
  channelNumber = '',
  channelColor = '#F5A623',
  onComplete,
}: ChannelSwitchEffectProps) {
  const [phase, setPhase] = useState<Phase>('idle');

  useEffect(() => {
    if (trigger === 0) return;
    setPhase('dim');

    const timers = [
      setTimeout(() => setPhase('scanline'), 100),
      setTimeout(() => setPhase('flash'), 320),
      setTimeout(() => setPhase('reveal'), 520),
      setTimeout(() => {
        setPhase('done');
        onComplete?.();
      }, 850),
    ];

    return () => timers.forEach(clearTimeout);
  }, [trigger, onComplete]);

  useEffect(() => {
    if (phase === 'done') {
      const t = setTimeout(() => setPhase('idle'), 100);
      return () => clearTimeout(t);
    }
  }, [phase]);

  return (
    <AnimatePresence>
      {phase !== 'idle' && phase !== 'done' && (
        <motion.div
          className="absolute inset-0 z-[60] pointer-events-none flex items-center justify-center overflow-hidden"
          style={{ backgroundColor: '#0a0806' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.08 }}
        >
          {/* ===== 阶段 1: 画面变暗层 ===== */}
          {phase === 'dim' && (
            <motion.div
              className="absolute inset-0"
              style={{ backgroundColor: '#000' }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.1 }}
            />
          )}

          {/* ===== 阶段 2: 扫描线横扫 ===== */}
          {(phase === 'scanline' || phase === 'flash') && (
            <>
              {/* 扫描线本体 */}
              <motion.div
                className="absolute left-0 right-0 h-1 z-10"
                style={{
                  background: `linear-gradient(180deg, transparent, ${channelColor}, transparent)`,
                  boxShadow: `0 0 8px ${channelColor}, 0 0 20px ${channelColor}40`,
                }}
                initial={{ top: '-2%' }}
                animate={{ top: '102%' }}
                transition={{ duration: 0.22, ease: 'easeIn' }}
              />
              {/* 扫描线扫过后的黑屏残留 */}
              <motion.div
                className="absolute inset-0"
                style={{ backgroundColor: '#0a0806' }}
                initial={{ clipPath: 'inset(0 0 100% 0)' }}
                animate={{ clipPath: 'inset(0 0 0% 0)' }}
                transition={{ duration: 0.22, ease: 'easeIn' }}
              />
              {/* 扫描噪点纹理 */}
              <motion.div
                className="absolute inset-0"
                style={{
                  backgroundImage: NOISE_SVG_URL,
                  backgroundSize: '96px 96px',
                  mixBlendMode: 'overlay',
                }}
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0.35, 0.15, 0] }}
                transition={{ duration: 0.35, times: [0, 0.3, 0.6, 1] }}
              />
            </>
          )}

          {/* ===== 阶段 3: 黄色亮线展开 ===== */}
          {(phase === 'flash' || phase === 'reveal') && (
            <>
              {/* 水平亮线 → 垂直展开 */}
              <motion.div
                className="absolute left-0 right-0"
                style={{
                  backgroundColor: channelColor,
                  boxShadow: `
                    0 0 20px ${channelColor}60,
                    0 0 60px ${channelColor}30,
                    inset 0 0 40px rgba(255,255,255,0.2)
                  `,
                }}
                initial={{ top: '50%', height: 2, opacity: 0 }}
                animate={phase === 'flash'
                  ? { top: '50%', height: 2, opacity: 1 }
                  : { top: '0%', height: '100%', opacity: [1, 1, 0.8] }
                }
                transition={phase === 'flash'
                  ? { duration: 0.12, ease: [0.87, 0, 0.13, 1] }
                  : { duration: 0.25, ease: [0.87, 0, 0.13, 1] }
                }
              />

              {/* RGB 色彩分离效果（模拟 CRT 换台失真） */}
              <motion.div
                className="absolute left-0 right-0"
                style={{
                  height: 2,
                  background: `linear-gradient(90deg, #FF4D4D, ${channelColor}, #7FE6EF)`,
                  filter: 'blur(2px)',
                }}
                initial={{ top: '50%', opacity: 0 }}
                animate={phase === 'flash'
                  ? { top: '50%', opacity: [0, 0.6, 0] }
                  : { top: '0%', opacity: 0 }
                }
                transition={{ duration: 0.2 }}
              />

              {/* 大号频道号（在亮线展开时闪现） */}
              {phase === 'flash' && (
                <motion.span
                  className="absolute z-20 text-5xl sm:text-6xl font-black tracking-tighter"
                  style={{
                    color: '#0a0806',
                    fontFamily: 'var(--font-display)',
                    lineHeight: 1,
                    textShadow: `0 0 20px ${channelColor}40`,
                  }}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: [0, 1, 1, 0], scale: [0.8, 1, 1, 1.1] }}
                  transition={{ duration: 0.3, times: [0, 0.2, 0.7, 1] }}
                >
                  {channelNumber}
                </motion.span>
              )}
            </>
          )}

          {/* ===== 阶段 4: 内容揭示 ===== */}
          {phase === 'reveal' && (
            <>
              {/* 黄色收缩时在新内容上的扫描线覆盖 */}
              <motion.div
                className="absolute inset-0"
                style={{
                  background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.3) 2px, rgba(0,0,0,0.3) 4px)',
                }}
                initial={{ opacity: 0.6 }}
                animate={{ opacity: 0 }}
                transition={{ duration: 0.3, delay: 0.1 }}
              />
              {/* 轻微 picture-roll（画面上下抖动后稳定） */}
              <motion.div
                className="absolute inset-0"
                style={{
                  background: 'linear-gradient(180deg, rgba(245,166,35,0.03) 0%, transparent 30%, transparent 70%, rgba(245,166,35,0.03) 100%)',
                }}
                initial={{ y: 0 }}
                animate={{ y: [0, -3, 2, -1, 0] }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
              />
            </>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
