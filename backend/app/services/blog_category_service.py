from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.core.permissions import require_super_admin
from app.schemas.blog_category import (
    BlogCategoryCreate,
    BlogCategoryUpdate,
    BlogCategoryWithPostCount,
)
from app.crud import blog_category as blog_category_crud
from app.utils.slug import generate_unique_slug
from app.infrastructure.cache import build_cache_key, get_json_cache, set_json_cache
from app.infrastructure.cache_invalidator import BlogCacheInvalidator
from app.core.config import settings


class BlogCategoryService:
    def __init__(self, db: Session):
        self.db = db

    def _require_super_admin(self, current_user: User) -> None:
        """要求当前用户为超级管理员"""
        require_super_admin(current_user)

    def _ensure_slug_unique(
        self, slug: str, exclude_category_id: int | None = None
    ) -> None:
        """校验 slug 唯一性"""
        existing = blog_category_crud.get_category_by_slug(self.db, slug)
        if existing and (
            exclude_category_id is None or existing.id != exclude_category_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分类 slug 已存在",
            )

    def create_category(
        self, category_in: BlogCategoryCreate, current_user: User
    ) -> BlogCategory:
        self._require_super_admin(current_user)

        # 若未提供 slug，根据名称自动生成
        if not category_in.slug:
            slug = generate_unique_slug(
                self.db, category_in.name, exists_checker=blog_category_crud.get_category_by_slug
            )
            category_in = category_in.model_copy(update={"slug": slug})
        else:
            self._ensure_slug_unique(category_in.slug)

        result = blog_category_crud.create_category(self.db, category_in)
        BlogCacheInvalidator.invalidate_blog_categories()
        return result

    def get_category(
        self, category_id: int
    ) -> BlogCategoryWithPostCount:
        db_category = blog_category_crud.get_category_by_id(self.db, category_id)
        if not db_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在"
            )
        post_count = blog_category_crud.count_posts_in_category(
            self.db, category_id
        )
        response_data = BlogCategoryWithPostCount.model_validate(
            db_category
        ).model_dump()
        response_data["post_count"] = post_count
        return BlogCategoryWithPostCount.model_validate(response_data)

    def list_categories(
        self
    ) -> list[BlogCategoryWithPostCount]:
        cache_key = build_cache_key("blog_categories:list")
        cached = get_json_cache(cache_key, list[BlogCategoryWithPostCount])
        if cached is not None:
            return cached

        categories = blog_category_crud.get_all_categories(self.db)

        # 一次性获取所有分类的文章数量，避免 N+1 查询
        counts = {
            row.category_id: row.count
            for row in self.db.query(
                BlogPost.category_id,
                func.count(BlogPost.id).label("count"),
            )
            .group_by(BlogPost.category_id)
            .all()
        }

        result = []
        for cat in categories:
            data = BlogCategoryWithPostCount.model_validate(cat).model_dump()
            data["post_count"] = counts.get(cat.id, 0)
            result.append(BlogCategoryWithPostCount.model_validate(data))

        set_json_cache(
            cache_key,
            result,
            settings.CACHE_BLOG_CATEGORY_TTL,
            tags=["blog_categories"],
        )
        return result

    def update_category(
        self,
        category_id: int,
        category_in: BlogCategoryUpdate,
        current_user: User,
    ) -> BlogCategory:
        self._require_super_admin(current_user)
        db_category = blog_category_crud.get_category_by_id(
            self.db, category_id
        )
        if not db_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在"
            )

        update_data = category_in.model_dump(exclude_unset=True)
        if "slug" in update_data and update_data["slug"] != db_category.slug:
            self._ensure_slug_unique(
                update_data["slug"], exclude_category_id=db_category.id
            )

        result = blog_category_crud.update_category(
            self.db, db_category, category_in
        )
        BlogCacheInvalidator.invalidate_all()
        return result

    def get_category_by_slug(self, slug: str) -> BlogCategoryWithPostCount:
        db_category = blog_category_crud.get_category_by_slug(self.db, slug)
        if not db_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在"
            )
        post_count = blog_category_crud.count_posts_in_category(
            self.db, db_category.id
        )
        response_data = BlogCategoryWithPostCount.model_validate(
            db_category
        ).model_dump()
        response_data["post_count"] = post_count
        return BlogCategoryWithPostCount.model_validate(response_data)

    def delete_category(self, category_id: int, current_user: User) -> None:
        self._require_super_admin(current_user)
        db_category = blog_category_crud.get_category_by_id(
            self.db, category_id
        )
        if not db_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分类不存在"
            )

        post_count = blog_category_crud.count_posts_in_category(
            self.db, category_id
        )
        if post_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该分类下还有文章，无法删除",
            )

        blog_category_crud.delete_category(self.db, category_id)
        BlogCacheInvalidator.invalidate_blog_categories()
