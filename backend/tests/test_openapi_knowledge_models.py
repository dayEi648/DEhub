"""OpenAPI 知识库数据模型与 CRUD 单元测试（阶段 1）。"""

import pytest
from sqlalchemy.orm import Session

from app.models.openapi_document import OpenAPIDocument
from app.models.openapi_endpoint_embedding import OpenAPIEndpointEmbedding
from app.crud import openapi_knowledge as crud


class TestOpenAPIDocumentModel:
    """测试 OpenAPIDocument ORM 模型。"""

    def test_create_document(self, db_session: Session):
        """应能创建 OpenAPI 文档记录并正确存储字段。"""
        doc = OpenAPIDocument(
            uploaded_by=1,
            filename="test.yaml",
            content_hash="abc123",
            status="pending",
            endpoint_count=0,
            chunk_count=0,
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        assert doc.id is not None
        assert doc.uploaded_by == 1
        assert doc.filename == "test.yaml"
        assert doc.content_hash == "abc123"
        assert doc.status == "pending"
        assert doc.endpoint_count == 0
        assert doc.chunk_count == 0
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_status_enum_constraint(self, db_session: Session):
        """status 字段应接受计划中的四个枚举值。"""
        for status in ["pending", "processing", "completed", "failed"]:
            doc = OpenAPIDocument(
                uploaded_by=1,
                filename=f"test_{status}.yaml",
                content_hash=f"hash_{status}",
                status=status,
            )
            db_session.add(doc)
            db_session.commit()
            db_session.refresh(doc)
            assert doc.status == status


class TestOpenAPIEndpointEmbeddingModel:
    """测试 OpenAPIEndpointEmbedding ORM 模型。"""

    def test_create_endpoint_embedding(self, db_session: Session):
        """应能创建端点向量记录并正确存储字段。"""
        doc = OpenAPIDocument(
            uploaded_by=1,
            filename="test.yaml",
            content_hash="abc123",
            status="completed",
        )
        db_session.add(doc)
        db_session.commit()

        embedding = OpenAPIEndpointEmbedding(
            document_id=doc.id,
            chunk_id="ep_1_GET_users_1",
            path="/users",
            method="GET",
            summary="获取用户列表",
            description="分页获取所有用户",
            tags=["user"],
            operation_id="listUsers",
            content="GET /users - 获取用户列表",
            embedding=[0.1] * 1024,
            content_hash="ep_hash_1",
        )
        db_session.add(embedding)
        db_session.commit()
        db_session.refresh(embedding)

        assert embedding.id is not None
        assert embedding.document_id == doc.id
        assert embedding.chunk_id == "ep_1_GET_users_1"
        assert embedding.path == "/users"
        assert embedding.method == "GET"
        assert embedding.summary == "获取用户列表"
        assert embedding.description == "分页获取所有用户"
        assert embedding.tags == ["user"]
        assert embedding.operation_id == "listUsers"
        assert embedding.content == "GET /users - 获取用户列表"
        assert len(embedding.embedding) == 1024
        assert embedding.content_hash == "ep_hash_1"

    def test_chunk_id_unique_constraint(self, db_session: Session):
        """相同 chunk_id 应触发唯一性约束错误。"""
        doc = OpenAPIDocument(
            uploaded_by=1,
            filename="test.yaml",
            content_hash="abc123",
            status="completed",
        )
        db_session.add(doc)
        db_session.commit()

        ep1 = OpenAPIEndpointEmbedding(
            document_id=doc.id,
            chunk_id="dup_chunk",
            path="/a",
            method="GET",
            content="A",
            embedding=[0.1] * 1024,
        )
        db_session.add(ep1)
        db_session.commit()

        ep2 = OpenAPIEndpointEmbedding(
            document_id=doc.id,
            chunk_id="dup_chunk",
            path="/b",
            method="POST",
            content="B",
            embedding=[0.2] * 1024,
        )
        db_session.add(ep2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestOpenapiKnowledgeCrud:
    """测试 openapi_knowledge CRUD 操作。"""

    # ------------------------------------------------------------------
    # 文档 CRUD
    # ------------------------------------------------------------------

    def test_create_document(self, db_session: Session):
        """create_document 应返回新建记录。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="pending",
        )
        assert doc.id is not None
        assert doc.filename == "api.yaml"
        assert doc.status == "pending"

    def test_get_document_by_id(self, db_session: Session):
        """get_document_by_id 应正确返回记录。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="pending",
        )
        found = crud.get_document_by_id(db_session, doc.id)
        assert found is not None
        assert found.id == doc.id

    def test_get_document_by_id_not_found(self, db_session: Session):
        """get_document_by_id 对不存在 ID 应返回 None。"""
        assert crud.get_document_by_id(db_session, 99999) is None

    def test_get_document_by_content_hash(self, db_session: Session):
        """get_document_by_content_hash 应按 hash 查询。"""
        crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="unique_hash",
            status="pending",
        )
        found = crud.get_document_by_content_hash(db_session, "unique_hash")
        assert found is not None
        assert found.content_hash == "unique_hash"

    def test_list_documents(self, db_session: Session):
        """list_documents 应支持分页和状态过滤。"""
        for i in range(5):
            crud.create_document(
                db=db_session,
                uploaded_by=1,
                filename=f"api{i}.yaml",
                content_hash=f"hash{i}",
                status="completed" if i % 2 == 0 else "pending",
            )

        all_docs, total = crud.list_documents(db_session, skip=0, limit=10)
        assert total == 5
        assert len(all_docs) == 5

        pending_docs, pending_total = crud.list_documents(
            db_session, skip=0, limit=10, status="pending"
        )
        assert pending_total == 2
        assert all(d.status == "pending" for d in pending_docs)

        paged, paged_total = crud.list_documents(db_session, skip=3, limit=2)
        assert paged_total == 5
        assert len(paged) == 2

    def test_update_document_status(self, db_session: Session):
        """update_document_status 应更新状态和计数。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="pending",
        )
        updated = crud.update_document_status(
            db=db_session,
            document_id=doc.id,
            status="completed",
            endpoint_count=10,
            chunk_count=10,
        )
        assert updated is not None
        assert updated.status == "completed"
        assert updated.endpoint_count == 10
        assert updated.chunk_count == 10

    def test_update_document_status_failed(self, db_session: Session):
        """update_document_status 应支持写入失败原因。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="processing",
        )
        updated = crud.update_document_status(
            db=db_session,
            document_id=doc.id,
            status="failed",
            error_message="解析失败：无效的 YAML",
        )
        assert updated.status == "failed"
        assert updated.error_message == "解析失败：无效的 YAML"

    def test_delete_document_cascades_endpoints(self, db_session: Session):
        """删除文档应级联删除其下所有端点向量。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="completed",
        )
        doc_id = doc.id
        crud.create_endpoint_embedding(
            db=db_session,
            document_id=doc_id,
            chunk_id="ep_1",
            path="/users",
            method="GET",
            content="GET /users",
            embedding=[0.1] * 1024,
            content_hash="eph1",
        )
        db_session.commit()

        # 确认端点存在
        eps_before = crud.list_endpoints(db_session, document_id=doc_id)
        assert len(eps_before[0]) == 1

        crud.delete_document(db_session, doc_id)

        assert crud.get_document_by_id(db_session, doc_id) is None
        eps_after = crud.list_endpoints(db_session, document_id=doc_id)
        assert len(eps_after[0]) == 0

    # ------------------------------------------------------------------
    # 端点 CRUD
    # ------------------------------------------------------------------

    def test_create_endpoint_embedding(self, db_session: Session):
        """create_endpoint_embedding 应返回新建记录。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="completed",
        )
        ep = crud.create_endpoint_embedding(
            db=db_session,
            document_id=doc.id,
            chunk_id="ep_1",
            path="/users",
            method="GET",
            content="GET /users",
            embedding=[0.1] * 1024,
            content_hash="eph1",
        )
        assert ep.id is not None
        assert ep.document_id == doc.id

    def test_list_endpoints_with_filters(self, db_session: Session):
        """list_endpoints 应支持 document_id、method、tag 过滤。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="completed",
        )
        crud.create_endpoint_embedding(
            db=db_session,
            document_id=doc.id,
            chunk_id="ep_1",
            path="/users",
            method="GET",
            tags=["user"],
            content="GET /users",
            embedding=[0.1] * 1024,
            content_hash="eph1",
        )
        crud.create_endpoint_embedding(
            db=db_session,
            document_id=doc.id,
            chunk_id="ep_2",
            path="/users",
            method="POST",
            tags=["user"],
            content="POST /users",
            embedding=[0.2] * 1024,
            content_hash="eph2",
        )
        crud.create_endpoint_embedding(
            db=db_session,
            document_id=doc.id,
            chunk_id="ep_3",
            path="/posts",
            method="GET",
            tags=["blog"],
            content="GET /posts",
            embedding=[0.3] * 1024,
            content_hash="eph3",
        )
        db_session.commit()

        all_eps, total = crud.list_endpoints(db_session, skip=0, limit=10)
        assert total == 3

        get_eps, _ = crud.list_endpoints(db_session, method="GET")
        assert len(get_eps) == 2
        assert all(e.method == "GET" for e in get_eps)

        user_eps, _ = crud.list_endpoints(db_session, tag="user")
        assert len(user_eps) == 2

        doc_eps, _ = crud.list_endpoints(db_session, document_id=doc.id)
        assert len(doc_eps) == 3

    def test_delete_endpoint_by_id(self, db_session: Session):
        """delete_endpoint_by_id 应删除指定端点。"""
        doc = crud.create_document(
            db=db_session,
            uploaded_by=1,
            filename="api.yaml",
            content_hash="hash123",
            status="completed",
        )
        ep = crud.create_endpoint_embedding(
            db=db_session,
            document_id=doc.id,
            chunk_id="ep_1",
            path="/users",
            method="GET",
            content="GET /users",
            embedding=[0.1] * 1024,
            content_hash="eph1",
        )
        db_session.commit()

        deleted = crud.delete_endpoint_by_id(db_session, ep.id)
        assert deleted is True

        eps, _ = crud.list_endpoints(db_session, document_id=doc.id)
        assert len(eps) == 0

    def test_delete_endpoint_by_id_not_found(self, db_session: Session):
        """delete_endpoint_by_id 对不存在 ID 应返回 False。"""
        assert crud.delete_endpoint_by_id(db_session, 99999) is False
