import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Glasses, Terminal, ChevronRight } from 'lucide-react';

/**
 * AI 对话入口 —— CH.03 科幻/终端频道
 */
export default function AIChatEntry() {
  const [typedText, setTypedText] = useState('');
  const fullText = '> 初始化多 Agent 协作系统...\n> 加载 LangGraph 工作流引擎...\n> 连接向量数据库 [OK]\n> 等待用户输入指令_';

  useEffect(() => {
    let index = 0;
    setTypedText('');
    const interval = setInterval(() => {
      if (index < fullText.length) {
        setTypedText(fullText.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 45);
    return () => clearInterval(interval);
  }, []);

  const codeLines = [
    'import { Agent } from "langgraph"',
    'const graph = new StateGraph()',
    'graph.addNode("research", researchAgent)',
    'graph.addNode("coding", codingAgent)',
    'graph.addEdge("research", "coding")',
    '// 等待输入...',
  ];

  return (
    <section className="relative min-h-[50vh] px-4 sm:px-8 lg:px-14 py-10 overflow-hidden" id="ai">
      {/* 背景数据流（极淡的氛围层） */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {codeLines.map((line, i) => (
          <motion.div
            key={i}
            className="absolute text-[10px] tracking-wider whitespace-nowrap"
            style={{
              top: `${10 + i * 18}%`,
              left: `${5 + (i % 3) * 30}%`,
              color: '#C4D70C',
              opacity: 0.04,
              fontFamily: 'var(--font-mono)',
            }}
            animate={{ x: [0, -20, 0] }}
            transition={{ duration: 8 + i * 2, repeat: Infinity, ease: 'linear' }}
          >
            {line}
          </motion.div>
        ))}
      </div>

      <div className="max-w-5xl mx-auto relative z-10">
        {/* 顶部终端风格标题栏 */}
        <motion.div
          className="flex items-center gap-2 mb-6"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Terminal size={14} style={{ color: '#C4D70C' }} />
          <span
            className="text-xs tracking-[0.3em] font-bold"
            style={{ color: '#C4D70C', fontFamily: 'var(--font-mono)' }}
          >
            AI_CONSOLE.exe
          </span>
          <div className="h-px flex-1 bg-[#C4D70C]/20" />
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* 左侧：打字机命令行 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <div
              className="p-5 sm:p-6 chamfer"
              style={{
                backgroundColor: 'rgba(10, 12, 8, 0.9)',
                border: '1px solid rgba(196, 215, 12, 0.2)',
              }}
            >
              {/* 窗口按钮 */}
              <div className="flex items-center gap-1.5 mb-4">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#C22303' }} />
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#FFE52C' }} />
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#C4D70C' }} />
              </div>

              {/* 打字机文本 */}
              <pre
                className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap"
                style={{ color: '#C4D70C', fontFamily: 'var(--font-mono)' }}
              >
                {typedText}
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.5, repeat: Infinity }}
                >
                  █
                </motion.span>
              </pre>

              {/* 快捷指令 */}
              <div className="mt-5 flex flex-wrap gap-2">
                {['知识检索', '代码分析', '工作流编排'].map((cmd) => (
                  <button
                    key={cmd}
                    className="flex items-center gap-1 px-3 py-1.5 text-[10px] tracking-wider transition-colors duration-150"
                    style={{
                      backgroundColor: 'rgba(196, 215, 12, 0.08)',
                      color: '#C4D70C',
                      border: '1px solid rgba(196, 215, 12, 0.2)',
                      fontFamily: 'var(--font-mono)',
                    }}
                    data-cursor-hover
                  >
                    <ChevronRight size={10} />
                    {cmd}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* 右侧：眼镜符号 + 说明 */}
          <motion.div
            className="flex flex-col items-center justify-center"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <motion.div
              className="relative mb-6"
              animate={{ y: [0, -4, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            >
              {/* 外圈光环 */}
              <div
                className="absolute inset-0 rounded-full"
                style={{
                  border: '1px solid rgba(196, 215, 12, 0.15)',
                  transform: 'scale(1.4)',
                }}
              />
              <div
                className="w-24 h-24 sm:w-28 sm:h-28 flex items-center justify-center chamfer"
                style={{
                  backgroundColor: 'rgba(196, 215, 12, 0.06)',
                  border: '2px solid rgba(196, 215, 12, 0.25)',
                }}
              >
                <Glasses size={48} strokeWidth={1} style={{ color: '#C4D70C' }} />
              </div>
              {/* 四角装饰 */}
              <div className="absolute -top-1 -left-1 w-2 h-2" style={{ borderTop: '2px solid #C4D70C', borderLeft: '2px solid #C4D70C' }} />
              <div className="absolute -top-1 -right-1 w-2 h-2" style={{ borderTop: '2px solid #C4D70C', borderRight: '2px solid #C4D70C' }} />
              <div className="absolute -bottom-1 -left-1 w-2 h-2" style={{ borderBottom: '2px solid #C4D70C', borderLeft: '2px solid #C4D70C' }} />
              <div className="absolute -bottom-1 -right-1 w-2 h-2" style={{ borderBottom: '2px solid #C4D70C', borderRight: '2px solid #C4D70C' }} />
            </motion.div>

            <h2
              className="text-xl sm:text-2xl font-black mb-3 text-center"
              style={{ fontFamily: 'var(--font-display)', color: '#FFF8EE' }}
            >
              与 AI 对话
            </h2>
            <p
              className="text-xs sm:text-sm text-center max-w-sm leading-relaxed mb-6"
              style={{ color: '#FFF8EE', opacity: 0.6 }}
            >
              基于 LangGraph 编排的多 Agent 智能助手，
              支持 RAG 检索增强与深度技术讨论
            </p>

            <button
              className="chamfer px-8 py-3 text-xs font-bold tracking-wider relative overflow-hidden lens-reflect flex items-center gap-2"
              style={{
                backgroundColor: 'transparent',
                color: '#C4D70C',
                border: '2px solid #C4D70C',
                fontFamily: 'var(--font-display)',
              }}
              data-cursor-hover
            >
              <Glasses size={14} />
              启动对话
            </button>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
