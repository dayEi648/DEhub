import { motion } from 'framer-motion';

interface ColorBarStripProps {
  height?: number;
  className?: string;
  animated?: boolean;
}

/**
 * 电视信号彩条装饰
 * P4标志性视觉元素：流动的多色垂直条纹
 */
export default function ColorBarStrip({
  height = 4,
  className = '',
  animated = true,
}: ColorBarStripProps) {
  return (
    <motion.div
      className={`w-full overflow-hidden ${className}`}
      style={{ height }}
      initial={{ scaleX: 0 }}
      whileInView={{ scaleX: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
    >
      <div
        className={animated ? 'color-bars-flow h-full w-[200%]' : 'h-full w-full'}
        style={
          animated
            ? undefined
            : {
                background: `repeating-linear-gradient(
                  90deg,
                  #FF4D4D 0px, #FF4D4D 16px,
                  #FFE52C 16px, #FFE52C 32px,
                  #C4D70C 32px, #C4D70C 48px,
                  #7FE6EF 48px, #7FE6EF 64px,
                  #F7F3E8 64px, #F7F3E8 80px,
                  #1A1612 80px, #1A1612 96px
                )`,
              }
        }
      />
    </motion.div>
  );
}
