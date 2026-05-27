"""OpenAPI 知识库 API 集成测试（阶段 3）。

测试覆盖上传、状态查询、列表、删除等接口的权限与业务逻辑。
"""

import hashlib
import inspect
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.openapi_document import OpenAPIDocument
from app.crud import openapi_knowledge as crud


class TestUploadDocument:
    """测试 POST /documents/upload。"""

    def _make_file(self, content: bytes, filename: str = "api.json"):
        return {"file": (filename, BytesIO(content), "application/json")}

    @staticmethod
    def _consume_background_task(coro):
        """消费并关闭上传接口创建的协程，避免测试产生 unawaited warning。"""
        if inspect.iscoroutine(coro):
            coro.close()

    def test_normal_user_upload_returns_403(self, client: TestClient, normal_user):
        """普通用户上传应返回 403。"""
        from app.core.security import get_current_user
        from app.api.deps import get_db
        from app.db.session import SessionLocal

        def override_get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        async def override_get_current_user():
            return normal_user

        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            resp = client.post(
                "/api/v1/openapi_knowledge/documents/upload",
                files=self._make_file(b'{"openapi":"3.0.0","paths":{}}'),
            )
            assert resp.status_code == 403
        finally:
            client.app.dependency_overrides.clear()

    def test_admin_upload_returns_document_id(self, auth_client: TestClient):
        """管理员上传应返回 document_id 和 pending 状态。"""
        with patch("app.api.v1.openapi_knowledge.background_task_manager") as mock_btm:
            mock_btm.create_task = MagicMock(
                side_effect=lambda coro, name=None: self._consume_background_task(coro)
            )
            resp = auth_client.post(
                "/api/v1/openapi_knowledge/documents/upload",
                files=self._make_file(b'{"openapi":"3.0.0","paths":{}}'),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "document_id" in data
            assert data["filename"] == "api.json"
            assert data["status"] == "pending"

    def test_upload_empty_file_returns_400(self, auth_client: TestClient):
        """空文件应返回 400。"""
        resp = auth_client.post(
            "/api/v1/openapi_knowledge/documents/upload",
            files=self._make_file(b"", "api.json"),
        )
        assert resp.status_code == 400

    def test_upload_unsupported_format_returns_400(self, auth_client: TestClient):
        """不支持的格式应返回 400。"""
        resp = auth_client.post(
            "/api/v1/openapi_knowledge/documents/upload",
            files=self._make_file(b'{"openapi":"3.0.0"}', "api.txt"),
        )
        assert resp.status_code == 400

    def test_upload_duplicate_overwrites(self, auth_client: TestClient, db_session: Session):
        """重复 content_hash 应覆盖旧文档。"""
        content = b'{"openapi":"3.0.0","paths":{}}'
        content_hash = hashlib.md5(content).hexdigest()

        # 先创建旧文档
        old_doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="old.json",
            content_hash=content_hash,
            status="completed",
        )
        old_id = old_doc.id

        with patch("app.api.v1.openapi_knowledge.background_task_manager") as mock_btm:
            mock_btm.create_task = MagicMock(
                side_effect=lambda coro, name=None: self._consume_background_task(coro)
            )
            resp = auth_client.post(
                "/api/v1/openapi_knowledge/documents/upload",
                files=self._make_file(content, "api.json"),
            )
            assert resp.status_code == 200
            new_id = resp.json()["document_id"]
            # 覆盖后旧文档应被删除，新 document_id 不同
            assert new_id != old_id
            assert crud.get_document_by_id(db_session, old_id) is None


class TestGetDocument:
    """测试 GET /documents/{document_id}。"""

    def test_get_document_detail(self, auth_client: TestClient, db_session: Session):
        """应返回文档详情和解析状态。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="processing",
        )
        crud.update_document_status(
            db_session, doc.id, "processing",
            endpoint_count=5, chunk_count=5,
        )
        resp = auth_client.get(f"/api/v1/openapi_knowledge/documents/{doc.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == doc.id
        assert data["filename"] == "api.yaml"
        assert data["status"] == "processing"
        assert data["endpoint_count"] == 5
        assert data["chunk_count"] == 5
        # 接口响应不应暴露内部字段
        assert "uploaded_by" not in data
        assert "content_hash" not in data

    def test_get_document_not_found(self, auth_client: TestClient):
        """不存在的文档应返回 404。"""
        resp = auth_client.get("/api/v1/openapi_knowledge/documents/99999")
        assert resp.status_code == 404

    def test_get_document_normal_user_returns_403(self, client: TestClient, normal_user):
        """普通用户访问应返回 403。"""
        from app.core.security import get_current_user
        from app.api.deps import get_db
        from app.db.session import SessionLocal

        def override_get_db():
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()

        async def override_get_current_user():
            return normal_user

        client.app.dependency_overrides[get_db] = override_get_db
        client.app.dependency_overrides[get_current_user] = override_get_current_user
        try:
            resp = client.get("/api/v1/openapi_knowledge/documents/1")
            assert resp.status_code == 403
        finally:
            client.app.dependency_overrides.clear()


class TestListDocuments:
    """测试 GET /documents。"""

    def test_list_documents_pagination(self, auth_client: TestClient, db_session: Session):
        """分页列表应正确返回。"""
        for i in range(3):
            crud.create_document(
                db=db_session,
                uploaded_by=1,
                filename=f"api{i}.json",
                content_hash=f"hash{i}",
                status="completed",
            )
        resp = auth_client.get("/api/v1/openapi_knowledge/documents?skip=0&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2

    def test_list_documents_status_filter(self, auth_client: TestClient, db_session: Session):
        """状态过滤应生效。"""
        crud.create_document(
            db=db_session, uploaded_by=1, filename="a.json",
            content_hash="h1", status="pending",
        )
        crud.create_document(
            db=db_session, uploaded_by=1, filename="b.json",
            content_hash="h2", status="completed",
        )
        resp = auth_client.get("/api/v1/openapi_knowledge/documents?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

    def test_list_documents_invalid_status_returns_422(self, auth_client: TestClient):
        """非法状态值应返回 422。"""
        resp = auth_client.get("/api/v1/openapi_knowledge/documents?status=abc")
        assert resp.status_code == 422


class TestDeleteDocument:
    """测试 DELETE /documents/{document_id}。"""

    def test_delete_document(self, auth_client: TestClient, db_session: Session):
        """管理员应能删除文档。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.json",
            content_hash="hash123",
            status="completed",
        )
        doc_id = doc.id
        resp = auth_client.delete(f"/api/v1/openapi_knowledge/documents/{doc_id}")
        assert resp.status_code == 204
        assert crud.get_document_by_id(db_session, doc_id) is None

    def test_delete_document_not_found(self, auth_client: TestClient):
        """删除不存在的文档应返回 404。"""
        resp = auth_client.delete("/api/v1/openapi_knowledge/documents/99999")
        assert resp.status_code == 404


class TestEndpointApi:
    """测试端点列表与检索接口。"""

    def test_list_endpoints_should_not_expose_embedding(
        self, auth_client: TestClient, db_session: Session
    ):
        """端点列表响应不应暴露向量字段。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.json",
            content_hash="hash-endpoint-list",
            status="completed",
        )
        crud.create_endpoint_embedding(
            db=db_session,
            document_id=doc.id,
            chunk_id="ep_list_1",
            path="/users",
            method="GET",
            content="GET /users",
            embedding=[0.1] * 1024,
            content_hash="ep-hash-1",
        )

        resp = auth_client.get("/api/v1/openapi_knowledge/endpoints")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "embedding" not in data["items"][0]


class TestProcessDocumentTask:
    """测试后台解析任务的状态流转。"""

    @pytest.mark.asyncio
    @patch("app.api.v1.openapi_knowledge.OpenAPIParserService")
    @patch("app.api.v1.openapi_knowledge.crud")
    @patch("app.db.session.SessionLocal")
    async def test_parse_failure_sets_failed_status(
        self, mock_session_local, mock_crud, mock_parser_cls
    ):
        """解析失败后应更新文档状态为 failed 并记录错误信息。"""
        # 让 parser.parse 抛出异常
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = ValueError("YAML 解析失败: broken")
        mock_parser_cls.return_value = mock_parser

        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db

        from app.api.v1.openapi_knowledge import _process_openapi_document
        await _process_openapi_document(1, b"broken yaml", "api.yaml")

        # 验证先更新为 processing
        mock_crud.update_document_status.assert_any_call(
            mock_db, 1, "processing"
        )
        # 验证失败后更新为 failed
        mock_crud.update_document_status.assert_any_call(
            mock_db, 1, "failed", error_message="YAML 解析失败: broken"
        )

    @pytest.mark.asyncio
    @patch("app.services.openapi_embedding_service.get_embedding_client")
    @patch("app.api.v1.openapi_knowledge.OpenAPIParserService")
    @patch("app.api.v1.openapi_knowledge.crud")
    @patch("app.db.session.SessionLocal")
    async def test_parse_success_sets_completed_status(
        self, mock_session_local, mock_crud, mock_parser_cls, mock_get_embed
    ):
        """解析成功后应更新文档状态为 completed 并记录端点数量。"""
        mock_embed_client = MagicMock()
        mock_embed_client.embed_documents.return_value = [
            [0.1] * 1024,
            [0.2] * 1024,
        ]
        mock_get_embed.return_value = mock_embed_client

        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            {"chunk_id": "ep_1", "path": "/users", "method": "GET", "content": "GET /users", "content_hash": "ch1"},
            {"chunk_id": "ep_2", "path": "/posts", "method": "POST", "content": "POST /posts", "content_hash": "ch2"},
        ]
        mock_parser_cls.return_value = mock_parser

        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db

        from app.api.v1.openapi_knowledge import _process_openapi_document
        await _process_openapi_document(1, b"{}", "api.json")

        mock_crud.update_document_status.assert_any_call(
            mock_db, 1, "processing"
        )
        mock_crud.update_document_status.assert_any_call(
            mock_db, 1, "completed", endpoint_count=2, chunk_count=2
        )
