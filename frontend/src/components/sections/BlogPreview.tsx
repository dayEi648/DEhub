import { motion } from 'framer-motion';
import ChamferCard from '../ui/ChamferCard';

const mockPosts = [
  {
    id: 1,
    title: 'LangGraph 多 Agent 工作流编排实战',
    category: 'AI',
    date: '2026.05.12',
    readTime: '12 min',
    tags: ['LangGraph', 'Python', 'Agent'],
    summary: '从零构建一个支持条件分支、循环与状态持久化的多 Agent 协作系统。',
  },
  {
    id: 2,
    title: 'PostgreSQL + pgvector 构建 RAG 向量检索',
    category: '后端',
    date: '2026.04.28',
    readTime: '8 min',
    tags: ['PostgreSQL', 'RAG', '向量检索'],
    summary: '在自有数据库中实现 Embedding 存储与相似度搜索，告别外部向量库。',
  },
  {
    id: 3,
    title: 'FastAPI 项目结构最佳实践',
    category: '后端',
    date: '2026.04.15',
    readTime: '6 min',
    tags: ['FastAPI', 'Python', '架构'],
    summary: '经过多个项目验证的目录组织方式与依赖注入模式。',
  },
];

/**
 * 博客预览 —— CH.01 纪录片/科教频道
 *
 * 风格：节目播出表
 */
export default function BlogPreview() {
  return (
    <section className="relative py-8 sm:py-10 px-4 sm:px-8 lg:px-14" id="blog">
      {/* 顶部频道标识 */}
      <motion.div
        className="max-w-5xl mx-auto mb-8 flex items-center gap-3"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#FFE52C' }} />
        <span
          className="text-[10px] tracking-[0.3em] font-bold"
          style={{ color: '#FFE52C', fontFamily: 'var(--font-mono)' }}
        >
          DOCUMENTARY CHANNEL
        </span>
        <div className="h-px flex-1 bg-[#FFE52C]/15" />
      </motion.div>

      {/* 节目播出表 */}
      <div className="max-w-5xl mx-auto space-y-3">
        {mockPosts.map((post, index) => (
          <motion.div
            key={post.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: index * 0.15 }}
          >
            <ChamferCard className="p-0 overflow-hidden lens-reflect" hoverable>
              <div className="flex flex-col sm:flex-row">
                {/* 左侧：时间轴信息 */}
                <div
                  className="flex flex-row sm:flex-col items-center sm:items-start justify-between sm:justify-center gap-2 sm:gap-1 px-4 sm:px-5 py-3 sm:py-4 min-w-[120px]"
                  style={{ backgroundColor: 'rgba(255, 229, 44, 0.05)', borderRight: '1px solid rgba(255, 229, 44, 0.1)' }}
                >
                  <span
                    className="text-xs font-bold"
                    style={{ color: '#FFE52C', fontFamily: 'var(--font-mono)' }}
                  >
                    {post.date}
                  </span>
                  <span
                    className="text-[10px] tracking-wider opacity-50"
                    style={{ fontFamily: 'var(--font-mono)', color: '#FFF8EE' }}
                  >
                    {post.readTime}
                  </span>
                </div>

                {/* 右侧：内容 */}
                <div className="flex-1 p-4 sm:p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="text-[9px] tracking-wider px-1.5 py-0.5"
                      style={{
                        backgroundColor: 'rgba(255, 229, 44, 0.1)',
                        color: '#FFE52C',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {post.category}
                    </span>
                  </div>

                  <h3
                    className="text-base sm:text-lg font-bold mb-2 leading-snug"
                    style={{ color: '#FFF8EE', fontFamily: 'var(--font-body)' }}
                  >
                    {post.title}
                  </h3>

                  <p
                    className="text-xs sm:text-sm mb-3 leading-relaxed"
                    style={{ color: '#FFF8EE', opacity: 0.55 }}
                  >
                    {post.summary}
                  </p>

                  <div className="flex flex-wrap gap-2">
                    {post.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[9px] tracking-wider px-1.5 py-0.5"
                        style={{
                          border: '1px solid rgba(247, 243, 232, 0.1)',
                          color: '#F7F3E8',
                          opacity: 0.5,
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </ChamferCard>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
