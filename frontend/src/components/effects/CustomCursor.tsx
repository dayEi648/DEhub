import { useEffect, useRef, useState } from 'react';
import { motion, useSpring, useMotionValue } from 'framer-motion';

/**
 * 自定义光标
 * P4风格：多层几何指针，高刚度快速跟随，悬停时变形脉冲
 *
 * 结构（由内到外）：
 * 1. 中心准星点（深黑/暖金）
 * 2. 内层填充菱形（亮黄/暖白）
 * 3. 中层轮廓菱形（暖金描边）
 * 4. 外层漫射光晕（暖金模糊圆）
 */
export default function CustomCursor() {
  const [isHovering, setIsHovering] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [isClicking, setIsClicking] = useState(false);
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const isVisibleRef = useRef(false);

  // 高刚度、低阻尼、轻质量 → 极致跟手，仅保留极轻微弹性缓冲
  const springConfig = { damping: 18, stiffness: 900, mass: 0.4 };
  const smoothX = useSpring(cursorX, springConfig);
  const smoothY = useSpring(cursorY, springConfig);

  useEffect(() => {
    const isTouch = window.matchMedia('(hover: none) and (pointer: coarse)').matches;
    if (isTouch) return;

    const moveCursor = (e: MouseEvent) => {
      cursorX.set(e.clientX);
      cursorY.set(e.clientY);
      if (!isVisibleRef.current) {
        isVisibleRef.current = true;
        setIsVisible(true);
      }
    };

    const handleMouseEnter = () => setIsVisible(true);
    const handleMouseLeave = () => {
      isVisibleRef.current = false;
      setIsVisible(false);
    };
    const handleMouseDown = () => setIsClicking(true);
    const handleMouseUp = () => setIsClicking(false);

    // 事件委托：在 document 上监听，避免反复绑定与 MutationObserver 的性能损耗
    const handleDelegateOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.closest('a, button, [role="button"], input, textarea, select, [data-cursor-hover]')
      ) {
        setIsHovering(true);
      }
    };
    const handleDelegateOut = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target.closest('a, button, [role="button"], input, textarea, select, [data-cursor-hover]')
      ) {
        setIsHovering(false);
      }
    };

    window.addEventListener('mousemove', moveCursor, { passive: true });
    document.addEventListener('mouseenter', handleMouseEnter);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseover', handleDelegateOver);
    document.addEventListener('mouseout', handleDelegateOut);
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', moveCursor);
      document.removeEventListener('mouseenter', handleMouseEnter);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseover', handleDelegateOver);
      document.removeEventListener('mouseout', handleDelegateOut);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [cursorX, cursorY]);

  if (
    typeof window !== 'undefined' &&
    window.matchMedia('(hover: none) and (pointer: coarse)').matches
  ) {
    return null;
  }

  return (
    <motion.div
      className="fixed top-0 left-0 pointer-events-none z-[9999]"
      style={{
        x: smoothX,
        y: smoothY,
      }}
    >
      {/* ==== 外层漫射光晕 ==== */}
      <motion.div
        className="absolute"
        animate={{
          scale: isHovering ? 2.2 : isClicking ? 0.7 : 1,
          opacity: isVisible ? (isHovering ? 0.4 : 0.15) : 0,
        }}
        transition={{ type: 'spring', damping: 20, stiffness: 500 }}
        style={{
          width: 36,
          height: 36,
          marginLeft: -18,
          marginTop: -18,
          borderRadius: '50%',
          background: 'radial-gradient(circle, #F5A623 0%, transparent 70%)',
          filter: 'blur(8px)',
        }}
      />

      {/* ==== 中层轮廓菱形 ==== */}
      <motion.div
        className="absolute"
        animate={{
          scale: isHovering ? 1.6 : isClicking ? 0.8 : 1,
          rotate: isHovering ? 0 : 45,
        }}
        transition={{ type: 'spring', damping: 18, stiffness: 600 }}
        style={{
          width: 20,
          height: 20,
          marginLeft: -10,
          marginTop: -10,
          backgroundColor: 'transparent',
          border: '2.5px solid #F5A623',
          transform: 'rotate(45deg)',
          opacity: isVisible ? 1 : 0,
        }}
      />

      {/* ==== 内层填充菱形 ==== */}
      <motion.div
        className="absolute"
        animate={{
          scale: isHovering ? 1.35 : isClicking ? 0.75 : 1,
          rotate: isHovering ? 0 : 45,
          backgroundColor: isHovering ? '#FFF8EE' : '#FFE52C',
        }}
        transition={{ type: 'spring', damping: 18, stiffness: 600 }}
        style={{
          width: 12,
          height: 12,
          marginLeft: -6,
          marginTop: -6,
          transform: 'rotate(45deg)',
          opacity: isVisible ? 0.95 : 0,
        }}
      />

      {/* ==== 中心准星点 ==== */}
      <motion.div
        className="absolute"
        animate={{
          scale: isHovering ? 0.5 : isClicking ? 1.6 : 1,
          backgroundColor: isHovering ? '#F5A623' : '#1A1612',
        }}
        transition={{ type: 'spring', damping: 18, stiffness: 700 }}
        style={{
          width: 5,
          height: 5,
          marginLeft: -2.5,
          marginTop: -2.5,
          borderRadius: '50%',
          opacity: isVisible ? 1 : 0,
          boxShadow: isHovering
            ? '0 0 6px 2px rgba(245, 166, 35, 0.6)'
            : 'none',
        }}
      />

      {/* ==== 四角装饰点（悬停时出现） ==== */}
      <motion.div
        className="absolute"
        animate={{
          scale: isHovering ? 1 : 0,
          opacity: isHovering ? 0.8 : 0,
        }}
        transition={{ type: 'spring', damping: 16, stiffness: 400 }}
        style={{
          width: 28,
          height: 28,
          marginLeft: -14,
          marginTop: -14,
        }}
      >
        {/* 上 */}
        <div
          className="absolute left-1/2 -translate-x-1/2"
          style={{ top: -3, width: 3, height: 3, backgroundColor: '#FFE52C' }}
        />
        {/* 下 */}
        <div
          className="absolute left-1/2 -translate-x-1/2"
          style={{ bottom: -3, width: 3, height: 3, backgroundColor: '#FFE52C' }}
        />
        {/* 左 */}
        <div
          className="absolute top-1/2 -translate-y-1/2"
          style={{ left: -3, width: 3, height: 3, backgroundColor: '#FFE52C' }}
        />
        {/* 右 */}
        <div
          className="absolute top-1/2 -translate-y-1/2"
          style={{ right: -3, width: 3, height: 3, backgroundColor: '#FFE52C' }}
        />
      </motion.div>
    </motion.div>
  );
}
