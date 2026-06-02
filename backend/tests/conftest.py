"""Pytest 全局配置与共享 fixture。"""

import os
from unittest.mock import AsyncMock, patch

# 必须在导入 app.core.config 前覆盖数据库名，确保测试指向独立的 test 库。
os.environ.setdefault("POSTGRES_DB", "dehub_test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 在导入 app.main 前 mock 掉 lifespan 中的外部依赖初始化，
# 避免测试启动时连接 Redis / LLM / Embedding 等服务。
_mock_modules = [
    "app.redis_client.init_redis_client",
    "app.redis_client.init_sync_redis_client",
    "app.redis_client.init_checkpoint_redis_client",
    "app.infrastructure.llm_client.init_llm_client",
    "app.infrastructure.llm_client.init_llm_small_client",
    "app.infrastructure.embedding_client.init_embedding_client",
    "app.infrastructure.checkpoint_client.init_checkpoint_client",
    "app.core.log_handler.SystemLogHandler",
]

for _m in _mock_modules:
    patch(_m, new_callable=AsyncMock if "init_" in _m else lambda: AsyncMock).start()

# 默认关闭内容审核后台任务的自动调度，避免通用测试被异步副作用污染。
patch(
    "app.services.content_moderation_service.background_task_manager.create_task",
    return_value=None,
).start()

# 现在安全导入 app
from app.core.config import settings
from app.core.security import get_current_user
from app.db.base import Base
from app.db.session import SessionLocal
from app.main import app
from app.api.deps import get_db
from app.models.user import User
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost

TEST_DATABASE_URL = settings.DATABASE_URL


@pytest.fixture(scope="session")
def engine():
    """创建指向测试库的 engine，并在测试会话开始前创建所有表。"""
    test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(engine):
    """
    每个测试函数在独立事务中运行，测试结束后自动回滚，
    确保测试互不污染。
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """
    FastAPI TestClient，注入测试用 db_session，替换默认的 get_db 依赖。
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """创建一个管理员用户，用于需要高权限的测试场景。"""
    user = User(
        username="admin_test",
        email="admin@test.com",
        hashed_password="$2b$12$dummyhashedpassword",
        permission=2,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def normal_user(db_session):
    """创建一个普通用户，用于常规测试场景。"""
    user = User(
        username="user_test",
        email="user@test.com",
        hashed_password="$2b$12$dummyhashedpassword",
        permission=0,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def blog_category(db_session):
    """创建一个博客分类，供文章测试使用。"""
    category = BlogCategory(name="测试分类", slug="test-category")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def blog_post(db_session, admin_user, blog_category):
    """创建一篇已发布的博客文章。"""
    post = BlogPost(
        title="测试文章",
        slug="test-post",
        summary="测试摘要",
        content_md="# Hello",
        user_id=admin_user.id,
        category_id=blog_category.id,
        status="published",
        tags=["test"],
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


@pytest.fixture
def draft_blog_post(db_session, admin_user, blog_category):
    """创建一篇草稿状态的博客文章。"""
    post = BlogPost(
        title="草稿文章",
        slug="draft-post",
        summary=None,
        content_md="# Draft\n\n这是一篇草稿文章。",
        user_id=admin_user.id,
        category_id=blog_category.id,
        status="draft",
        tags=["draft"],
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


@pytest.fixture
def auth_client(db_session, admin_user):
    """
    已认证的 TestClient，默认以 admin_user 身份访问。
    绕过了 JWT + Redis 的校验链，专注于接口业务逻辑测试。
    """
    def override_get_db():
        yield db_session

    async def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()
