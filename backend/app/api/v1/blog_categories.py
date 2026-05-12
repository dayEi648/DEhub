from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.blog_category import (
    BlogCategoryCreate,
    BlogCategoryUpdate,
    BlogCategoryWithPostCount,
)
from app.services.blog_category_service import BlogCategoryService

router = APIRouter(prefix="/blog_categories", tags=["博客分类管理"])


@router.post("/", response_model=BlogCategoryWithPostCount, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: BlogCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogCategoryWithPostCount:
    """
    创建分类（超级管理员专属）
    """
    service = BlogCategoryService(db)
    return service.create_category(category_in, current_user)


@router.get("/", response_model=List[BlogCategoryWithPostCount])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BlogCategoryWithPostCount]:
    """
    查询所有分类
    """
    service = BlogCategoryService(db)
    return service.list_categories()


@router.get("/{category_id}", response_model=BlogCategoryWithPostCount)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogCategoryWithPostCount:
    """
    根据 ID 查询分类
    """
    service = BlogCategoryService(db)
    return service.get_category(category_id)


@router.get("/by-slug/{slug}", response_model=BlogCategoryWithPostCount)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogCategoryWithPostCount:
    """
    根据 slug 查询分类（SEO 友好）
    """
    service = BlogCategoryService(db)
    return service.get_category_by_slug(slug)


@router.put("/{category_id}", response_model=BlogCategoryWithPostCount)
def update_category(
    category_id: int,
    category_in: BlogCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogCategoryWithPostCount:
    """
    编辑分类（超级管理员专属）
    """
    service = BlogCategoryService(db)
    return service.update_category(category_id, category_in, current_user)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    删除分类（超级管理员专属）
    若该分类下还有文章，将返回 400
    """
    service = BlogCategoryService(db)
    service.delete_category(category_id, current_user)
    return None
