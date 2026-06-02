"""内容审核管理员 API 集成测试。

测试覆盖：
- 列表查询（分页、筛选）
- 单条详情
- 重试接口（权限、状态校验）
- 统计概览
- 导出接口（JSON/CSV）
- 普通用户 403 权限控制
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.crud import content_moderation as cm_crud
from app.models.content_moderation_record import ContentModerationRecord
from app.models.user import User


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_moderation_records(db_session: Session, admin_user: User):
    """创建多条审核记录，覆盖不同状态和风险等级。"""
    records = []

    # pending
    r1 = cm_crud.create_moderation_record(
        db_session,
        task_id="task-pending-001",
        target_type="blog_post",
        target_id=1,
        target_version="v1",
        trigger_action="publish",
        original_snapshot={"title": "Test", "content_md": "Hello"},
        created_by_user_id=admin_user.id,
    )
    records.append(r1)

    # passed
    r2 = cm_crud.create_moderation_record(
        db_session,
        task_id="task-passed-002",
        target_type="comment",
        target_id=2,
        target_version="v1",
        trigger_action="create",
        original_snapshot={"content": "Nice comment"},
        created_by_user_id=admin_user.id,
    )
    cm_crud.update_moderation_record(
        db_session, r2.id,
        status="passed",
        risk_level="none",
        categories=[],
        finished_at=datetime.now(timezone.utc),
    )
    records.append(r2)

    # blocked
    r3 = cm_crud.create_moderation_record(
        db_session,
        task_id="task-blocked-003",
        target_type="forum_post",
        target_id=3,
        target_version="v1",
        trigger_action="create",
        original_snapshot={"title": "Spam", "content": "Buy now"},
        created_by_user_id=admin_user.id,
    )
    cm_crud.update_moderation_record(
        db_session, r3.id,
        status="blocked",
        risk_level="high",
        categories=["广告"],
        finished_at=datetime.now(timezone.utc),
    )
    records.append(r3)

    # review_failed
    r4 = cm_crud.create_moderation_record(
        db_session,
        task_id="task-failed-004",
        target_type="user",
        target_id=4,
        target_version="v1",
        trigger_action="create",
        original_snapshot={"username": "user", "personal_profile": "test"},
        created_by_user_id=admin_user.id,
    )
    cm_crud.update_moderation_record(
        db_session, r4.id,
        status="review_failed",
        risk_level="none",
        error_type="JSONDecodeError",
        error_message="Invalid JSON from LLM",
        finished_at=datetime.now(timezone.utc),
    )
    records.append(r4)

    # action_failed
    r5 = cm_crud.create_moderation_record(
        db_session,
        task_id="task-action-failed-005",
        target_type="forum_reply",
        target_id=5,
        target_version="v1",
        trigger_action="create",
        original_snapshot={"content": "Bad reply"},
        created_by_user_id=admin_user.id,
    )
    cm_crud.update_moderation_record(
        db_session, r5.id,
        status="action_failed",
        risk_level="medium",
        categories=["辱骂"],
        error_type="ActionFailed",
        error_message="Target object deleted",
        finished_at=datetime.now(timezone.utc),
    )
    records.append(r5)

    # stale
    r6 = cm_crud.create_moderation_record(
        db_session,
        task_id="task-stale-006",
        target_type="forum_zone",
        target_id=6,
        target_version="v1",
        trigger_action="update",
        original_snapshot={"zone_name": "Zone", "description": "Desc"},
        created_by_user_id=admin_user.id,
    )
    cm_crud.update_moderation_record(
        db_session, r6.id,
        status="stale",
        risk_level="none",
        error_type="StalenessError",
        error_message="内容已过期",
        finished_at=datetime.now(timezone.utc),
    )
    records.append(r6)

    db_session.commit()
    return records


@pytest.fixture
def normal_user_client(client: TestClient, db_session: Session, normal_user: User):
    """返回以普通用户身份认证的 TestClient。"""
    from app.core.security import get_current_user
    from app.api.deps import get_db

    def override_get_db():
        yield db_session

    async def override_get_current_user():
        return normal_user

    client.app.dependency_overrides[get_db] = override_get_db
    client.app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    client.app.dependency_overrides.clear()


# ------------------------------------------------------------------
# 权限测试
# ------------------------------------------------------------------

class TestPermission:
    """测试普通用户访问管理员接口返回 403。"""

    def test_list_records_normal_user_403(self, normal_user_client: TestClient):
        resp = normal_user_client.get("/api/v1/content_moderation/records")
        assert resp.status_code == 403

    def test_get_record_detail_normal_user_403(self, normal_user_client: TestClient):
        resp = normal_user_client.get("/api/v1/content_moderation/records/1")
        assert resp.status_code == 403

    def test_retry_record_normal_user_403(self, normal_user_client: TestClient):
        resp = normal_user_client.post("/api/v1/content_moderation/records/1/retry")
        assert resp.status_code == 403

    def test_get_stats_normal_user_403(self, normal_user_client: TestClient):
        resp = normal_user_client.get("/api/v1/content_moderation/stats")
        assert resp.status_code == 403

    def test_export_records_normal_user_403(self, normal_user_client: TestClient):
        resp = normal_user_client.get("/api/v1/content_moderation/records/export")
        assert resp.status_code == 403


# ------------------------------------------------------------------
# 列表查询测试
# ------------------------------------------------------------------

class TestListRecords:
    """测试 GET /content_moderation/records 列表查询。"""

    def test_list_records_basic(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/records")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == len(sample_moderation_records)
        assert len(data["items"]) == len(sample_moderation_records)

    def test_list_records_pagination(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/records?skip=0&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 6

        resp = auth_client.get("/api/v1/content_moderation/records?skip=2&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2

    def test_list_records_filter_by_status(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/records?status=passed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "passed"

    def test_list_records_filter_by_target_type(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/records?target_type=blog_post")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["target_type"] == "blog_post"

    def test_list_records_filter_by_risk_level(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/records?risk_level=high")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["risk_level"] == "high"

    def test_list_records_filter_by_user_id(self, auth_client: TestClient, sample_moderation_records, admin_user):
        resp = auth_client.get(f"/api/v1/content_moderation/records?user_id={admin_user.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 6

    def test_list_records_invalid_status_422(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/content_moderation/records?status=invalid")
        assert resp.status_code == 422

    def test_list_records_invalid_target_type_422(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/content_moderation/records?target_type=invalid")
        assert resp.status_code == 422

    def test_list_records_combined_filters(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get(
            "/api/v1/content_moderation/records"
            "?status=blocked&target_type=forum_post&risk_level=high"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "blocked"
        assert data["items"][0]["target_type"] == "forum_post"
        assert data["items"][0]["risk_level"] == "high"

    def test_list_records_time_range(self, auth_client: TestClient, sample_moderation_records):
        from urllib.parse import quote
        now = datetime.now(timezone.utc).isoformat()
        past = datetime(2000, 1, 1, tzinfo=timezone.utc).isoformat()

        resp = auth_client.get(
            f"/api/v1/content_moderation/records?start_time={quote(past)}&end_time={quote(now)}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 6


# ------------------------------------------------------------------
# 详情测试
# ------------------------------------------------------------------

class TestGetRecordDetail:
    """测试 GET /content_moderation/records/{id} 详情接口。"""

    def test_get_record_detail_success(self, auth_client: TestClient, sample_moderation_records):
        record = sample_moderation_records[0]
        resp = auth_client.get(f"/api/v1/content_moderation/records/{record.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == record.id
        assert data["task_id"] == record.task_id
        assert data["target_type"] == record.target_type
        assert data["status"] == record.status
        assert "original_snapshot" in data
        assert data["original_snapshot"] is not None

    def test_get_record_detail_with_full_data(self, auth_client: TestClient, sample_moderation_records):
        """详情接口应包含 moderation_result、action_plan、action_result 等完整数据。"""
        record = sample_moderation_records[2]  # blocked record
        resp = auth_client.get(f"/api/v1/content_moderation/records/{record.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == record.id
        assert data["status"] == "blocked"
        assert data["risk_level"] == "high"
        assert data["categories"] == ["广告"]
        assert "original_snapshot" in data
        assert "moderation_result" in data
        assert "action_plan" in data
        assert "action_result" in data

    def test_get_record_detail_not_found(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/content_moderation/records/99999")
        assert resp.status_code == 404
        assert "不存在" in resp.json()["message"]


# ------------------------------------------------------------------
# 重试接口测试
# ------------------------------------------------------------------

class TestRetryRecord:
    """测试 POST /content_moderation/records/{id}/retry 重试接口。"""

    def test_retry_review_failed_success(self, auth_client: TestClient, sample_moderation_records, db_session):
        record = sample_moderation_records[3]  # review_failed
        assert record.status == "review_failed"
        original_task_id = record.task_id

        resp = auth_client.post(f"/api/v1/content_moderation/records/{record.id}/retry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == record.id
        assert data["status"] == "pending"
        assert data["message"] == "审核任务已重新调度"
        assert data["task_id"] != original_task_id  # 新 task_id

    def test_retry_action_failed_success(self, auth_client: TestClient, sample_moderation_records):
        record = sample_moderation_records[4]  # action_failed
        resp = auth_client.post(f"/api/v1/content_moderation/records/{record.id}/retry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"

    def test_retry_stale_success(self, auth_client: TestClient, sample_moderation_records):
        record = sample_moderation_records[5]  # stale
        resp = auth_client.post(f"/api/v1/content_moderation/records/{record.id}/retry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"

    def test_retry_pending_status_400(self, auth_client: TestClient, sample_moderation_records):
        record = sample_moderation_records[0]  # pending
        resp = auth_client.post(f"/api/v1/content_moderation/records/{record.id}/retry")
        assert resp.status_code == 400
        assert "不允许重试" in resp.json()["message"]

    def test_retry_passed_status_400(self, auth_client: TestClient, sample_moderation_records):
        record = sample_moderation_records[1]  # passed
        resp = auth_client.post(f"/api/v1/content_moderation/records/{record.id}/retry")
        assert resp.status_code == 400
        assert "不允许重试" in resp.json()["message"]

    def test_retry_blocked_status_400(self, auth_client: TestClient, sample_moderation_records):
        record = sample_moderation_records[2]  # blocked
        resp = auth_client.post(f"/api/v1/content_moderation/records/{record.id}/retry")
        assert resp.status_code == 400
        assert "不允许重试" in resp.json()["message"]

    def test_retry_not_found(self, auth_client: TestClient):
        resp = auth_client.post("/api/v1/content_moderation/records/99999/retry")
        assert resp.status_code == 404
        assert "不存在" in resp.json()["message"]


# ------------------------------------------------------------------
# 统计接口测试
# ------------------------------------------------------------------

class TestGetStats:
    """测试 GET /content_moderation/stats 统计接口。"""

    def test_get_stats(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "today_count" in data
        assert "failed_count" in data
        assert "blocked_count" in data
        assert "avg_latency_ms" in data
        assert data["total"] == 6
        assert data["failed_count"] == 2  # review_failed + action_failed
        assert data["blocked_count"] == 1

    def test_get_stats_empty(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/content_moderation/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["today_count"] == 0
        assert data["failed_count"] == 0
        assert data["blocked_count"] == 0
        assert data["avg_latency_ms"] is None


# ------------------------------------------------------------------
# 导出接口测试
# ------------------------------------------------------------------

class TestExportRecords:
    """测试 GET /content_moderation/records/export 导出接口。"""

    def test_export_json(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/records/export?format=json")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"
        assert "attachment" in resp.headers["content-disposition"]
        assert ".json" in resp.headers["content-disposition"]

        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 6
        # 验证包含完整敏感数据
        assert "original_snapshot" in data[0]

    def test_export_csv(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get("/api/v1/content_moderation/records/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]
        assert ".csv" in resp.headers["content-disposition"]

        content = resp.text
        lines = content.strip().split("\n")
        assert len(lines) == 7  # header + 6 records
        assert "id,task_id,trace_id" in lines[0]

    def test_export_with_filters(self, auth_client: TestClient, sample_moderation_records):
        resp = auth_client.get(
            "/api/v1/content_moderation/records/export"
            "?format=json&status=blocked&target_type=forum_post"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "blocked"
        assert data[0]["target_type"] == "forum_post"

    def test_export_empty_json(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/content_moderation/records/export?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data == []

    def test_export_invalid_format_422(self, auth_client: TestClient):
        resp = auth_client.get("/api/v1/content_moderation/records/export?format=xml")
        assert resp.status_code == 422
