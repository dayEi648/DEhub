import json
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.blog_post import (
    BlogPostCreate,
    BlogPostUpdate,
    BlogPostResponse,
    BlogPostDetailResponse,
    BlogPostListResponse,
    GenerateSummaryRequest,
    GenerateSummaryResponse,
)
from app.services.blog_post_service import BlogPostService
from app.services.vector_sync_service import (
    sync_blog_post_embedding,
    sync_cleanup_orphaned_embeddings,
)

router = APIRouter(prefix="/blog_posts", tags=["博客文章管理"])


def parse_blog_post_create(post_in: str = Form(..., description="博客文章创建请求的 JSON 字符串")) -> BlogPostCreate:
    """解析前端传来的 post_in JSON 字符串为 BlogPostCreate 模型"""
    return BlogPostCreate.model_validate(json.loads(post_in))


def parse_blog_post_update(post_in: str = Form(..., description="博客文章更新请求的 JSON 字符串")) -> BlogPostUpdate:
    """解析前端传来的 post_in JSON 字符串为 BlogPostUpdate 模型"""
    return BlogPostUpdate.model_validate(json.loads(post_in))


# ---------- 写操作（超管专属）----------

@router.post("/", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_post(
    post_in: BlogPostCreate = Depends(parse_blog_post_create),
    file: UploadFile | None = File(None, description="封面图片文件，最大 5MB，支持自动压缩"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostResponse:
    """
    创建博客文章（超级管理员专属）
    """
    service = BlogPostService(db)
    post = await service.create_blog_post(post_in, current_user, file)
    background_tasks.add_task(sync_blog_post_embedding, post.id)
    return post


@router.post("/{post_id}/publish", response_model=BlogPostResponse)
def publish_blog_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostResponse:
    """
    发布博客文章（超级管理员专属）
    """
    service = BlogPostService(db)
    post = service.publish_blog_post(post_id, current_user)
    background_tasks.add_task(sync_blog_post_embedding, post.id)
    return post


@router.post("/{post_id}/unpublish", response_model=BlogPostResponse)
def unpublish_blog_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostResponse:
    """
    下线博客文章（超级管理员专属）
    """
    service = BlogPostService(db)
    post = service.unpublish_blog_post(post_id, current_user)
    background_tasks.add_task(sync_blog_post_embedding, post.id)
    return post


@router.put("/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: int,
    post_in: BlogPostUpdate = Depends(parse_blog_post_update),
    file: UploadFile | None = File(None, description="封面图片文件，最大 5MB，支持自动压缩"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostResponse:
    """
    更新博客文章（超级管理员专属）
    """
    service = BlogPostService(db)
    post = await service.update_blog_post(post_id, post_in, current_user, file)
    background_tasks.add_task(sync_blog_post_embedding, post.id)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_blog_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    逻辑删除博客文章（超级管理员专属）
    """
    service = BlogPostService(db)
    service.soft_delete_blog_post(post_id, current_user)
    background_tasks.add_task(sync_blog_post_embedding, post_id)
    return None


@router.delete("/{post_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_blog_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    物理删除博客文章（超级管理员专属）
    """
    service = BlogPostService(db)
    await service.hard_delete_blog_post(post_id, current_user)
    background_tasks.add_task(sync_blog_post_embedding, post_id)
    return None


@router.delete("/cleanup")
def cleanup_deleted_posts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    一键清理所有已逻辑删除的博客文章（超级管理员专属）
    Returns:
        dict: 清理数量
    """
    service = BlogPostService(db)
    count = service.cleanup_deleted_posts(current_user)
    background_tasks.add_task(sync_cleanup_orphaned_embeddings)
    return {"deleted_count": count}


# ---------- 读操作（权限区分）----------

@router.get("/{post_id}", response_model=BlogPostDetailResponse)
def get_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostDetailResponse:
    """
    查看单篇博客文章详情（通过 ID）
    - 普通用户：只能查看已发布且未删除的文章
    - 超级管理员：可查看任何未删除的文章（含草稿）
    """
    service = BlogPostService(db)
    return service.get_blog_post(post_id, current_user)


@router.get("/by-slug/{slug}", response_model=BlogPostDetailResponse)
def get_blog_post_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostDetailResponse:
    """
    查看单篇博客文章详情（通过 slug，SEO 友好）
    - 普通用户：只能查看已发布且未删除的文章
    - 超级管理员：可查看任何未删除的文章（含草稿）
    """
    service = BlogPostService(db)
    return service.get_blog_post_by_slug(slug, current_user)


@router.post("/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary(
    req: GenerateSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerateSummaryResponse:
    """
    AI 自动生成文章摘要（超级管理员专属）
    正文需至少 100 字符
    """
    service = BlogPostService(db)
    summary = await service.generate_summary(req.content_md, current_user)
    return GenerateSummaryResponse(summary=summary)


@router.get("/", response_model=BlogPostListResponse)
def list_blog_posts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None, pattern=r"^(draft|published)$"),
    category_id: int | None = Query(default=None, ge=1),
    tag: str | None = Query(default=None),
    q: str | None = Query(default=None, description="标题关键词搜索"),
    include_unpublished: bool = Query(default=False, description="是否包含未发布文章（仅超管有效）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostListResponse:
    """
    列出博客文章列表（分页查询）
    - 普通用户：只能查询已发布且未删除的文章
    - 超级管理员：可通过 include_unpublished=true 查询未发布的文章
    """
    service = BlogPostService(db)
    return service.list_blog_posts(
        skip=skip,
        limit=limit,
        status=status,
        category_id=category_id,
        tag=tag,
        q=q,
        include_unpublished=include_unpublished,
        current_user=current_user,
    )
