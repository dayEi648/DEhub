import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

/**
 * Hero 区域 —— CH.00 概览频道（新闻台风格）
 */
export default function HeroSection() {
  const navigate = useNavigate();
  const containerVariants = {
    hidden: {},
    visible: {
      transition: { staggerChildren: 0.1, delayChildren: 0.2 },
    },
  };

  const itemVariants = {
    hidden: { y: 40, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
    },
  };

  const skills = ['Python', 'FastAPI', 'React', 'LangGraph', 'PostgreSQL'];

  return (
    <section className="relative min-h-full flex items-center justify-center overflow-hidden px-4 sm:px-8 lg:px-14 py-10 sm:py-12">
      {/* 背景装饰 */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            linear-gradient(135deg, transparent 40%, rgba(245, 166, 35, 0.03) 40%, rgba(245, 166, 35, 0.03) 45%, transparent 45%),
            linear-gradient(135deg, transparent 60%, rgba(255, 229, 44, 0.02) 60%, rgba(255, 229, 44, 0.02) 65%, transparent 65%)
          `,
        }}
      />

      {/* 右侧静态装饰条 */}
      <motion.div
        className="absolute right-0 top-1/4 bottom-1/4 w-1"
        style={{
          background: 'linear-gradient(180deg, transparent, #F5A623, #FFE52C, #7FE6EF, transparent)',
          opacity: 0.5,
        }}
        initial={{ scaleY: 0, skewY: -15 }}
        animate={{ scaleY: 1, skewY: -15 }}
        transition={{ delay: 0.5, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      />

      {/* LIVE 直播标识 */}
      <motion.div
        className="absolute top-4 right-4 sm:top-6 sm:right-6 flex items-center gap-1.5 z-20"
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.8, duration: 0.5 }}
      >
        <motion.div
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: '#FF4D4D' }}
          animate={{
            boxShadow: [
              '0 0 0 0 rgba(255, 77, 77, 0)',
              '0 0 8px 2px rgba(255, 77, 77, 0.5)',
              '0 0 0 0 rgba(255, 77, 77, 0)',
            ],
          }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />
        <span
          className="text-[10px] font-bold tracking-widest"
          style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}
        >
          LIVE
        </span>
      </motion.div>

      {/* 主内容 */}
      <motion.div
        className="relative z-10 w-full max-w-5xl"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <div
          className="relative p-6 sm:p-8 lg:p-12"
          style={{
            border: '3px solid #2A2118',
            background: 'rgba(26, 22, 18, 0.6)',
          }}
        >
          {/* 内框高光 */}
          <div
            className="absolute inset-2 pointer-events-none"
            style={{ border: '1px solid rgba(247, 243, 232, 0.08)' }}
          />

          <div className="relative">
            {/* 顶部标签栏 */}
            <motion.div
              className="flex items-center justify-between mb-6"
              variants={itemVariants}
            >
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rotate-45" style={{ backgroundColor: '#FFE52C' }} />
                <span
                  className="text-xs tracking-[0.3em] opacity-60"
                  style={{ fontFamily: 'var(--font-mono)' }}
                >
                  PERSONAL DEV SPACE
                </span>
              </div>
            </motion.div>

            {/* 主标题 */}
            <motion.h1
              className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight mb-4"
              style={{
                fontFamily: 'var(--font-display)',
                color: '#F5A623',
                lineHeight: 0.95,
                letterSpacing: '-0.02em',
              }}
              variants={itemVariants}
            >
              DE
              <br />
              <span style={{ color: '#FFF8EE' }}>hub</span>
            </motion.h1>

            {/* 斜向分割线 */}
            <motion.div
              className="my-6 h-px w-48 origin-left"
              style={{
                background: 'linear-gradient(90deg, #F5A623, #FFE52C, #7FE6EF)',
                transform: 'rotate(-2deg)',
              }}
              variants={itemVariants}
            />

            {/* 副标题 */}
            <motion.p
              className="text-base sm:text-lg max-w-lg mb-6 leading-relaxed"
              style={{ color: '#FFF8EE', opacity: 0.85 }}
              variants={itemVariants}
            >
              <span className="hidden sm:inline">开发者个人空间站 —— 记录技术探索的轨迹，</span>
              <span className="sm:hidden">开发者个人空间站 —— 记录技术探索的轨迹，</span>
              <br />
              分享对代码与世界的思考
            </motion.p>

            {/* 技能标签 —— 新闻台风格的信息条 */}
            <motion.div
              className="flex flex-wrap gap-2 mb-6"
              variants={itemVariants}
            >
              {skills.map((skill) => (
                <span
                  key={skill}
                  className="text-[10px] tracking-wider px-2 py-1"
                  style={{
                    border: '1px solid rgba(245, 166, 35, 0.3)',
                    color: '#F5A623',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  {skill}
                </span>
              ))}
            </motion.div>

            {/* CTA 按钮组 */}
            <motion.div
              className="flex flex-wrap gap-4"
              variants={itemVariants}
            >
              <button
                onClick={() => navigate('/blog')}
                className="chamfer px-6 py-2.5 text-xs sm:text-sm font-bold tracking-wider relative overflow-hidden lens-reflect"
                style={{
                  backgroundColor: '#F5A623',
                  color: '#2A2118',
                  fontFamily: 'var(--font-display)',
                }}
                data-cursor-hover
              >
                进入博客
              </button>
              <button
                onClick={() => navigate('/?channel=ai')}
                className="chamfer px-6 py-2.5 text-xs sm:text-sm font-bold tracking-wider relative overflow-hidden"
                style={{
                  backgroundColor: 'transparent',
                  color: '#F5A623',
                  border: '2px solid #F5A623',
                  fontFamily: 'var(--font-display)',
                }}
                data-cursor-hover
              >
                AI 对话
              </button>
            </motion.div>
          </div>
        </div>

        {/* 右下角装饰 */}
        <motion.div
          className="absolute -bottom-5 right-4 text-[10px] tracking-[0.5em] opacity-30"
          style={{ fontFamily: 'var(--font-mono)', color: '#F5A623' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.3 }}
          transition={{ delay: 1, duration: 0.8 }}
        >
          SYSTEM ONLINE
        </motion.div>
      </motion.div>
    </section>
  );
}
