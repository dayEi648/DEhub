export type OpenAPIDocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface OpenAPIDocument {
  id: number
  filename: string
  status: OpenAPIDocumentStatus
  endpoint_count: number
  chunk_count: number
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface OpenAPIDocumentUploadResponse {
  document_id: number
  filename: string
  status: OpenAPIDocumentStatus
}

export interface OpenAPIDocumentListResponse {
  items: OpenAPIDocument[]
  total: number
  skip: number
  limit: number
}

export interface OpenAPIEndpoint {
  id: number
  document_id: number
  chunk_id: string
  path: string
  method: string
  summary: string | null
  description: string | null
  tags: string[] | null
  operation_id: string | null
  content: string
  created_at: string
  updated_at: string
}

export interface OpenAPIEndpointListResponse {
  items: OpenAPIEndpoint[]
  total: number
  skip: number
  limit: number
}

export interface OpenAPISearchResult {
  id: number
  document_id: number
  chunk_id: string
  path: string
  method: string
  summary: string | null
  description: string | null
  tags: string[] | null
  operation_id: string | null
  content: string
  similarity_score: number
}

export interface OpenAPISearchResponse {
  items: OpenAPISearchResult[]
  total: number
}

export interface ListOpenAPIDocumentsParams {
  skip?: number
  limit?: number
  status?: OpenAPIDocumentStatus
}

export interface ListOpenAPIEndpointsParams {
  skip?: number
  limit?: number
  document_id?: number
  method?: string
  tag?: string
}

export interface SearchOpenAPIKnowledgeParams {
  q: string
  top_k?: number
  method?: string
  document_id?: number
}
