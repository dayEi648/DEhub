import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * 电视开机动画
 * 页面首次加载时：纯黑 → 水平亮线 → 垂直展开 → 内容显现
 */
export default function TVBootAnimation({ onComplete }: { onComplete?: () => void }) {
  const [phase, setPhase] = useState<'line' | 'expand' | 'done'>('line');

  useEffect(() => {
    const t1 = setTimeout(() => setPhase('expand'), 600);
    const t2 = setTimeout(() => {
      setPhase('done');
      onComplete?.();
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
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.4'/%3E%3C/svg%3E")`,
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
