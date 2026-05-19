import { motion } from 'framer-motion';
import { MessageSquare, Flame } from 'lucide-react';

const mockTopics = [
  {
    id: 1,
    title: '大家怎么看 AI 辅助编程的未来？',
    zone: '技术杂谈',
    replies: 34,
    hot: true,
    author: 'Dev_A',
  },
  {
    id: 2,
    title: '分享一个自用的 VS Code 主题配置',
    zone: '工具分享',
    replies: 18,
    hot: false,
    author: 'CodeWalker',
  },
  {
    id: 3,
    title: 'Python 3.13 新特性讨论汇总',
    zone: 'Python',
    replies: 52,
    hot: true,
    author: 'PyFan',
  },
  {
    id: 4,
    title: '独立开发者如何平衡工作与创作？',
    zone: '生活方式',
    replies: 27,
    hot: false,
    author: 'SoloDev',
  },
];

/**
 * 论坛预览 —— CH.02 访谈/脱口秀频道
 */
export default function ForumPreview() {
  return (
    <section className="relative py-8 sm:py-10 px-4 sm:px-8 lg:px-14" id="forum">
      <div className="max-w-5xl mx-auto">
        {/* 顶部频道标识 */}
        <motion.div
          className="mb-8 flex items-center gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#7FE6EF' }} />
          <span
            className="text-[10px] tracking-[0.3em] font-bold"
            style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}
          >
            TALK SHOW CHANNEL
          </span>
          <div className="h-px flex-1 bg-[#7FE6EF]/15" />
        </motion.div>

        {/* 话题列表：对话气泡风格 */}
        <div className="space-y-3">
          {mockTopics.map((topic, index) => (
            <motion.div
              key={topic.id}
              className="relative"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 }}
            >
              <div
                className="flex items-start gap-3 sm:gap-4 p-4 sm:p-5 chamfer"
                style={{
                  backgroundColor: topic.hot ? 'rgba(127, 230, 239, 0.04)' : 'rgba(42, 33, 24, 0.6)',
                  border: topic.hot
                    ? '1px solid rgba(127, 230, 239, 0.2)'
                    : '1px solid rgba(247, 243, 232, 0.06)',
                }}
                data-cursor-hover
              >
                {/* 左侧：嘉宾头像占位 + 身份标识 */}
                <div className="flex flex-col items-center gap-1 shrink-0">
                  <div
                    className="w-8 h-8 sm:w-10 sm:h-10 flex items-center justify-center text-xs font-bold"
                    style={{
                      backgroundColor: topic.hot ? 'rgba(127, 230, 239, 0.15)' : 'rgba(247, 243, 232, 0.05)',
                      color: topic.hot ? '#7FE6EF' : '#FFF8EE',
                      fontFamily: 'var(--font-mono)',
                      clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                    }}
                  >
                    {topic.author.slice(0, 2).toUpperCase()}
                  </div>
                  {topic.hot && (
                    <Flame size={12} style={{ color: '#FF4D4D' }} />
                  )}
                </div>

                {/* 中间：话题内容 */}
                <div className="flex-1 min-w-0">
                  <h3
                    className="text-sm sm:text-base font-medium leading-snug mb-1"
                    style={{ color: '#FFF8EE' }}
                  >
                    {topic.title}
                  </h3>
                  <div className="flex items-center gap-2">
                    <span
                      className="text-[9px] tracking-wider px-1.5 py-0.5"
                      style={{
                        backgroundColor: 'rgba(127, 230, 239, 0.08)',
                        color: '#7FE6EF',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {topic.zone}
                    </span>
                    <span
                      className="text-[9px] tracking-wider opacity-40"
                      style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE' }}
                    >
                      BY {topic.author}
                    </span>
                  </div>
                </div>

                {/* 右侧：观众来电数 */}
                <div className="flex items-center gap-1.5 shrink-0">
                  <MessageSquare size={12} style={{ color: '#7FE6EF', opacity: 0.6 }} />
                  <span
                    className="text-xs font-bold"
                    style={{ color: '#7FE6EF', fontFamily: 'var(--font-mono)' }}
                  >
                    {topic.replies}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
