import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { isAxiosError } from 'axios'
import { Database, FileJson2, LoaderCircle, RefreshCw, Search, Trash2, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { parseErrorMessage } from '../../utils/error'
import { formatDateTime } from '../../utils/format'
import {
  deleteOpenAPIDocument,
  deleteOpenAPIEndpoint,
  getOpenAPIDocument,
  getOpenAPIDocuments,
  getOpenAPIEndpoints,
  searchOpenAPIKnowledge,
  uploadOpenAPIDocument,
} from '../../api/openapiKnowledge'
import { getUser } from '../../utils/auth'
import type {
  OpenAPIDocument,
  OpenAPIDocumentStatus,
  OpenAPIEndpoint,
  OpenAPISearchResult,
} from '../../types/openapiKnowledge'

const MAX_UPLOAD_SIZE = 10 * 1024 * 1024
const DOCUMENT_PAGE_SIZE = 20
const ENDPOINT_PAGE_SIZE = 50
const POLL_INTERVAL_MS = 2000
const POLL_TIMEOUT_MS = 5 * 60 * 1000

function documentStatusText(status: OpenAPIDocumentStatus) {
  if (status === 'pending') return '等待解析'
  if (status === 'processing') return '处理中'
  if (status === 'completed') return '已完成'
  return '失败'
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

export default function OpenAPIKnowledgePage() {
  const currentUser = getUser()
  const isAdmin = (currentUser?.permission ?? 0) >= 1

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)

  const [documents, setDocuments] = useState<OpenAPIDocument[]>([])
  const [documentTotal, setDocumentTotal] = useState(0)
  const [documentSkip, setDocumentSkip] = useState(0)
  const [documentStatusFilter, setDocumentStatusFilter] = useState<'' | OpenAPIDocumentStatus>('')
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [deletingDocumentIds, setDeletingDocumentIds] = useState<number[]>([])
  const [pollingDocumentId, setPollingDocumentId] = useState<number | null>(null)

  const [endpointItems, setEndpointItems] = useState<OpenAPIEndpoint[]>([])
  const [endpointTotal, setEndpointTotal] = useState(0)
  const [endpointSkip, setEndpointSkip] = useState(0)
  const [endpointDocumentIdFilter, setEndpointDocumentIdFilter] = useState<number | ''>('')
  const [endpointMethodFilter, setEndpointMethodFilter] = useState('')
  const [endpointTagFilter, setEndpointTagFilter] = useState('')
  const [endpointsLoading, setEndpointsLoading] = useState(false)
  const [deletingEndpointIds, setDeletingEndpointIds] = useState<number[]>([])
  const [expandedEndpointIds, setExpandedEndpointIds] = useState<number[]>([])

  const [searchQ, setSearchQ] = useState('')
  const [searchTopK, setSearchTopK] = useState(5)
  const [searchMethod, setSearchMethod] = useState('')
  const [searchDocumentId, setSearchDocumentId] = useState<number | ''>('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [searchResults, setSearchResults] = useState<OpenAPISearchResult[]>([])

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const pollTimerRef = useRef<number | null>(null)
  const pollStartedAtRef = useRef(0)
  const pollRequestRef = useRef(0)
  const pollAbortRef = useRef<AbortController | null>(null)
  const documentRequestRef = useRef(0)
  const endpointRequestRef = useRef(0)
  const searchRequestRef = useRef(0)

  const hasPrevDocumentPage = documentSkip > 0
  const hasNextDocumentPage = documentSkip + DOCUMENT_PAGE_SIZE < documentTotal
  const hasPrevEndpointPage = endpointSkip > 0
  const hasNextEndpointPage = endpointSkip + ENDPOINT_PAGE_SIZE < endpointTotal

  const documentOptions = useMemo(
    () => documents.map((doc) => ({ value: doc.id, label: `${doc.filename} (#${doc.id})` })),
    [documents],
  )

  const clearSelectedFile = useCallback(() => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current)
      pollTimerRef.current = null
    }
    pollAbortRef.current?.abort()
    pollAbortRef.current = null
    setPollingDocumentId(null)
  }, [])

  const fetchDocuments = useCallback(async (overrides?: { skip?: number; status?: '' | OpenAPIDocumentStatus }) => {
    const skip = overrides?.skip ?? documentSkip
    const status = overrides?.status !== undefined ? overrides.status : documentStatusFilter
    const requestId = ++documentRequestRef.current
    setDocumentsLoading(true)
    try {
      const res = await getOpenAPIDocuments({
        skip,
        limit: DOCUMENT_PAGE_SIZE,
        ...(status ? { status } : {}),
      })
      if (requestId !== documentRequestRef.current) return
      setDocuments(res.data.items)
      setDocumentTotal(res.data.total)
    } catch (error) {
      if (requestId !== documentRequestRef.current) return
      toast.error(parseErrorMessage(error, '文档列表加载失败'))
    } finally {
      if (requestId === documentRequestRef.current) {
        setDocumentsLoading(false)
      }
    }
  }, [documentSkip, documentStatusFilter])

  const fetchEndpoints = useCallback(async () => {
    const requestId = ++endpointRequestRef.current
    setEndpointsLoading(true)
    try {
      const res = await getOpenAPIEndpoints({
        skip: endpointSkip,
        limit: ENDPOINT_PAGE_SIZE,
        ...(endpointDocumentIdFilter !== '' ? { document_id: endpointDocumentIdFilter } : {}),
        ...(endpointMethodFilter ? { method: endpointMethodFilter.toUpperCase() } : {}),
        ...(endpointTagFilter ? { tag: endpointTagFilter } : {}),
      })
      if (requestId !== endpointRequestRef.current) return
      setEndpointItems(res.data.items)
      setEndpointTotal(res.data.total)
    } catch (error) {
      if (requestId !== endpointRequestRef.current) return
      toast.error(parseErrorMessage(error, '端点列表加载失败'))
    } finally {
      if (requestId === endpointRequestRef.current) {
        setEndpointsLoading(false)
      }
    }
  }, [endpointDocumentIdFilter, endpointMethodFilter, endpointSkip, endpointTagFilter])

  const pollDocumentStatus = useCallback((documentId: number) => {
    const pollId = ++pollRequestRef.current
    stopPolling()
    setPollingDocumentId(documentId)
    pollStartedAtRef.current = Date.now()

    const runPoll = async () => {
      if (pollId !== pollRequestRef.current) return
      const elapsed = Date.now() - pollStartedAtRef.current
      if (elapsed > POLL_TIMEOUT_MS) {
        stopPolling()
        toast.warning('解析状态轮询超时，请稍后手动刷新文档列表')
        return
      }

      const controller = new AbortController()
      pollAbortRef.current = controller

      try {
        const res = await getOpenAPIDocument(documentId, controller.signal)
        if (pollId !== pollRequestRef.current) return

        setDocuments((prev) =>
          prev.map((doc) => (doc.id === documentId ? res.data : doc)),
        )

        if (res.data.status === 'completed') {
          stopPolling()
          toast.success('知识库文档解析完成')
          await Promise.all([fetchDocuments(), fetchEndpoints()])
          return
        }
        if (res.data.status === 'failed') {
          stopPolling()
          toast.error(res.data.error_message || '文档解析失败')
          await fetchDocuments()
          return
        }

        pollTimerRef.current = window.setTimeout(() => {
          void runPoll()
        }, POLL_INTERVAL_MS)
      } catch (error) {
        if (controller.signal.aborted) return
        toast.error(parseErrorMessage(error, '轮询文档状态失败'))
        stopPolling()
      }
    }

    void runPoll()
  }, [fetchDocuments, fetchEndpoints, stopPolling])

  useEffect(() => {
    if (!isAdmin) return
    void fetchDocuments()
  }, [fetchDocuments, isAdmin])

  useEffect(() => {
    if (!isAdmin) return
    void fetchEndpoints()
  }, [fetchEndpoints, isAdmin])

  useEffect(() => () => stopPolling(), [stopPolling])

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.warning('请先选择 OpenAPI 文件')
      return
    }
    if (!/\.(json|yaml|yml)$/i.test(selectedFile.name)) {
      toast.warning('仅支持 .json / .yaml / .yml 文件')
      clearSelectedFile()
      return
    }
    if (selectedFile.size <= 0) {
      toast.warning('文件为空，请重新选择')
      clearSelectedFile()
      return
    }
    if (selectedFile.size > MAX_UPLOAD_SIZE) {
      toast.warning('文件超过 10MB 限制')
      clearSelectedFile()
      return
    }

    setUploading(true)
    try {
      const res = await uploadOpenAPIDocument(selectedFile)
      toast.success('上传成功，已开始后台解析')
      toast.message('若重复上传相同文档，将覆盖旧文档与端点向量')
      clearSelectedFile()
      setSearchResults([])
      setHasSearched(false)
      await fetchDocuments({ skip: 0 })
      setDocumentSkip(0)
      pollDocumentStatus(res.data.document_id)
    } catch (error) {
      toast.error(parseErrorMessage(error, '上传失败'))
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteDocument = async (doc: OpenAPIDocument) => {
    if (doc.status === 'pending' || doc.status === 'processing') {
      toast.warning('处理中或等待中的文档暂不允许删除')
      return
    }
    if (deletingDocumentIds.includes(doc.id)) return
    if (!window.confirm(`确认删除文档「${doc.filename} (#${doc.id})」吗？`)) return

    setDeletingDocumentIds((prev) => prev.concat(doc.id))
    try {
      await deleteOpenAPIDocument(doc.id)
      toast.success('文档已删除')
      if (pollingDocumentId === doc.id) {
        stopPolling()
      }
      await Promise.all([fetchDocuments(), fetchEndpoints()])
      setSearchResults([])
      setHasSearched(false)
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 404) {
        toast.success('文档已删除')
        if (pollingDocumentId === doc.id) {
          stopPolling()
        }
        await Promise.all([fetchDocuments(), fetchEndpoints()])
        setSearchResults([])
        setHasSearched(false)
      } else {
        toast.error(parseErrorMessage(error, '删除文档失败'))
      }
    } finally {
      setDeletingDocumentIds((prev) => prev.filter((id) => id !== doc.id))
    }
  }

  const handleDeleteEndpoint = async (endpoint: OpenAPIEndpoint) => {
    if (deletingEndpointIds.includes(endpoint.id)) return
    if (!window.confirm(`确认删除端点 ${endpoint.method} ${endpoint.path} 吗？`)) return

    setDeletingEndpointIds((prev) => prev.concat(endpoint.id))
    try {
      await deleteOpenAPIEndpoint(endpoint.id)
      toast.success('端点已删除')
      await Promise.all([fetchEndpoints(), fetchDocuments()])
      setSearchResults((prev) => prev.filter((item) => item.id !== endpoint.id))
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 404) {
        toast.success('端点已删除')
        await Promise.all([fetchEndpoints(), fetchDocuments()])
        setSearchResults((prev) => prev.filter((item) => item.id !== endpoint.id))
      } else {
        toast.error(parseErrorMessage(error, '删除端点失败'))
      }
    } finally {
      setDeletingEndpointIds((prev) => prev.filter((id) => id !== endpoint.id))
    }
  }

  const handleSearch = async () => {
    const q = searchQ.trim()
    if (!q) {
      toast.warning('请输入检索关键词')
      return
    }
    setHasSearched(true)
    const requestId = ++searchRequestRef.current
    setSearchLoading(true)
    try {
      const res = await searchOpenAPIKnowledge({
        q,
        top_k: searchTopK,
        ...(searchMethod ? { method: searchMethod.toUpperCase() } : {}),
        ...(searchDocumentId !== '' ? { document_id: searchDocumentId } : {}),
      })
      if (requestId !== searchRequestRef.current) return
      setSearchResults(res.data.items)
      if (res.data.total === 0) {
        toast.message('当前知识库未找到相关接口')
      }
    } catch (error) {
      if (requestId !== searchRequestRef.current) return
      toast.error(parseErrorMessage(error, '检索失败'))
    } finally {
      if (requestId === searchRequestRef.current) {
        setSearchLoading(false)
      }
    }
  }

  const toggleExpanded = (endpointId: number) => {
    setExpandedEndpointIds((prev) =>
      prev.includes(endpointId)
        ? prev.filter((id) => id !== endpointId)
        : prev.concat(endpointId),
    )
  }

  if (!isAdmin) {
    return (
      <div className="openapi-knowledge-page">
        <div className="openapi-knowledge-card">
          <h1>权限不足</h1>
          <p>当前账号无权访问此页面。</p>
        </div>
      </div>
    )
  }

  return (
    <div className="openapi-knowledge-page">
      <header className="openapi-knowledge-header">
        <div className="openapi-knowledge-header__title">
          <Database size={22} />
          <div>
            <h1>OpenAPI 知识库</h1>
            <p>上传文档后将更新共享知识库，供管理员 AI 对话调用。</p>
          </div>
        </div>
        <button
          type="button"
          className="openapi-knowledge-refresh"
          onClick={() => {
            void Promise.all([fetchDocuments(), fetchEndpoints()])
          }}
          disabled={documentsLoading || endpointsLoading}
        >
          <RefreshCw size={14} />
          刷新
        </button>
      </header>

      <section className="openapi-knowledge-card openapi-knowledge-upload">
        <h2>
          <Upload size={16} />
          文档上传
        </h2>
        <p>支持 `.json / .yaml / .yml`，文件大小不超过 10MB。重复文件会覆盖旧文档及端点向量。</p>
        <div className="openapi-knowledge-upload__row">
          <input
            type="file"
            ref={fileInputRef}
            accept=".json,.yaml,.yml"
            onChange={(event) => {
              const file = event.target.files?.[0] || null
              setSelectedFile(file)
            }}
            disabled={uploading}
          />
          <button
            type="button"
            className="openapi-knowledge-primary-button"
            onClick={() => {
              void handleUpload()
            }}
            disabled={uploading || !selectedFile}
          >
            {uploading ? <LoaderCircle size={14} className="spin" /> : <Upload size={14} />}
            {uploading ? '上传中...' : '上传并解析'}
          </button>
        </div>
        {selectedFile && (
          <div className="openapi-knowledge-upload__meta">
            <FileJson2 size={14} />
            <span>{selectedFile.name}</span>
            <span>{formatFileSize(selectedFile.size)}</span>
          </div>
        )}
        {pollingDocumentId && (
          <div className="openapi-knowledge-upload__polling">
            <LoaderCircle size={14} className="spin" />
            正在轮询文档 #{pollingDocumentId} 解析状态...
          </div>
        )}
      </section>

      <div className="openapi-knowledge-grid">
        <section className="openapi-knowledge-card">
          <div className="openapi-knowledge-card__header">
            <h2>文档列表</h2>
            <div className="openapi-knowledge-card__actions">
              <select
                value={documentStatusFilter}
                onChange={(event) => {
                  setDocumentStatusFilter(event.target.value as '' | OpenAPIDocumentStatus)
                  setDocumentSkip(0)
                }}
              >
                <option value="">全部状态</option>
                <option value="pending">pending</option>
                <option value="processing">processing</option>
                <option value="completed">completed</option>
                <option value="failed">failed</option>
              </select>
            </div>
          </div>

          <div className="openapi-knowledge-table-wrap">
            <table className="openapi-knowledge-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>文件名</th>
                  <th>状态</th>
                  <th>端点/分片</th>
                  <th>创建时间</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {documentsLoading ? (
                  <tr>
                    <td colSpan={7} className="openapi-knowledge-empty">加载中...</td>
                  </tr>
                ) : documents.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="openapi-knowledge-empty">暂无文档</td>
                  </tr>
                ) : (
                  documents.map((doc) => {
                    const deleting = deletingDocumentIds.includes(doc.id)
                    const deletingDisabled = deleting || doc.status === 'pending' || doc.status === 'processing'
                    return (
                      <tr key={doc.id}>
                        <td>#{doc.id}</td>
                        <td>
                          <button
                            type="button"
                            className="openapi-knowledge-link-button"
                            onClick={() => {
                              setEndpointDocumentIdFilter(doc.id)
                              setEndpointSkip(0)
                              setSearchDocumentId(doc.id)
                            }}
                          >
                            {doc.filename}
                          </button>
                          {doc.error_message && (
                            <p className="openapi-knowledge-error-text">{doc.error_message}</p>
                          )}
                        </td>
                        <td>
                          <span className={`openapi-status-badge is-${doc.status}`}>
                            {documentStatusText(doc.status)}
                          </span>
                        </td>
                        <td>{doc.endpoint_count} / {doc.chunk_count}</td>
                        <td>{formatDateTime(doc.created_at)}</td>
                        <td>{formatDateTime(doc.updated_at)}</td>
                        <td>
                          <button
                            type="button"
                            className="openapi-knowledge-danger-button"
                            disabled={deletingDisabled}
                            onClick={() => {
                              void handleDeleteDocument(doc)
                            }}
                          >
                            {deleting ? <LoaderCircle size={13} className="spin" /> : <Trash2 size={13} />}
                            删除
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="openapi-knowledge-pagination">
            <button
              type="button"
              disabled={!hasPrevDocumentPage}
              onClick={() => setDocumentSkip((prev) => Math.max(0, prev - DOCUMENT_PAGE_SIZE))}
            >
              上一页
            </button>
            <span>{documentTotal === 0 ? '0 / 0' : `${documentSkip + 1} - ${Math.min(documentSkip + DOCUMENT_PAGE_SIZE, documentTotal)} / ${documentTotal}`}</span>
            <button
              type="button"
              disabled={!hasNextDocumentPage}
              onClick={() => setDocumentSkip((prev) => prev + DOCUMENT_PAGE_SIZE)}
            >
              下一页
            </button>
          </div>
        </section>

        <section className="openapi-knowledge-card">
          <div className="openapi-knowledge-card__header">
            <h2>端点列表</h2>
            <div className="openapi-knowledge-card__filters">
              <select
                value={endpointDocumentIdFilter}
                onChange={(event) => {
                  const value = event.target.value
                  setEndpointDocumentIdFilter(value ? Number(value) : '')
                  setEndpointSkip(0)
                }}
              >
                <option value="">全部文档</option>
                {documentOptions.map((item) => (
                  <option key={item.value} value={item.value}>{item.label}</option>
                ))}
              </select>
              <input
                type="text"
                value={endpointMethodFilter}
                onChange={(event) => {
                  setEndpointMethodFilter(event.target.value)
                  setEndpointSkip(0)
                }}
                placeholder="METHOD"
              />
              <input
                type="text"
                value={endpointTagFilter}
                onChange={(event) => {
                  setEndpointTagFilter(event.target.value)
                  setEndpointSkip(0)
                }}
                placeholder="tag"
              />
            </div>
          </div>

          <div className="openapi-knowledge-table-wrap">
            <table className="openapi-knowledge-table">
              <thead>
                <tr>
                  <th>方法</th>
                  <th>路径</th>
                  <th>摘要</th>
                  <th>标签</th>
                  <th>Operation ID</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {endpointsLoading ? (
                  <tr>
                    <td colSpan={6} className="openapi-knowledge-empty">加载中...</td>
                  </tr>
                ) : endpointItems.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="openapi-knowledge-empty">暂无端点</td>
                  </tr>
                ) : (
                  endpointItems.map((endpoint) => {
                    const deleting = deletingEndpointIds.includes(endpoint.id)
                    const expanded = expandedEndpointIds.includes(endpoint.id)
                    return (
                      <tr key={endpoint.id}>
                        <td><span className="openapi-method-badge">{endpoint.method}</span></td>
                        <td className="openapi-knowledge-path">{endpoint.path}</td>
                        <td>
                          <p className="openapi-knowledge-summary">{endpoint.summary || '-'}</p>
                          <button
                            type="button"
                            className="openapi-knowledge-link-button"
                            onClick={() => toggleExpanded(endpoint.id)}
                          >
                            {expanded ? '收起详情' : '展开详情'}
                          </button>
                          {expanded && (
                            <pre className="openapi-knowledge-content">{endpoint.content}</pre>
                          )}
                        </td>
                        <td>{endpoint.tags?.join(', ') || '-'}</td>
                        <td>{endpoint.operation_id || '-'}</td>
                        <td>
                          <button
                            type="button"
                            className="openapi-knowledge-danger-button"
                            disabled={deleting}
                            onClick={() => {
                              void handleDeleteEndpoint(endpoint)
                            }}
                          >
                            {deleting ? <LoaderCircle size={13} className="spin" /> : <Trash2 size={13} />}
                            删除
                          </button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="openapi-knowledge-pagination">
            <button
              type="button"
              disabled={!hasPrevEndpointPage}
              onClick={() => setEndpointSkip((prev) => Math.max(0, prev - ENDPOINT_PAGE_SIZE))}
            >
              上一页
            </button>
            <span>{endpointTotal === 0 ? '0 / 0' : `${endpointSkip + 1} - ${Math.min(endpointSkip + ENDPOINT_PAGE_SIZE, endpointTotal)} / ${endpointTotal}`}</span>
            <button
              type="button"
              disabled={!hasNextEndpointPage}
              onClick={() => setEndpointSkip((prev) => prev + ENDPOINT_PAGE_SIZE)}
            >
              下一页
            </button>
          </div>
        </section>
      </div>

      <section className="openapi-knowledge-card">
        <div className="openapi-knowledge-card__header">
          <h2>手动检索</h2>
        </div>
        <div className="openapi-knowledge-search-bar">
          <input
            type="text"
            placeholder="输入接口问题或关键词"
            value={searchQ}
            onChange={(event) => setSearchQ(event.target.value)}
          />
          <input
            type="number"
            min={1}
            max={20}
            value={searchTopK}
            onChange={(event) => setSearchTopK(Math.max(1, Math.min(20, Number(event.target.value) || 1)))}
          />
          <input
            type="text"
            placeholder="METHOD"
            value={searchMethod}
            onChange={(event) => setSearchMethod(event.target.value)}
          />
          <select
            value={searchDocumentId}
            onChange={(event) => {
              const value = event.target.value
              setSearchDocumentId(value ? Number(value) : '')
            }}
          >
            <option value="">全部文档</option>
            {documentOptions.map((item) => (
              <option key={item.value} value={item.value}>{item.label}</option>
            ))}
          </select>
          <button
            type="button"
            className="openapi-knowledge-primary-button"
            onClick={() => {
              void handleSearch()
            }}
            disabled={searchLoading || !searchQ.trim()}
          >
            {searchLoading ? <LoaderCircle size={14} className="spin" /> : <Search size={14} />}
            检索
          </button>
        </div>

        <div className="openapi-knowledge-search-results">
          {!hasSearched ? (
            <p className="openapi-knowledge-empty">请输入关键词并点击检索</p>
          ) : searchResults.length === 0 ? (
            <p className="openapi-knowledge-empty">当前知识库未找到相关接口</p>
          ) : (
            searchResults.map((item) => (
              <article key={item.chunk_id} className="openapi-knowledge-result-card">
                <header>
                  <span className="openapi-method-badge">{item.method}</span>
                  <strong>{item.path}</strong>
                  <span>相似度：{item.similarity_score.toFixed(4)}</span>
                </header>
                <p>{item.summary || item.description || '无摘要'}</p>
                <pre>{item.content}</pre>
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  )
}
