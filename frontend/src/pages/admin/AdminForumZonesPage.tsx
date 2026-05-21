import { useState } from 'react'
import { Plus, Edit, Trash2, Users } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'


const MOCK_ZONES = [
  { id: 1, slug: 'frontend', zone_name: '前端开发', description: 'HTML, CSS, JavaScript, React, Vue 等前端技术讨论区', manager: { username: 'FrontendLead' }, view_count: 15420, created_at: '2024-01-01T00:00:00' },
  { id: 2, slug: 'backend', zone_name: '后端开发', description: 'Python, Go, Java, Node.js 等后端技术讨论区', manager: { username: 'BackendMaster' }, view_count: 12350, created_at: '2024-01-02T00:00:00' },
  { id: 3, slug: 'ai-ml', zone_name: 'AI / 机器学习', description: '大语言模型、LangChain、LangGraph、深度学习', manager: { username: 'AIGuru' }, view_count: 22100, created_at: '2024-01-03T00:00:00' },
  { id: 4, slug: 'database', zone_name: '数据库', description: 'PostgreSQL, MySQL, Redis, MongoDB', manager: { username: 'DBAdmin' }, view_count: 8900, created_at: '2024-01-04T00:00:00' },
]

export default function AdminForumZonesPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [editZone, setEditZone] = useState<typeof MOCK_ZONES[0] | null>(null)

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold">论坛分区管理</h1>
          <p className="text-sm text-muted-foreground">管理论坛分区与区主</p>
        </div>
        <Button className="gap-1" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          新建分区
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">ID</th>
                  <th className="px-4 py-3 text-left font-medium">分区名称</th>
                  <th className="px-4 py-3 text-left font-medium">Slug</th>
                  <th className="px-4 py-3 text-left font-medium">描述</th>
                  <th className="px-4 py-3 text-left font-medium">区主</th>
                  <th className="px-4 py-3 text-left font-medium">浏览量</th>
                  <th className="px-4 py-3 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_ZONES.map(zone => (
                  <tr key={zone.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground">{zone.id}</td>
                    <td className="px-4 py-3 font-medium">{zone.zone_name}</td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{zone.slug}</td>
                    <td className="px-4 py-3 text-muted-foreground max-w-xs truncate">{zone.description}</td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1 text-sm">
                        <Users className="h-3.5 w-3.5 text-muted-foreground" />
                        {zone.manager.username}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{zone.view_count.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setEditZone(zone)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="新建分区">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">分区名称</label>
            <Input placeholder="分区名称" className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">Slug</label>
            <Input placeholder="url-friendly-name" className="mt-1" />
            <p className="text-xs text-muted-foreground mt-1">留空将自动根据名称生成</p>
          </div>
          <div>
            <label className="text-sm font-medium">描述</label>
            <Input placeholder="分区描述（可选）" className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">区主 ID</label>
            <Input placeholder="留空默认设为当前用户" className="mt-1" />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowCreate(false)}>取消</Button>
            <Button>创建</Button>
          </div>
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal open={!!editZone} onClose={() => setEditZone(null)} title="编辑分区">
        {editZone && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">分区名称</label>
              <Input defaultValue={editZone.zone_name} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">Slug</label>
              <Input defaultValue={editZone.slug} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">描述</label>
              <Input defaultValue={editZone.description} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">区主 ID</label>
              <Input defaultValue={editZone.manager.username} className="mt-1" />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditZone(null)}>取消</Button>
              <Button>保存</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
