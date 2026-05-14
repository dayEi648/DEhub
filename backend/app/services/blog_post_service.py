from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.models.blog_post import BlogPost
from app.core.permissions import require_super_admin
from app.schemas.blog_post import (
    BlogPostCreate,
    BlogPostUpdate,
    BlogPostResponse,
    BlogPostDetailResponse,
    BlogPostListItem,
    BlogPostListResponse,
)
from app.crud import blog_post as blog_post_crud


class BlogPostService:
    def __init__(self, db: Session):
        self.db = db

    def _require_super_admin(self, current_user: User) -> None:
        """要求当前用户为超级管理员"""
        require_super_admin(current_user)

    def _ensure_slug_unique(self, slug: str, exclude_post_id: int | None = None) -> None:
        """校验 slug 唯一性"""
        existing = blog_post_crud.get_blog_post_by_slug(self.db, slug)
        if existing and (exclude_post_id is None or existing.id != exclude_post_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文章 slug 已存在"
            )

    def _build_visible_query(self, current_user: User):
        """构建基于当前用户权限的可见文章查询基线（自动 join 分类信息）"""
        query = (
            self.db.query(BlogPost)
            .options(joinedload(BlogPost.category))
            .filter(BlogPost.is_deleted == False)
        )
        if current_user.permission < 2:
            query = query.filter(BlogPost.status == "published")
        return query

    # ---------- 写操作（超管专属）----------

    def create_blog_post(self, post_in: BlogPostCreate, current_user: User) -> BlogPost:
        self._require_super_admin(current_user)
        self._ensure_slug_unique(post_in.slug)
        db_post = blog_post_crud.create_blog_post(self.db, post_in)
        # 重新查询以加载 category 关联，避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    def publish_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        self._require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
        if db_post.status == "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文章已是发布状态")
        db_post.status = "published"
        self.db.commit()
        self.db.refresh(db_post)
        # 重新查询以加载 category 关联，避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    def unpublish_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        self._require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
        if db_post.status == "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文章已是草稿状态")
        db_post.status = "draft"
        self.db.commit()
        self.db.refresh(db_post)
        # 重新查询以加载 category 关联，避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    def update_blog_post(
        self, post_id: int, post_in: BlogPostUpdate, current_user: User
    ) -> BlogPost:
        self._require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        update_data = post_in.model_dump(exclude_unset=True)
        if "slug" in update_data and update_data["slug"] != db_post.slug:
            self._ensure_slug_unique(update_data["slug"], exclude_post_id=db_post.id)

        updated = blog_post_crud.update_blog_post(self.db, db_post, post_in)
        # 重新查询以加载 category 关联（可能已变更），避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, updated.id)
        return refreshed

    def soft_delete_blog_post(self, post_id: int, current_user: User) -> None:
        self._require_super_admin(current_user)
        result = blog_post_crud.soft_delete_blog_post(self.db, post_id)
        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在或已被删除"
            )

    def hard_delete_blog_post(self, post_id: int, current_user: User) -> None:
        self._require_super_admin(current_user)
        result = blog_post_crud.hard_delete_blog_post(self.db, post_id)
        if result == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    def cleanup_deleted_posts(self, current_user: User) -> int:
        self._require_super_admin(current_user)
        return blog_post_crud.cleanup_deleted_posts(self.db)

    # ---------- 读操作（权限区分）----------

    def _get_visible_post(self, current_user: User):
        """获取当前用户可见的单篇文章查询"""
        query = self.db.query(BlogPost).filter(BlogPost.is_deleted == False)
        if current_user.permission < 2:
            query = query.filter(BlogPost.status == "published")
        return query

    def get_blog_post(self, post_id: int, current_user: User) -> BlogPostDetailResponse:
        query = self._build_visible_query(current_user)
        db_post = query.filter(BlogPost.id == post_id).first()
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        # 增加浏览量
        blog_post_crud.increment_view_count(self.db, post_id)

        # 查询相邻文章（基于当前用户可见范围）
        prev_post = (
            self._build_visible_query(current_user)
            .filter(BlogPost.created_at < db_post.created_at)
            .order_by(BlogPost.created_at.desc())
            .first()
        )
        next_post = (
            self._build_visible_query(current_user)
            .filter(BlogPost.created_at > db_post.created_at)
            .order_by(BlogPost.created_at.asc())
            .first()
        )

        response_data = BlogPostResponse.model_validate(db_post).model_dump()
        response_data["prev_post"] = (
            BlogPostListItem.model_validate(prev_post) if prev_post else None
        )
        response_data["next_post"] = (
            BlogPostListItem.model_validate(next_post) if next_post else None
        )
        return BlogPostDetailResponse.model_validate(response_data)

    def get_blog_post_by_slug(self, slug: str, current_user: User) -> BlogPostDetailResponse:
        query = self._build_visible_query(current_user)
        db_post = query.filter(BlogPost.slug == slug).first()
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        # 增加浏览量
        blog_post_crud.increment_view_count(self.db, db_post.id)

        # 查询相邻文章
        prev_post = (
            self._build_visible_query(current_user)
            .filter(BlogPost.created_at < db_post.created_at)
            .order_by(BlogPost.created_at.desc())
            .first()
        )
        next_post = (
            self._build_visible_query(current_user)
            .filter(BlogPost.created_at > db_post.created_at)
            .order_by(BlogPost.created_at.asc())
            .first()
        )

        response_data = BlogPostResponse.model_validate(db_post).model_dump()
        response_data["prev_post"] = (
            BlogPostListItem.model_validate(prev_post) if prev_post else None
        )
        response_data["next_post"] = (
            BlogPostListItem.model_validate(next_post) if next_post else None
        )
        return BlogPostDetailResponse.model_validate(response_data)

    def list_blog_posts(
        self,
        skip: int,
        limit: int,
        status: str | None,
        category_id: int | None,
        tag: str | None,
        q: str | None,
        include_unpublished: bool,
        current_user: User,
    ) -> BlogPostListResponse:
        if current_user.permission != 2:
            effective_status = "published"
        else:
            effective_status = status if include_unpublished else "published"

        posts = blog_post_crud.get_blog_posts(
            self.db,
            skip=skip,
            limit=limit,
            status=effective_status,
            category_id=category_id,
            tag=tag,
            q=q,
        )
        total = blog_post_crud.get_blog_posts_count(
            self.db,
            status=effective_status,
            category_id=category_id,
            tag=tag,
            q=q,
        )
        return BlogPostListResponse(
            items=[BlogPostListItem.model_validate(post) for post in posts],
            total=total,
        )
