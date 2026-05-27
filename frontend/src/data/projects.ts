/**
 * 作品集静态配置
 *
 * 说明：
 *   - 每新增一个项目，在此数组追加一个对象即可。
 *   - coverGradient 使用 CSS 渐变字符串，无需引入图片资源。
 *   - ECS 公网 IP 通过环境变量 VITE_ECS_IP 注入，不在源码中硬编码。
 */

// 从环境变量读取 ECS 公网 IP，构建时注入
const ECS_IP = import.meta.env.VITE_ECS_IP || 'YOUR_ECS_IP'

export interface Project {
  id: string
  name: string
  coverGradient: string
  coverIcon: string // lucide-react 图标名
  summary: string
  link: string
  tags: string[]
}

export const projects: Project[] = [
  {
    id: 'deepsearch',
    name: '智能深度研究助手',
    coverGradient: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    coverIcon: 'Brain',
    summary:
      '基于 LangGraph + MCP + RAG + Redis 的多 Agent 协作研究系统。输入研究主题，AI 自动完成规划、检索、分析、撰写与审校，最终生成结构化的深度研究报告。',
    link: `http://${ECS_IP}:8080`,
    tags: ['AI', 'LangGraph', 'FastAPI', 'Vue', 'RAG'],
  },
]

/**
 * 获取所有作品列表
 */
export function getProjects(): Project[] {
  return projects
}

/**
 * 根据 ID 查找单个作品
 */
export function getProjectById(id: string): Project | undefined {
  return projects.find((p) => p.id === id)
}
