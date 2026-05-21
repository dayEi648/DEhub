import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { NOISE_SVG_URL } from '../../utils/noiseTexture';

/**
 * 电视开机动画
 * 页面首次加载时：纯黑 → 水平亮线 → 垂直展开 → 内容显现
 * 
 * 注意：此组件由父组件控制挂载/卸载。当动画完成时，onComplete 回调通知父组件，
 * 父组件应在短暂延迟（至少 200ms，等待 exit 动画播放完毕）后再卸载此组件，
 * 以确保 AnimatePresence 的退出动画能够完整播放。
 */
export default function TVBootAnimation({ onComplete }: { onComplete?: () => void }) {
  const [phase, setPhase] = useState<'line' | 'expand' | 'done'>('line');

  useEffect(() => {
    const t1 = setTimeout(() => setPhase('expand'), 600);
    const t2 = setTimeout(() => {
      setPhase('done');
      // 延迟调用 onComplete，等待 exit 动画（200ms）播放完毕
      const t3 = setTimeout(() => {
        onComplete?.();
      }, 250);
      return () => clearTimeout(t3);
    }, 1200);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [onComplete]);

  return (
    <AnimatePresence>
      {phase !== 'done' && (
      <motion.div
        className="fixed inset-0 z-[10000] flex items-center justify-center"
        style={{ backgroundColor: '#1A1612' }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        {/* 水平亮线 */}
        {phase === 'line' && (
          <motion.div
            className="absolute w-full"
            style={{ height: 3, backgroundColor: '#FFE52C' }}
            initial={{ scaleX: 0, opacity: 0 }}
            animate={{ scaleX: 1, opacity: 1 }}
            transition={{ duration: 0.3, ease: [0.87, 0, 0.13, 1] }}
          />
        )}

        {/* 垂直展开 */}
        {phase === 'expand' && (
          <motion.div
            className="absolute w-full bg-[#FFE52C]"
            initial={{ height: 3 }}
            animate={{ height: '100vh', opacity: [1, 1, 0] }}
            transition={{
              height: { duration: 0.4, ease: [0.87, 0, 0.13, 1] },
              opacity: { duration: 0.3, delay: 0.3 },
            }}
          />
        )}

        {/* 雪花噪点层（短暂闪现） */}
        <motion.div
          className="absolute inset-0"
          style={{
            backgroundImage: NOISE_SVG_URL,
            backgroundSize: '128px 128px',
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.4, 0.2, 0] }}
          transition={{ duration: 0.5, times: [0, 0.3, 0.6, 1] }}
        />
      </motion.div>
      )}
    </AnimatePresence>
  );
}
