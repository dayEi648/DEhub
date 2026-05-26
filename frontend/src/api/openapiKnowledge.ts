import request from '../utils/request'
import type {
  ListOpenAPIDocumentsParams,
  ListOpenAPIEndpointsParams,
  OpenAPIDocument,
  OpenAPIDocumentListResponse,
  OpenAPIDocumentUploadResponse,
  OpenAPIEndpointListResponse,
  OpenAPISearchResponse,
  SearchOpenAPIKnowledgeParams,
} from '../types/openapiKnowledge'

export async function uploadOpenAPIDocument(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<OpenAPIDocumentUploadResponse>('/openapi_knowledge/documents/upload', formData)
}

export function getOpenAPIDocuments(params: ListOpenAPIDocumentsParams = {}) {
  return request.get<OpenAPIDocumentListResponse>('/openapi_knowledge/documents', { params })
}

export function getOpenAPIDocument(documentId: number, signal?: AbortSignal) {
  return request.get<OpenAPIDocument>(`/openapi_knowledge/documents/${documentId}`, { signal })
}

export function deleteOpenAPIDocument(documentId: number) {
  return request.delete(`/openapi_knowledge/documents/${documentId}`)
}

export function getOpenAPIEndpoints(params: ListOpenAPIEndpointsParams = {}) {
  return request.get<OpenAPIEndpointListResponse>('/openapi_knowledge/endpoints', { params })
}

export function searchOpenAPIKnowledge(params: SearchOpenAPIKnowledgeParams) {
  return request.get<OpenAPISearchResponse>('/openapi_knowledge/search', { params })
}

export function deleteOpenAPIEndpoint(endpointId: number) {
  return request.delete(`/openapi_knowledge/endpoints/${endpointId}`)
}
