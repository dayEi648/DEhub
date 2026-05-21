import { Link } from 'react-router-dom'
import { Map, FileText, TrendingUp, ArrowRight } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'

const MOCK_ZONES = [
  {
    id: 1,
    slug: 'frontend',
    zone_name: '前端开发',
    description: 'HTML, CSS, JavaScript, React, Vue 等前端技术讨论区',
    manager: { username: 'FrontendLead' },
    view_count: 15420,
    post_count: 342,
  },
  {
    id: 2,
    slug: 'backend',
    zone_name: '后端开发',
    description: 'Python, Go, Java, Node.js 等后端技术讨论区',
    manager: { username: 'BackendMaster' },
    view_count: 12350,
    post_count: 278,
  },
  {
    id: 3,
    slug: 'ai-ml',
    zone_name: 'AI / 机器学习',
    description: '大语言模型、LangChain、LangGraph、深度学习等技术交流',
    manager: { username: 'AIGuru' },
    view_count: 22100,
    post_count: 567,
  },
  {
    id: 4,
    slug: 'database',
    zone_name: '数据库',
    description: 'PostgreSQL, MySQL, Redis, MongoDB 等数据库技术讨论',
    manager: { username: 'DBAdmin' },
    view_count: 8900,
    post_count: 156,
  },
  {
    id: 5,
    slug: 'devops',
    zone_name: 'DevOps',
    description: 'Docker, Kubernetes, CI/CD, 云原生技术交流',
    manager: { username: 'OpsExpert' },
    view_count: 6700,
    post_count: 98,
  },
  {
    id: 6,
    slug: 'general',
    zone_name: '综合讨论',
    description: '技术之外的话题，职业发展、生活分享等',
    manager: { username: 'CommunityMod' },
    view_count: 32000,
    post_count: 1205,
  },
]

export default function ForumHomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">论坛</h1>
          <p className="mt-1 text-muted-foreground">技术交流、问题讨论与经验分享</p>
        </div>
        <Button>发表新帖</Button>
      </div>

      {/* Zone Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MOCK_ZONES.map(zone => (
          <Link key={zone.id} to={`/forum/${zone.slug}`}>
            <Card className="h-full transition-all hover:border-primary/50 hover:shadow-md group">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="rounded-lg bg-primary/10 p-3">
                    <Map className="h-5 w-5 text-primary" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
                </div>

                <h3 className="font-semibold text-lg">{zone.zone_name}</h3>
                <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{zone.description}</p>

                <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <FileText className="h-3.5 w-3.5" />
                    {zone.post_count} 帖子
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="h-3.5 w-3.5" />
                    {zone.view_count.toLocaleString()} 浏览
                  </span>
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">区主:</span>
                  <Badge variant="outline" className="text-xs">@{zone.manager.username}</Badge>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
