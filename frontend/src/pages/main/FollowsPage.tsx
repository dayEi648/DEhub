import { Link } from 'react-router-dom'
import { Map, FileText, TrendingUp, BellOff } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'

const MOCK_FOLLOWS = [
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
    id: 3,
    slug: 'ai-ml',
    zone_name: 'AI / 机器学习',
    description: '大语言模型、LangChain、LangGraph、深度学习等技术交流',
    manager: { username: 'AIGuru' },
    view_count: 22100,
    post_count: 567,
  },
]

export default function FollowsPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">我的关注</h1>
          <p className="mt-1 text-muted-foreground">关注的论坛分区</p>
        </div>
      </div>

      <div className="space-y-3">
        {MOCK_FOLLOWS.map(zone => (
          <Card key={zone.id} className="transition-colors hover:bg-muted/50">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Map className="h-4 w-4 text-primary" />
                    <Link to={`/forum/${zone.slug}`} className="font-semibold hover:text-primary transition-colors">
                      {zone.zone_name}
                    </Link>
                    <Badge variant="outline" className="text-xs">@{zone.manager.username}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{zone.description}</p>
                  <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <FileText className="h-3.5 w-3.5" />
                      {zone.post_count} 帖子
                    </span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="h-3.5 w-3.5" />
                      {zone.view_count.toLocaleString()} 浏览
                    </span>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="gap-1 shrink-0">
                  <BellOff className="h-3.5 w-3.5" />
                  取消关注
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
