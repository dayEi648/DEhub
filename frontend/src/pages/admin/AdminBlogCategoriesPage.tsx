import { useState } from 'react'
import { Plus, Edit, Trash2, FileText } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'

const MOCK_CATEGORIES = [
  { id: 1, name: '前端开发', slug: 'frontend', description: 'HTML, CSS, JavaScript, React, Vue 等', post_count: 45 },
  { id: 2, name: '后端开发', slug: 'backend', description: 'Python, Go, Java, Node.js 等', post_count: 32 },
  { id: 3, name: '数据库', slug: 'database', description: 'PostgreSQL, MySQL, Redis 等', post_count: 18 },
  { id: 4, name: 'AI', slug: 'ai', description: '大语言模型、机器学习、深度学习', post_count: 28 },
  { id: 5, name: '运维', slug: 'devops', description: 'Docker, Kubernetes, CI/CD', post_count: 12 },
]

export default function AdminBlogCategoriesPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [editCategory, setEditCategory] = useState<typeof MOCK_CATEGORIES[0] | null>(null)

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold">博客分类管理</h1>
          <p className="text-sm text-muted-foreground">管理博客文章分类</p>
        </div>
        <Button className="gap-1" onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4" />
          新建分类
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">ID</th>
                  <th className="px-4 py-3 text-left font-medium">名称</th>
                  <th className="px-4 py-3 text-left font-medium">Slug</th>
                  <th className="px-4 py-3 text-left font-medium">描述</th>
                  <th className="px-4 py-3 text-left font-medium">文章数</th>
                  <th className="px-4 py-3 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_CATEGORIES.map(cat => (
                  <tr key={cat.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground">{cat.id}</td>
                    <td className="px-4 py-3 font-medium">{cat.name}</td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{cat.slug}</td>
                    <td className="px-4 py-3 text-muted-foreground">{cat.description}</td>
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1 text-muted-foreground">
                        <FileText className="h-3.5 w-3.5" />
                        {cat.post_count}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setEditCategory(cat)}>
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
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="新建分类">
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">名称</label>
            <Input placeholder="分类名称" className="mt-1" />
          </div>
          <div>
            <label className="text-sm font-medium">Slug</label>
            <Input placeholder="url-friendly-name" className="mt-1" />
            <p className="text-xs text-muted-foreground mt-1">留空将自动根据名称生成</p>
          </div>
          <div>
            <label className="text-sm font-medium">描述</label>
            <Input placeholder="分类描述（可选）" className="mt-1" />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setShowCreate(false)}>取消</Button>
            <Button>创建</Button>
          </div>
        </div>
      </Modal>

      {/* Edit Modal */}
      <Modal open={!!editCategory} onClose={() => setEditCategory(null)} title="编辑分类">
        {editCategory && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">名称</label>
              <Input defaultValue={editCategory.name} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">Slug</label>
              <Input defaultValue={editCategory.slug} className="mt-1" />
            </div>
            <div>
              <label className="text-sm font-medium">描述</label>
              <Input defaultValue={editCategory.description} className="mt-1" />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditCategory(null)}>取消</Button>
              <Button>保存</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
