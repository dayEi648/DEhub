import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Archive, Bot, ChevronLeft, ChevronRight, Loader2, MessageSquarePlus, Send, ShieldAlert, Trash2 } from 'lucide-react'
import { parseErrorMessage, isAuthError } from '../utils/error'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useNavigate } from 'react-router-dom'
import AppTopNav from '../components/AppTopNav'
import { useLogout } from '../hooks/useLogout'
import { chatWithAI, deleteConversation, getConversationList, getConversationMessages } from '../api/aiChat'
import { formatDateTime } from '../utils/format'
import { getUser } from '../utils/auth'
import type { AIConversationItem, AIMessage } from '../types/aiChat'

const CONVERSATION_PAGE_SIZE = 20
const MESSAGE_PAGE_SIZE = 100

function roleLabel(role: AIMessage['role']) {
  if (role === 'assistant') return 'AI'
  if (role === 'user') return '你'
  if (role === 'system') return 'System'
  return 'Tool'
}

function hasDisplayableContent(message: AIMessage) {
  return message.content.trim().length > 0
}

function isCompactSummaryMessage(message: AIMessage) {
  return Boolean(message.meta && message.meta.compact_summary === true)
}

function isDefaultVisibleMessage(message: AIMessage) {
  if (isCompactSummaryMessage(message)) {
    return true
  }
  if (!hasDisplayableContent(message)) {
    return false
  }
  if (message.role === 'user') {
    return true
  }
  if (message.role === 'assistant') {
    // 包含 tool_calls 的 AIMessage 视为中间决策消息，对普通用户隐藏
    const meta = message.meta
    if (meta && Array.isArray(meta.tool_calls) && meta.tool_calls.length > 0) {
      return false
    }
    return true
  }
  return false
}

export default function AIChatPage() {
  const navigate = useNavigate()
  const handleLogout = useLogout()
  const [conversations, setConversations] = useState<AIConversationItem[]>([])
  const [conversationTotal, setConversationTotal] = useState(0)
  const [conversationsLoading, setConversationsLoading] = useState(true)
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<AIMessage[]>([])
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const [sending, setSending] = useState(false)
  const [newConversationMode, setNewConversationMode] = useState(false)
  const [includeHidden, setIncludeHidden] = useState(false)
  const [panelError, setPanelError] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const skipNextMessagesFetchRef = useRef<number | null>(null)
  const currentUser = getUser()
  const canViewHiddenMessages = (currentUser?.permission ?? 0) >= 1

  const hasMoreConversations = conversations.length < conversationTotal

  const fetchConversations = useCallback(
    async (reset: boolean, skip: number) => {
      setConversationsLoading(true)
      try {
        const res = await getConversationList({
          skip,
          limit: CONVERSATION_PAGE_SIZE,
        })
        const incomingItems = res.data.items || []
        setConversationTotal(res.data.total || 0)
        setConversations((prev) => (reset ? incomingItems : prev.concat(incomingItems)))
      } catch (error) {
        if (!isAuthError(error)) {
          toast.error(parseErrorMessage(error, '对话列表加载失败'))
        }
      } finally {
        setConversationsLoading(false)
      }
    },
    [],
  )

  const fetchMessages = useCallback(async (conversationId: number) => {
    setMessagesLoading(true)
    setPanelError('')
    try {
      const res = await getConversationMessages(conversationId, {
        skip: 0,
        limit: MESSAGE_PAGE_SIZE,
        include_hidden: canViewHiddenMessages ? includeHidden : false,
      })
      setMessages(res.data || [])
    } catch (error) {
      setMessages([])
      const message = parseErrorMessage(error, '消息加载失败')
      setPanelError(message)
      toast.error(message)
    } finally {
      setMessagesLoading(false)
    }
  }, [canViewHiddenMessages, includeHidden])

  useEffect(() => {
    if (!canViewHiddenMessages && includeHidden) {
      setIncludeHidden(false)
    }
  }, [canViewHiddenMessages, includeHidden])

  useEffect(() => {
    void fetchConversations(true, 0)
  }, [fetchConversations])

  useEffect(() => {
    if (!activeConversationId) {
      setMessages([])
      setPanelError('')
      return
    }
    if (skipNextMessagesFetchRef.current === activeConversationId) {
      skipNextMessagesFetchRef.current = null
      return
    }
    void fetchMessages(activeConversationId)
  }, [activeConversationId, fetchMessages])

  useEffect(() => {
    if (activeConversationId || newConversationMode) return
    if (conversations.length > 0) {
      setActiveConversationId(conversations[0].id)
    }
  }, [conversations, activeConversationId, newConversationMode])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, sending])

  const displayMessages = useMemo(() => {
    if (canViewHiddenMessages && includeHidden) {
      return messages.filter(hasDisplayableContent)
    }
    return messages.filter(isDefaultVisibleMessage)
  }, [canViewHiddenMessages, includeHidden, messages])

  const handleSendMessage = async () => {
    const userInput = inputValue.trim()
    if (!userInput) {
      toast.warning('请输入内容后再发送')
      return
    }
    if (userInput.length > 2000) {
      toast.warning('输入内容不能超过 2000 字')
      return
    }

    setSending(true)
    setInputValue('')

    const optimisticUserMessage: AIMessage = {
      id: -Date.now(),
      conversation_id: activeConversationId ?? -1,
      role: 'user',
      content: userInput,
      meta: null,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => prev.concat(optimisticUserMessage))

    try {
      const res = await chatWithAI({
        conversation_id: activeConversationId ?? undefined,
        user_input: userInput,
      })
      const resolvedConversationId = res.data.conversation_id
      const optimisticAssistantMessage: AIMessage = {
        id: -(Date.now() + 1),
        conversation_id: resolvedConversationId,
        role: 'assistant',
        content: res.data.response,
        meta: null,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) =>
        prev
          .map((message) =>
            message.id === optimisticUserMessage.id
              ? { ...message, conversation_id: resolvedConversationId }
              : message,
          )
          .concat(optimisticAssistantMessage),
      )
      setNewConversationMode(false)
      if (activeConversationId !== resolvedConversationId) {
        skipNextMessagesFetchRef.current = resolvedConversationId
      }
      setActiveConversationId(resolvedConversationId)
      await fetchConversations(true, 0)
    } catch (error) {
      const message = parseErrorMessage(error, '发送失败，请稍后重试')
      toast.error(message)
      await fetchConversations(true, 0)
      if (activeConversationId) {
        await fetchMessages(activeConversationId)
      } else {
        setMessages([])
      }
    } finally {
      setSending(false)
    }
  }

  const handleDeleteConversation = async (conversationId: number) => {
    const target = conversations.find((item) => item.id === conversationId)
    const confirmText = target ? `确定删除对话「${target.title}」吗？` : '确定删除该对话吗？'
    if (!window.confirm(confirmText)) return

    try {
      await deleteConversation(conversationId)
      toast.success('对话已删除')
      if (conversationId === activeConversationId) {
        setNewConversationMode(false)
        setActiveConversationId(null)
        setMessages([])
      }
      await fetchConversations(true, 0)
    } catch (error) {
      if (!isAuthError(error)) {
        toast.error(parseErrorMessage(error, '删除失败，请稍后重试'))
      }
    }
  }

  return (
    <div className="ai-chat-page">
      <AppTopNav onLogout={handleLogout} />

      <main className={`ai-chat-main ${sidebarCollapsed ? 'has-collapsed-sidebar' : ''}`}>
        <aside className={`ai-chat-sidebar ${sidebarCollapsed ? 'is-collapsed' : ''}`}>
          <div className="ai-chat-sidebar__top">
            <div className="ai-chat-sidebar__title">
              <Bot size={17} />
              <span>AI 助手</span>
            </div>
            <button
              type="button"
              className="ai-chat-sidebar__toggle"
              onClick={() => setSidebarCollapsed(true)}
              aria-label="收起侧边栏"
            >
              <ChevronLeft size={14} />
            </button>
            <button
              type="button"
              className="ai-chat-sidebar__new-button"
              disabled={sending}
              onClick={() => {
                if (sending) return
                setNewConversationMode(true)
                setActiveConversationId(null)
                setMessages([])
                setPanelError('')
              }}
            >
              <MessageSquarePlus size={14} />
              新建对话
            </button>
          </div>

          <div className="ai-chat-sidebar__list">
            {conversations.map((conversation) => {
              const isActive = conversation.id === activeConversationId
              return (
                <div
                  key={conversation.id}
                  className={`ai-chat-sidebar__item ${isActive ? 'is-active' : ''}`}
                  aria-disabled={sending}
                  onClick={() => {
                    if (sending) return
                    setNewConversationMode(false)
                    setActiveConversationId(conversation.id)
                  }}
                  onKeyDown={(event) => {
                    if (sending) return
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      setNewConversationMode(false)
                      setActiveConversationId(conversation.id)
                    }
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="ai-chat-sidebar__item-header">
                    <span className="ai-chat-sidebar__item-title">{conversation.title}</span>
                    <span className="ai-chat-sidebar__item-time">
                      {formatDateTime(conversation.last_message_at || conversation.updated_at)}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="ai-chat-sidebar__delete"
                    disabled={sending}
                    onClick={(event) => {
                      event.stopPropagation()
                      if (sending) return
                      void handleDeleteConversation(conversation.id)
                    }}
                    aria-label={`删除对话 ${conversation.title}`}
                  >
                    <Trash2 size={13} />
                    删除
                  </button>
                </div>
              )
            })}

            {!conversationsLoading && conversations.length === 0 && (
              <div className="ai-chat-sidebar__empty">暂无历史对话</div>
            )}
          </div>

          <div className="ai-chat-sidebar__footer">
            <button
              type="button"
              className="ai-chat-sidebar__loadmore"
              disabled={sending || conversationsLoading || !hasMoreConversations}
              onClick={() => {
                if (sending) return
                if (!hasMoreConversations) return
                void fetchConversations(false, conversations.length)
              }}
            >
              {conversationsLoading ? '加载中...' : hasMoreConversations ? '加载更多' : '没有更多了'}
            </button>
          </div>
        </aside>

        <section className="ai-chat-panel">
          <header className="ai-chat-panel__header">
            <div className="ai-chat-panel__header-left">
              {sidebarCollapsed && (
                <button
                  type="button"
                  className="ai-chat-panel__sidebar-toggle"
                  onClick={() => setSidebarCollapsed(false)}
                  aria-label="展开侧边栏"
                >
                  <ChevronRight size={16} />
                </button>
              )}
              <h1 className="ai-chat-panel__title">AI 聊天助手</h1>
            </div>

            <div className="ai-chat-panel__switches">
              {canViewHiddenMessages && (
                <label>
                  <input
                    type="checkbox"
                    checked={includeHidden}
                    onChange={(event) => setIncludeHidden(event.target.checked)}
                  />
                  包含隐藏消息
                </label>
              )}
              {canViewHiddenMessages && (
                <button
                  type="button"
                  className="ai-chat-panel__admin-link"
                  onClick={() => navigate('/admin/openapi-knowledge')}
                >
                  接口知识库
                </button>
              )}
            </div>
          </header>

          <div className="ai-chat-panel__messages">
            {messagesLoading ? (
              <div className="ai-chat-panel__status">正在加载消息...</div>
            ) : panelError ? (
              <div className="ai-chat-panel__status is-error">
                <ShieldAlert size={16} />
                {panelError}
              </div>
            ) : displayMessages.length === 0 ? (
              <div className="ai-chat-panel__status">暂无消息，开始提问吧。</div>
            ) : (
              <>
                {displayMessages.map((message) => {
                  if (isCompactSummaryMessage(message)) {
                    return (
                      <article
                        key={message.id}
                        className="ai-chat-bubble ai-chat-bubble--compact"
                      >
                        <Archive size={14} />
                        <span>{message.content}</span>
                        <time>{formatDateTime(message.created_at)}</time>
                      </article>
                    )
                  }
                  return (
                    <article
                      key={message.id}
                      className={`ai-chat-bubble ai-chat-bubble--${message.role} animate-fadeIn`}
                      style={{ animationDuration: '0.25s' }}
                    >
                      <div className="ai-chat-bubble__meta">
                        <strong>{roleLabel(message.role)}</strong>
                        <span>{formatDateTime(message.created_at)}</span>
                      </div>
                      {message.role === 'assistant' ? (
                        <div className="ai-chat-bubble__markdown">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <p className="ai-chat-bubble__plain">{message.content}</p>
                      )}
                    </article>
                  )
                })}
                {sending && (
                  <article className="ai-chat-bubble ai-chat-bubble--thinking">
                    <Loader2 size={16} className="ai-chat-thinking__spinner" />
                    <span>思考中...</span>
                  </article>
                )}
              </>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="ai-chat-panel__composer">
            <textarea
              data-testid="ai-chat-input"
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              placeholder="输入你的问题，支持多行。按 Ctrl+Enter 快速发送。"
              disabled={sending}
              maxLength={2000}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && event.ctrlKey) {
                  event.preventDefault()
                  void handleSendMessage()
                }
              }}
            />
            <div className="ai-chat-panel__composer-footer">
              <span className="ai-chat-panel__counter">{inputValue.length}/2000</span>
              <button
                data-testid="ai-chat-send"
                type="button"
                className="ripple-container"
                onClick={() => {
                  void handleSendMessage()
                }}
                disabled={sending || !inputValue.trim()}
                style={{
                  transition: 'background-color 0.2s ease, transform 0.1s ease',
                }}
                onMouseDown={(e) => {
                  if (!sending && inputValue.trim()) {
                    e.currentTarget.style.transform = 'scale(0.95)'
                  }
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.transform = 'scale(1)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)'
                }}
              >
                <Send size={14} />
                {sending ? '发送中...' : '发送'}
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
