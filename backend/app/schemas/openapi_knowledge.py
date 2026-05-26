"""OpenAPI 知识库接口 Schemas。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _BaseSchema(BaseModel):
    model_config = {"from_attributes": True}


class OpenAPIDocumentResponse(_BaseSchema):
    id: int
    filename: str
    status: str
    endpoint_count: int
    chunk_count: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class OpenAPIDocumentListResponse(BaseModel):
    items: list[OpenAPIDocumentResponse]
    total: int
    skip: int
    limit: int


class OpenAPIDocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str


class OpenAPIEndpointResponse(_BaseSchema):
    id: int
    document_id: int
    chunk_id: str
    path: str
    method: str
    summary: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    operation_id: str | None = None
    content: str
    created_at: datetime
    updated_at: datetime


class OpenAPIEndpointListResponse(BaseModel):
    items: list[OpenAPIEndpointResponse]
    total: int
    skip: int
    limit: int


class OpenAPISearchResultResponse(BaseModel):
    id: int
    document_id: int
    chunk_id: str
    path: str
    method: str
    summary: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    operation_id: str | None = None
    content: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class OpenAPISearchResponse(BaseModel):
    items: list[OpenAPISearchResultResponse]
    total: int
