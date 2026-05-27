"""OpenAPI 知识库管理接口（管理员专用）。

所有接口均要求管理员权限，普通用户无法通过 REST 访问 OpenAPI 知识库能力。
"""

from __future__ import annotations

import hashlib
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.crud import openapi_knowledge as crud
from app.infrastructure.background_tasks import background_task_manager
from app.models.user import User
from app.schemas.openapi_knowledge import (
    OpenAPIDocumentListResponse,
    OpenAPIDocumentResponse,
    OpenAPIDocumentUploadResponse,
    OpenAPIEndpointListResponse,
    OpenAPISearchResponse,
)
from app.services.openapi_embedding_service import OpenAPIEmbeddingService
from app.services.openapi_parser_service import OpenAPIParserService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openapi_knowledge", tags=["OpenAPI 知识库"])

# ------------------------------------------------------------------
# 后台解析任务
# ------------------------------------------------------------------


async def _process_openapi_document(document_id: int, content: bytes, filename: str) -> None:
    """后台解析 OpenAPI 文档、向量化入库并更新状态。"""
    from app.db.session import SessionLocal

    parser = OpenAPIParserService()

    with SessionLocal() as db:
        try:
            crud.update_document_status(db, document_id, "processing")

            # 并发安全检查：文档可能在上传后被删除
            doc = crud.get_document_by_id(db, document_id)
            if doc is None:
                logger.warning("文档在解析前已被删除，终止后台任务: doc_id=%s", document_id)
                return

            chunks = parser.parse(content, filename, document_id)

            # 向量入库
            embed_service = OpenAPIEmbeddingService(db)
            inserted = embed_service.sync_document_embeddings(document_id, chunks)

            crud.update_document_status(
                db,
                document_id,
                "completed",
                endpoint_count=len(chunks),
                chunk_count=inserted,
            )
            logger.info(
                "OpenAPI 文档解析完成: doc_id=%s, endpoints=%s, inserted=%s",
                document_id,
                len(chunks),
                inserted,
            )
        except Exception as exc:
            error_msg = str(exc)
            logger.exception(
                "OpenAPI 文档解析失败: doc_id=%s, error=%s",
                document_id,
                error_msg,
            )
            crud.update_document_status(
                db,
                document_id,
                "failed",
                error_message=error_msg,
            )


def recover_pending_documents() -> None:
    """启动时扫描 pending/processing 文档，标记为 failed（服务重启导致中断）。

    因当前模型未持久化原始文件内容，重启后无法自动恢复解析流程，
    故将挂起文档明确标记失败，避免状态无限挂起。
    """
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        pending_docs, _ = crud.list_documents(
            db, skip=0, limit=1000, status="pending"
        )
        processing_docs, _ = crud.list_documents(
            db, skip=0, limit=1000, status="processing"
        )
        for doc in pending_docs + processing_docs:
            crud.update_document_status(
                db,
                doc.id,
                "failed",
                error_message="服务重启导致解析任务中断，请重新上传",
            )
            logger.warning(
                "OpenAPI 文档状态已修正为失败: doc_id=%s, old_status=%s",
                doc.id,
                doc.status,
            )


# ------------------------------------------------------------------
# REST 接口
# ------------------------------------------------------------------


@router.post("/documents/upload", response_model=OpenAPIDocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传 OpenAPI 文档并启动后台解析。

    权限：管理员及以上。
    重复文件（content_hash 相同）会覆盖旧文档。
    """
    require_admin(current_user)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未上传文件",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="空文件",
        )

    # 文件大小限制
    if len(content) > settings.OPENAPI_UPLOAD_MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="文件超过大小限制（10MB）",
        )

    filename = file.filename
    if not any(filename.lower().endswith(ext) for ext in [".json", ".yaml", ".yml"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="格式不支持，仅接受 .json / .yaml / .yml",
        )

    content_hash = hashlib.md5(content).hexdigest()

    # 重复上传检测：覆盖旧文档
    existing = crud.get_document_by_content_hash(db, content_hash)
    if existing:
        existing_id = existing.id
        crud.delete_document(db, existing_id)
        logger.info(
            "覆盖旧 OpenAPI 文档: old_id=%s, hash=%s",
            existing_id,
            content_hash,
        )

    doc = crud.create_document(
        db=db,
        uploaded_by=current_user.id,
        filename=filename,
        content_hash=content_hash,
        status="pending",
    )

    background_task_manager.create_task(
        _process_openapi_document(doc.id, content, filename),
        name=f"openapi.parse.{doc.id}",
    )

    return {
        "document_id": doc.id,
        "filename": filename,
        "status": "pending",
    }


@router.get("/documents", response_model=OpenAPIDocumentListResponse)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(
        default=None,
        pattern=r"^(pending|processing|completed|failed)$",
        description="状态过滤：pending / processing / completed / failed",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分页查看 OpenAPI 文档列表。

    权限：管理员及以上。
    """
    require_admin(current_user)

    docs, total = crud.list_documents(db, skip=skip, limit=limit, status=status)
    return {
        "items": docs,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/documents/{document_id}", response_model=OpenAPIDocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查看单个文档详情和解析状态。

    权限：管理员及以上。
    前端上传后可通过该接口轮询 status。
    """
    require_admin(current_user)

    doc = crud.get_document_by_id(db, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )
    return doc


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文档及其所有端点向量。

    权限：管理员及以上。
    """
    require_admin(current_user)

    doc = crud.get_document_by_id(db, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在",
        )

    crud.delete_document(db, document_id)
    return None


@router.get("/endpoints", response_model=OpenAPIEndpointListResponse)
async def list_endpoints(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    document_id: int | None = Query(default=None),
    method: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分页查看端点列表。

    权限：管理员及以上。
    """
    require_admin(current_user)

    eps, total = crud.list_endpoints(
        db, skip=skip, limit=limit, document_id=document_id, method=method, tag=tag
    )
    return {
        "items": eps,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/search", response_model=OpenAPISearchResponse)
async def search_endpoints(
    q: str = Query(..., min_length=1, description="检索问题或关键词"),
    top_k: int = Query(default=5, ge=1, le=20),
    method: str | None = Query(default=None),
    document_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动检索 OpenAPI 知识库。

    权限：管理员及以上。
    """
    require_admin(current_user)

    service = OpenAPIEmbeddingService(db)
    results = service.search(
        query=q,
        top_k=top_k,
        method=method,
        document_id=document_id,
    )
    return {"items": results, "total": len(results)}


@router.delete(
    "/endpoints/{endpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_endpoint(
    endpoint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除单个端点向量。

    权限：管理员及以上。
    """
    require_admin(current_user)

    deleted = crud.delete_endpoint_by_id(db, endpoint_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="端点不存在",
        )
    return None
