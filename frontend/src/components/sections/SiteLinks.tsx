import { motion } from 'framer-motion';
import { ExternalLink, Radio } from 'lucide-react';

const links = [
  { name: 'GitHub', desc: '开源项目与代码仓库', color: '#F5A623', status: 'ON AIR' },
  { name: '技术笔记', desc: '碎片化知识整理', color: '#FFE52C', status: 'ON AIR' },
  { name: '设计实验', desc: '前端视觉探索', color: '#7FE6EF', status: 'SOON' },
  { name: '工具箱', desc: '常用开发工具集', color: '#C4D70C', status: 'ON AIR' },
];

/**
 * 子站链接 —— CH.04 导视频道
 */
export default function SiteLinks() {
  return (
    <section className="relative py-8 sm:py-10 px-4 sm:px-8 lg:px-14" id="links">
      <div className="max-w-5xl mx-auto">
        {/* 顶部频道标识 */}
        <motion.div
          className="mb-8 flex items-center gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="w-1.5 h-1.5 rotate-45" style={{ backgroundColor: '#FF4D4D' }} />
          <span
            className="text-[10px] tracking-[0.3em] font-bold"
            style={{ color: '#FF4D4D', fontFamily: 'var(--font-mono)' }}
          >
            GUIDE CHANNEL
          </span>
          <div className="h-px flex-1 bg-[#FF4D4D]/15" />
        </motion.div>

        {/* 节目预告网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {links.map((link, index) => (
            <motion.a
              key={link.name}
              href="#"
              className="group relative block overflow-hidden"
              style={{
                backgroundColor: 'rgba(42, 33, 24, 0.7)',
                border: `2px solid ${link.color}18`,
              }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{
                backgroundColor: `${link.color}10`,
                borderColor: `${link.color}40`,
              }}
              onClick={(e) => e.preventDefault()}
              data-cursor-hover
            >
              {/* 顶部状态条 */}
              <div
                className="flex items-center justify-between px-3 py-1.5"
                style={{ backgroundColor: `${link.color}10` }}
              >
                <div className="flex items-center gap-1.5">
                  <Radio size={10} style={{ color: link.color, opacity: 0.7 }} />
                  <span
                    className="text-[9px] tracking-wider font-bold"
                    style={{ color: link.color, fontFamily: 'var(--font-mono)' }}
                  >
                    {link.status}
                  </span>
                </div>
                <ExternalLink size={10} style={{ color: link.color, opacity: 0.4 }} />
              </div>

              {/* 内容 */}
              <div className="p-4 sm:p-5">
                <h3
                  className="text-lg sm:text-xl font-black mb-2 group-hover:translate-x-1 transition-transform duration-200"
                  style={{ fontFamily: 'var(--font-display)', color: link.color }}
                >
                  {link.name}
                </h3>
                <p
                  className="text-xs sm:text-sm leading-relaxed"
                  style={{ color: '#FFF8EE', opacity: 0.55 }}
                >
                  {link.desc}
                </p>
              </div>

              {/* 底部装饰线 */}
              <div
                className="h-0.5 w-full origin-left scale-x-0 group-hover:scale-x-100 transition-transform duration-300"
                style={{ backgroundColor: link.color }}
              />
            </motion.a>
          ))}
        </div>
      </div>
    </section>
  );
}
