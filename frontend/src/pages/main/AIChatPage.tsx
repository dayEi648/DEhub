import { useState, useRef, useEffect } from 'react'
import { Send, Plus, Trash2, MessageSquare, Bot, User, ChevronLeft } from 'lucide-react'
import Button from '@/components/ui/Button'
import Textarea from '@/components/ui/Textarea'
import { cn } from '@/lib/utils'

interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface Conversation {
  id: number
  title: string
  messages: ChatMessage[]
}

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: 1,
    title: 'React 19 新特性讨论',
    messages: [
      { id: 1, role: 'user', content: 'React 19 的 use() Hook 和 useEffect 有什么区别？', created_at: '2024-01-15T10:00:00' },
      { id: 2, role: 'assistant', content: 'use() 和 useEffect 是两个完全不同的 Hook：\n\n1. **use()** 可以在条件语句中使用，而 useEffect 不行\n2. **use()** 用于读取 Promise 或 Context，会触发 Suspense\n3. **useEffect** 用于副作用处理，不会阻塞渲染\n\n简单来说，use() 是同步读取异步数据的方式，而 useEffect 是处理副作用的钩子。', created_at: '2024-01-15T10:00:05' },
    ],
  },
  {
    id: 2,
    title: 'FastAPI 数据库设计',
    messages: [
      { id: 3, role: 'user', content: 'FastAPI 里怎么设计分层架构比较好？', created_at: '2024-01-14T15:00:00' },
      { id: 4, role: 'assistant', content: '推荐的分层架构：\n\n- **API Layer**: 路由定义、请求校验\n- **Service Layer**: 业务逻辑\n- **CRUD Layer**: 数据库操作\n- **Model Layer**: ORM 模型定义\n\n这样职责清晰，便于测试和维护。', created_at: '2024-01-14T15:00:03' },
    ],
  },
  {
    id: 3,
    title: 'PostgreSQL 性能优化',
    messages: [],
  },
]

export default function AIChatPage() {
  const [conversations, setConversations] = useState(MOCK_CONVERSATIONS)
  const [activeId, setActiveId] = useState(1)
  const [input, setInput] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const activeConversation = conversations.find(c => c.id === activeId)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConversation?.messages])

  const handleSend = () => {
    if (!input.trim()) return
    // Mock send - would call API here
    setInput('')
  }

  const handleNewConversation = () => {
    const newConv: Conversation = {
      id: Date.now(),
      title: '新对话',
      messages: [],
    }
    setConversations([newConv, ...conversations])
    setActiveId(newConv.id)
  }

  const handleDeleteConversation = (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const filtered = conversations.filter(c => c.id !== id)
    setConversations(filtered)
    if (activeId === id && filtered.length > 0) {
      setActiveId(filtered[0].id)
    }
  }

  return (
    <div className="flex h-[calc(100svh-3.5rem)] overflow-hidden">
      {/* Sidebar */}
      <div
        className={cn(
          'flex flex-col border-r border-border bg-card transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
        )}
      >
        <div className="p-3">
          <Button variant="outline" className="w-full gap-1" onClick={handleNewConversation}>
            <Plus className="h-4 w-4" />
            新建对话
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
          {conversations.map(conv => (
            <button
              key={conv.id}
              onClick={() => setActiveId(conv.id)}
              className={cn(
                'w-full flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors group',
                activeId === conv.id
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              <MessageSquare className="h-4 w-4 shrink-0" />
              <span className="flex-1 truncate text-left">{conv.title}</span>
              <button
                onClick={(e) => handleDeleteConversation(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/10 hover:text-destructive transition-all"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col min-w-0 bg-background">
        {/* Header */}
        <div className="flex h-14 items-center border-b border-border px-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="mr-3 rounded-md p-1.5 text-muted-foreground hover:bg-muted lg:hidden"
          >
            <ChevronLeft className={cn('h-4 w-4 transition-transform', !sidebarOpen && 'rotate-180')} />
          </button>
          <h2 className="text-sm font-semibold truncate">
            {activeConversation?.title || '选择或创建一个对话'}
          </h2>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {activeConversation?.messages.length === 0 && (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <div className="text-center">
                <Bot className="h-10 w-10 mx-auto mb-3 text-primary/50" />
                <p>发送消息开始对话</p>
              </div>
            </div>
          )}
          {activeConversation?.messages.map(msg => (
            <div
              key={msg.id}
              className={cn(
                'flex gap-3 animate-fade-in',
                msg.role === 'user' ? 'flex-row-reverse' : ''
              )}
            >
              <div className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                msg.role === 'assistant' ? 'bg-primary/10 text-primary' : 'bg-muted text-foreground'
              )}>
                {msg.role === 'assistant' ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
              </div>
              <div className={cn(
                'max-w-[80%] rounded-lg px-4 py-2.5 text-sm leading-relaxed',
                msg.role === 'assistant'
                  ? 'bg-card border border-border text-foreground'
                  : 'bg-primary text-primary-foreground'
              )}>
                <div className="whitespace-pre-line">{msg.content}</div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border p-4">
          <div className="mx-auto max-w-3xl flex gap-2">
            <Textarea
              placeholder="输入消息..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              className="min-h-[48px] max-h-[160px] resize-none"
              rows={1}
            />
            <Button size="icon" onClick={handleSend} className="shrink-0 h-12 w-12">
              <Send className="h-4 w-4" />
            </Button>
          </div>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            AI 生成的内容仅供参考，请自行验证准确性
          </p>
        </div>
      </div>
    </div>
  )
}
