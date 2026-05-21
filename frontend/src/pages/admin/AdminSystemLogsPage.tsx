import { useState } from 'react'
import { Search, Filter, CheckCircle, Trash2, AlertTriangle, AlertCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import Pagination from '@/components/ui/Pagination'
import Modal from '@/components/ui/Modal'
import { LOG_LEVEL_COLORS, LOG_LEVEL_BADGE_COLORS } from '@/constants'
import { cn, formatDateTime } from '@/lib/utils'
import type { SystemLog, LogLevel } from '@/types'

const MOCK_STATS = {
  total: 128,
  total_unresolved: 5,
  warn_count: 80,
  error_count: 40,
  critical_count: 8,
}

const MOCK_LOGS: SystemLog[] = [
  {
    id: 1,
    level: 'ERROR',
    module: 'app.api.users',
    message: '数据库连接超时',
    exception: 'TimeoutError: Connection to database timed out after 30s\n  File "app/db/session.py", line 45, in get_db\n    yield db\n  File "app/api/users.py", line 32, in login',
    trace_id: 'trace-abc123',
    user_id: 5,
    ip: '192.168.1.100',
    extra: { 'endpoint': '/api/v1/users/login' },
    is_resolved: false,
    resolved_at: null,
    resolved_by: null,
    created_at: '2024-01-15T10:30:00',
  },
  {
    id: 2,
    level: 'WARN',
    module: 'app.services.ai',
    message: 'LLM API 响应较慢，耗时 8.5s',
    exception: null,
    trace_id: 'trace-def456',
    user_id: 3,
    ip: '192.168.1.101',
    extra: { 'model': 'gpt-4', 'latency': 8.5 },
    is_resolved: false,
    resolved_at: null,
    resolved_by: null,
    created_at: '2024-01-15T09:00:00',
  },
  {
    id: 3,
    level: 'CRITICAL',
    module: 'app.core.security',
    message: '检测到异常登录行为',
    exception: null,
    trace_id: 'trace-ghi789',
    user_id: null,
    ip: '10.0.0.50',
    extra: { 'attempts': 15, 'username': 'admin' },
    is_resolved: true,
    resolved_at: '2024-01-15T08:30:00',
    resolved_by: 1,
    created_at: '2024-01-15T08:00:00',
  },
  {
    id: 4,
    level: 'WARN',
    module: 'app.storage.oss',
    message: '上传图片尺寸过大，已自动压缩',
    exception: null,
    trace_id: null,
    user_id: 4,
    ip: '192.168.1.102',
    extra: { 'original_size': 5242880, 'compressed_size': 1048576 },
    is_resolved: true,
    resolved_at: '2024-01-14T16:00:00',
    resolved_by: 1,
    created_at: '2024-01-14T15:45:00',
  },
  {
    id: 5,
    level: 'ERROR',
    module: 'app.graphs.chat',
    message: 'LangGraph 工作流执行失败',
    exception: 'ValueError: Invalid state transition from "thinking" to "error"\n  File "app/graphs/nodes.py", line 89, in process',
    trace_id: 'trace-jkl012',
    user_id: 2,
    ip: '192.168.1.103',
    extra: { 'conversation_id': 42 },
    is_resolved: false,
    resolved_at: null,
    resolved_by: null,
    created_at: '2024-01-14T14:20:00',
  },
]

export default function AdminSystemLogsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterLevel, setFilterLevel] = useState<LogLevel | null>(null)
  const [filterResolved, setFilterResolved] = useState<boolean | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedLog, setSelectedLog] = useState<SystemLog | null>(null)
  const [expandedException, setExpandedException] = useState<number | null>(null)

  const levelIcons: Record<LogLevel, React.ReactNode> = {
    WARN: <AlertTriangle className="h-4 w-4" />,
    ERROR: <AlertCircle className="h-4 w-4" />,
    CRITICAL: <XCircle className="h-4 w-4" />,
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">系统日志监控</h1>
        <p className="text-sm text-muted-foreground">查看和管理系统告警日志</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">日志总数</p>
            <p className="text-2xl font-bold">{MOCK_STATS.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">未处理</p>
            <p className="text-2xl font-bold text-red-500">{MOCK_STATS.total_unresolved}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">WARN</p>
            <p className="text-2xl font-bold text-yellow-500">{MOCK_STATS.warn_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">ERROR / CRITICAL</p>
            <p className="text-2xl font-bold text-red-500">{MOCK_STATS.error_count + MOCK_STATS.critical_count}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="搜索模块或消息..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">级别：</span>
              <button
                onClick={() => setFilterLevel(null)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterLevel === null ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                全部
              </button>
              {(['WARN', 'ERROR', 'CRITICAL'] as LogLevel[]).map(level => (
                <button
                  key={level}
                  onClick={() => setFilterLevel(level)}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-sm transition-colors',
                    filterLevel === level ? LOG_LEVEL_BADGE_COLORS[level] : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  )}
                >
                  {level}
                </button>
              ))}
              <span className="text-sm text-muted-foreground ml-2">状态：</span>
              <button
                onClick={() => setFilterResolved(null)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterResolved === null ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                全部
              </button>
              <button
                onClick={() => setFilterResolved(false)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterResolved === false ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                未处理
              </button>
              <button
                onClick={() => setFilterResolved(true)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterResolved === true ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                已处理
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Batch Actions */}
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" className="gap-1">
          <CheckCircle className="h-4 w-4" />
          批量标记已处理
        </Button>
      </div>

      {/* Logs Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium w-10">
                    <input type="checkbox" className="rounded border-border" />
                  </th>
                  <th className="px-4 py-3 text-left font-medium">级别</th>
                  <th className="px-4 py-3 text-left font-medium">模块</th>
                  <th className="px-4 py-3 text-left font-medium">消息</th>
                  <th className="px-4 py-3 text-left font-medium">IP</th>
                  <th className="px-4 py-3 text-left font-medium">状态</th>
                  <th className="px-4 py-3 text-left font-medium">时间</th>
                  <th className="px-4 py-3 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_LOGS.map(log => (
                  <tr key={log.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3">
                      <input type="checkbox" className="rounded border-border" />
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={cn('gap-1', LOG_LEVEL_COLORS[log.level])}>
                        {levelIcons[log.level]}
                        {log.level}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{log.module}</td>
                    <td className="px-4 py-3 max-w-xs">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="text-left hover:text-primary transition-colors line-clamp-1"
                      >
                        {log.message}
                      </button>
                      {log.exception && (
                        <button
                          onClick={() => setExpandedException(expandedException === log.id ? null : log.id)}
                          className="mt-1 flex items-center gap-1 text-xs text-destructive hover:underline"
                        >
                          {expandedException === log.id ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          异常堆栈
                        </button>
                      )}
                      {expandedException === log.id && log.exception && (
                        <pre className="mt-2 rounded bg-destructive/5 p-2 text-xs text-destructive overflow-x-auto font-mono">
                          {log.exception}
                        </pre>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">{log.ip}</td>
                    <td className="px-4 py-3">
                      {log.is_resolved ? (
                        <Badge variant="outline" className="text-emerald-500 border-emerald-500/20">已处理</Badge>
                      ) : (
                        <Badge variant="outline" className="text-red-500 border-red-500/20">未处理</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-xs whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {!log.is_resolved && (
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-emerald-500" title="标记已处理">
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                        )}
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

      <div className="flex justify-center">
        <Pagination currentPage={currentPage} totalPages={10} onPageChange={setCurrentPage} />
      </div>

      {/* Detail Modal */}
      <Modal open={!!selectedLog} onClose={() => setSelectedLog(null)} title="日志详情">
        {selectedLog && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-muted-foreground">ID</label>
                <p className="text-sm font-mono">{selectedLog.id}</p>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">级别</label>
                <p className="text-sm">
                  <Badge className={LOG_LEVEL_COLORS[selectedLog.level]}>{selectedLog.level}</Badge>
                </p>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">模块</label>
                <p className="text-sm font-mono">{selectedLog.module}</p>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Trace ID</label>
                <p className="text-sm font-mono">{selectedLog.trace_id || '-'}</p>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">用户 ID</label>
                <p className="text-sm font-mono">{selectedLog.user_id || '-'}</p>
              </div>
              <div>
                <label className="text-xs text-muted-foreground">IP</label>
                <p className="text-sm font-mono">{selectedLog.ip || '-'}</p>
              </div>
            </div>
            <div>
              <label className="text-xs text-muted-foreground">消息</label>
              <p className="text-sm mt-1 p-3 rounded bg-muted">{selectedLog.message}</p>
            </div>
            {selectedLog.exception && (
              <div>
                <label className="text-xs text-muted-foreground">异常堆栈</label>
                <pre className="mt-1 p-3 rounded bg-destructive/5 text-destructive text-xs overflow-x-auto font-mono">
                  {selectedLog.exception}
                </pre>
              </div>
            )}
            {selectedLog.extra && (
              <div>
                <label className="text-xs text-muted-foreground">额外信息</label>
                <pre className="mt-1 p-3 rounded bg-muted text-xs overflow-x-auto font-mono">
                  {JSON.stringify(selectedLog.extra, null, 2)}
                </pre>
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setSelectedLog(null)}>关闭</Button>
              {!selectedLog.is_resolved && (
                <Button>标记已处理</Button>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
