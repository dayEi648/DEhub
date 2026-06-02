"""内容审核模块测试。

覆盖：
- ContentModerationAgent 解析与异常处理
- ContentModerationService 入队与执行流程
- ContentSanitizer 文本替换逻辑
- 与 agent_traces 的落库打通
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.crud import content_moderation as cm_crud
from app.core.config import settings
from app.models.blog_post import BlogPost
from app.models.comment import Comment
from app.models.content_moderation_record import ContentModerationRecord
from app.models.forum_post import ForumPost
from app.models.forum_reply import ForumReply
from app.models.forum_zone import ForumZone
from app.models.user import User
from app.schemas.content_moderation import FlaggedSpan, ModerationAgentOutput
from app.services.content_moderation_agent import ContentModerationAgent
from app.services.content_moderation_sanitizer import sanitize_content
from app.services.content_moderation_service import ContentModerationService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def moderation_service(db_session: Session):
    return ContentModerationService(db_session)


@pytest.fixture
def sample_snapshot():
    return {
        "title": "Test Blog Post",
        "content_md": "This is a test blog post with some content.",
    }


# ------------------------------------------------------------------
# Agent 解析测试
# ------------------------------------------------------------------

class TestContentModerationAgent:
    def test_parse_output_pass(self):
        agent = ContentModerationAgent()
        raw = json.dumps({
            "verdict": "pass",
            "risk_level": "none",
            "categories": [],
            "reason": "内容正常",
            "flagged_spans": [],
            "suggested_action": "none",
        })
        result = agent._parse_output(raw)
        assert result.verdict == "pass"
        assert result.risk_level == "none"
        assert result.flagged_spans == []
        assert result.suggested_action == "none"

    def test_parse_output_block(self):
        agent = ContentModerationAgent()
        raw = json.dumps({
            "verdict": "block",
            "risk_level": "high",
            "categories": ["辱骂"],
            "reason": "包含辱骂词汇",
            "flagged_spans": [
                {
                    "field": "content_md",
                    "text": "some bad word",
                    "start": 27,
                    "end": 40,
                    "category": "辱骂",
                    "confidence": 0.95,
                }
            ],
            "suggested_action": "mask_text",
        })
        result = agent._parse_output(raw)
        assert result.verdict == "block"
        assert result.risk_level == "high"
        assert len(result.flagged_spans) == 1
        assert result.flagged_spans[0].field == "content_md"
        assert result.suggested_action == "mask_text"

    def test_parse_output_wrapped_in_markdown(self):
        agent = ContentModerationAgent()
        raw = '```json\n' + json.dumps({
            "verdict": "pass",
            "risk_level": "none",
            "categories": [],
            "reason": "OK",
            "flagged_spans": [],
            "suggested_action": "none",
        }) + '\n```'
        result = agent._parse_output(raw)
        assert result.verdict == "pass"

    def test_parse_output_invalid_json(self):
        agent = ContentModerationAgent()
        with pytest.raises(json.JSONDecodeError):
            agent._parse_output("not json at all")

    def test_parse_output_block_without_spans_raises(self):
        agent = ContentModerationAgent()
        raw = json.dumps({
            "verdict": "block",
            "risk_level": "high",
            "categories": [],
            "reason": "bad",
            "flagged_spans": [],
            "suggested_action": "none",
        })
        with pytest.raises(ValueError, match="flagged_spans 不能为空"):
            agent._parse_output(raw)

    @pytest.mark.asyncio
    async def test_moderate_mock_llm_pass(self, db_session: Session):
        """mock LLM 返回 pass，验证 trace 能落库。"""
        agent = ContentModerationAgent()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "verdict": "pass",
            "risk_level": "none",
            "categories": [],
            "reason": "内容正常",
            "flagged_spans": [],
            "suggested_action": "none",
        })
        mock_response.usage_metadata = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
        mock_response.response_metadata = {}

        with patch("app.services.content_moderation_agent.create_llm_small_client") as mock_client:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_llm

            output, trace_id = await agent.moderate(
                content_snapshot={"content": "hello"},
                target_type="comment",
                user_id=1,
            )

        assert output is not None
        assert output.verdict == "pass"
        assert trace_id is not None
        assert trace_id.startswith("cm-")

        # 验证 trace 已落库
        from app.crud import agent_trace as trace_crud
        trace = trace_crud.get_agent_trace_by_trace_id(db_session, trace_id)
        assert trace is not None
        assert trace.status == "completed"
        assert trace.graph_name == "content_moderation"

    @pytest.mark.asyncio
    async def test_moderate_mock_llm_block(self, db_session: Session):
        """mock LLM 返回 block，验证 trace 能落库。"""
        agent = ContentModerationAgent()
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "verdict": "block",
            "risk_level": "medium",
            "categories": ["广告"],
            "reason": "包含广告信息",
            "flagged_spans": [
                {
                    "field": "content",
                    "text": "buy now",
                    "start": 0,
                    "end": 7,
                    "category": "广告",
                    "confidence": 0.88,
                }
            ],
            "suggested_action": "mask_text",
        })
        mock_response.usage_metadata = {}
        mock_response.response_metadata = {}

        with patch("app.services.content_moderation_agent.create_llm_small_client") as mock_client:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_llm

            output, trace_id = await agent.moderate(
                content_snapshot={"content": "buy now"},
                target_type="comment",
            )

        assert output is not None
        assert output.verdict == "block"
        assert trace_id is not None

    @pytest.mark.asyncio
    async def test_moderate_mock_llm_json_error(self, db_session: Session):
        """mock LLM 返回非法 JSON，验证记录 review_failed 且 trace 落库。"""
        agent = ContentModerationAgent()
        mock_response = MagicMock()
        mock_response.content = "invalid json {{{"
        mock_response.usage_metadata = {}
        mock_response.response_metadata = {}

        with patch("app.services.content_moderation_agent.create_llm_small_client") as mock_client:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_llm

            output, trace_id = await agent.moderate(
                content_snapshot={"content": "test"},
                target_type="comment",
            )

        assert output is None
        assert trace_id is not None

        from app.crud import agent_trace as trace_crud
        trace = trace_crud.get_agent_trace_by_trace_id(db_session, trace_id)
        assert trace is not None
        assert trace.status == "failed"

    @pytest.mark.asyncio
    async def test_moderate_mock_llm_timeout(self, db_session: Session):
        """mock LLM 调用超时，验证 trace 落库。"""
        agent = ContentModerationAgent()

        with patch("app.services.content_moderation_agent.create_llm_small_client") as mock_client:
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock(side_effect=TimeoutError("LLM timeout"))
            mock_client.return_value = mock_llm

            output, trace_id = await agent.moderate(
                content_snapshot={"content": "test"},
                target_type="comment",
            )

        assert output is None
        assert trace_id is not None

        from app.crud import agent_trace as trace_crud
        trace = trace_crud.get_agent_trace_by_trace_id(db_session, trace_id)
        assert trace is not None
        assert trace.status == "failed"
        assert trace.error_type == "TimeoutError"


# ------------------------------------------------------------------
# Service 测试
# ------------------------------------------------------------------

def _create_mock_trace(db: Session, trace_id: str):
    """在数据库中创建一个模拟的 agent_trace，用于满足外键约束。"""
    from app.crud import agent_trace as trace_crud
    from datetime import datetime, timezone
    trace_crud.create_agent_trace(
        db,
        trace_id=trace_id,
        status="completed",
        started_at=datetime.now(timezone.utc),
    )


class TestContentModerationService:
    def test_enqueue_respects_disabled_flag(
        self,
        db_session: Session,
        moderation_service,
        sample_snapshot,
        admin_user,
        monkeypatch,
    ):
        monkeypatch.setattr(settings, "CONTENT_MODERATION_ENABLED", False)
        record = moderation_service.enqueue(
            target_type="blog_post",
            target_id=99,
            target_version="v1",
            trigger_action="publish",
            snapshot=sample_snapshot,
            created_by_user_id=admin_user.id,
        )
        assert record is None

    def test_enqueue_creates_record(self, db_session: Session, moderation_service, sample_snapshot, admin_user):
        record = moderation_service.enqueue(
            target_type="blog_post",
            target_id=1,
            target_version="v1",
            trigger_action="publish",
            snapshot=sample_snapshot,
            created_by_user_id=admin_user.id,
        )
        assert record.id is not None
        assert record.status == "pending"
        assert record.task_id is not None

    def test_enqueue_idempotent_same_version(self, db_session: Session, moderation_service, sample_snapshot, admin_user):
        record1 = moderation_service.enqueue(
            target_type="blog_post",
            target_id=2,
            target_version="v1",
            trigger_action="publish",
            snapshot=sample_snapshot,
            created_by_user_id=admin_user.id,
        )
        record2 = moderation_service.enqueue(
            target_type="blog_post",
            target_id=2,
            target_version="v1",
            trigger_action="publish",
            snapshot=sample_snapshot,
            created_by_user_id=admin_user.id,
        )
        # 同一版本应返回已有记录
        assert record1.id == record2.id

    def test_enqueue_different_version_creates_new(self, db_session: Session, moderation_service, sample_snapshot, admin_user):
        record1 = moderation_service.enqueue(
            target_type="blog_post",
            target_id=3,
            target_version="v1",
            trigger_action="publish",
            snapshot=sample_snapshot,
            created_by_user_id=admin_user.id,
        )
        record2 = moderation_service.enqueue(
            target_type="blog_post",
            target_id=3,
            target_version="v2",
            trigger_action="update",
            snapshot=sample_snapshot,
            created_by_user_id=admin_user.id,
        )
        assert record1.id != record2.id

    def test_enqueue_failed_same_version_returns_existing(
        self,
        db_session: Session,
        moderation_service,
        admin_user,
    ):
        record1 = moderation_service.enqueue(
            target_type="comment",
            target_id=88,
            target_version="v1",
            trigger_action="create",
            snapshot={"content": "hello"},
            created_by_user_id=admin_user.id,
        )
        cm_crud.update_moderation_record(
            db_session,
            record1.id,
            status="review_failed",
        )

        record2 = moderation_service.enqueue(
            target_type="comment",
            target_id=88,
            target_version="v1",
            trigger_action="create",
            snapshot={"content": "hello"},
            created_by_user_id=admin_user.id,
        )

        assert record2 is not None
        assert record1.id == record2.id

    @pytest.mark.asyncio
    async def test_execute_moderation_pass(self, db_session: Session, admin_user, blog_category):
        post = BlogPost(
            title="Test",
            slug="test-moderation-pass",
            content_md="Hello world",
            user_id=admin_user.id,
            category_id=blog_category.id,
            status="published",
        )
        db_session.add(post)
        db_session.commit()
        db_session.refresh(post)

        service = ContentModerationService(db_session)
        record = service.enqueue(
            target_type="blog_post",
            target_id=post.id,
            target_version=post.updated_at.isoformat(),
            trigger_action="publish",
            snapshot={"title": post.title, "content_md": post.content_md},
            created_by_user_id=admin_user.id,
        )

        _create_mock_trace(db_session, "cm-test-pass")
        mock_output = ModerationAgentOutput(
            verdict="pass",
            risk_level="none",
            categories=[],
            reason="OK",
            flagged_spans=[],
            suggested_action="none",
        )
        with patch.object(
            ContentModerationAgent, "moderate", return_value=(mock_output, "cm-test-pass")
        ):
            await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        assert refreshed.status == "passed"
        assert refreshed.trace_id == "cm-test-pass"
        assert refreshed.model_name == settings.LLM_SMALL_MODEL
        assert post.status == "published"

    @pytest.mark.asyncio
    async def test_execute_moderation_block_blog(self, db_session: Session, admin_user, blog_category):
        post = BlogPost(
            title="Test Block",
            slug="test-moderation-block",
            content_md="Some bad content here",
            user_id=admin_user.id,
            category_id=blog_category.id,
            status="published",
        )
        db_session.add(post)
        db_session.commit()
        db_session.refresh(post)

        service = ContentModerationService(db_session)
        record = service.enqueue(
            target_type="blog_post",
            target_id=post.id,
            target_version=post.updated_at.isoformat(),
            trigger_action="publish",
            snapshot={"title": post.title, "content_md": post.content_md},
            created_by_user_id=admin_user.id,
        )

        _create_mock_trace(db_session, "cm-test-block")
        mock_output = ModerationAgentOutput(
            verdict="block",
            risk_level="high",
            categories=["辱骂"],
            reason="Bad",
            flagged_spans=[
                FlaggedSpan(
                    field="content_md",
                    text="bad content",
                    start=5,
                    end=16,
                    category="辱骂",
                    confidence=0.95,
                )
            ],
            suggested_action="unpublish_blog",
        )
        with patch.object(
            ContentModerationAgent, "moderate", return_value=(mock_output, "cm-test-block")
        ):
            await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        assert refreshed.status == "blocked"
        db_session.refresh(post)
        assert post.status == "draft"

    @pytest.mark.asyncio
    async def test_execute_moderation_stale(self, db_session: Session, admin_user, blog_category):
        post = BlogPost(
            title="Stale Test",
            slug="test-moderation-stale",
            content_md="Content",
            user_id=admin_user.id,
            category_id=blog_category.id,
            status="published",
        )
        db_session.add(post)
        db_session.commit()
        db_session.refresh(post)

        old_version = "2020-01-01T00:00:00+00:00"
        service = ContentModerationService(db_session)
        record = service.enqueue(
            target_type="blog_post",
            target_id=post.id,
            target_version=old_version,
            trigger_action="publish",
            snapshot={"title": post.title, "content_md": post.content_md},
            created_by_user_id=admin_user.id,
        )

        await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        assert refreshed.status == "stale"
        assert "过期" in (refreshed.error_message or "")

    @pytest.mark.asyncio
    async def test_execute_moderation_stale_after_agent_does_not_apply_old_action(
        self,
        db_session: Session,
        admin_user,
        blog_category,
    ):
        post = BlogPost(
            title="Race Test",
            slug="test-moderation-race",
            content_md="bad content",
            user_id=admin_user.id,
            category_id=blog_category.id,
            status="published",
        )
        db_session.add(post)
        db_session.commit()
        db_session.refresh(post)

        record = ContentModerationService(db_session).enqueue(
            target_type="blog_post",
            target_id=post.id,
            target_version=post.updated_at.isoformat(),
            trigger_action="publish",
            snapshot={"title": post.title, "content_md": post.content_md},
            created_by_user_id=admin_user.id,
        )
        _create_mock_trace(db_session, "cm-test-race")

        async def fake_moderate(*args, **kwargs):
            post.content_md = "new safe content"
            post.updated_at = post.updated_at + timedelta(seconds=5)
            db_session.commit()
            db_session.refresh(post)
            return (
                ModerationAgentOutput(
                    verdict="block",
                    risk_level="high",
                    categories=["辱骂"],
                    reason="Bad",
                    flagged_spans=[
                        FlaggedSpan(
                            field="content_md",
                            text="bad",
                            start=0,
                            end=3,
                            category="辱骂",
                            confidence=0.95,
                        )
                    ],
                    suggested_action="unpublish_blog",
                ),
                "cm-test-race",
            )

        with patch.object(
            ContentModerationAgent,
            "moderate",
            side_effect=fake_moderate,
        ), patch(
            "app.services.content_moderation_service.BlogPostEmbeddingService.delete_post_embedding",
            return_value=None,
        ), patch(
            "app.services.content_moderation_service.BlogCacheInvalidator.invalidate_all",
            return_value=None,
        ):
            await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        db_session.refresh(post)
        assert refreshed.status == "stale"
        assert post.status == "published"

    @pytest.mark.asyncio
    async def test_execute_moderation_mask_comment(self, db_session: Session, admin_user):
        comment = Comment(
            target_type="blog_post",
            target_id=1,
            user_id=admin_user.id,
            content="This is a bad word in comment",
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)

        service = ContentModerationService(db_session)
        record = service.enqueue(
            target_type="comment",
            target_id=comment.id,
            target_version=comment.updated_at.isoformat(),
            trigger_action="create",
            snapshot={"content": comment.content},
            created_by_user_id=admin_user.id,
        )

        _create_mock_trace(db_session, "cm-test-mask")
        mock_output = ModerationAgentOutput(
            verdict="block",
            risk_level="medium",
            categories=["辱骂"],
            reason="Bad word",
            flagged_spans=[
                FlaggedSpan(
                    field="content",
                    text="bad word",
                    start=12,
                    end=20,
                    category="辱骂",
                    confidence=0.9,
                )
            ],
            suggested_action="mask_text",
        )
        with patch.object(
            ContentModerationAgent, "moderate", return_value=(mock_output, "cm-test-mask")
        ):
            await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        assert refreshed.status == "blocked"
        db_session.refresh(comment)
        assert "bad word" not in comment.content
        assert "*******" in comment.content

    @pytest.mark.asyncio
    async def test_execute_moderation_unknown_field_marks_action_failed(
        self,
        db_session: Session,
        admin_user,
    ):
        comment = Comment(
            target_type="blog_post",
            target_id=1,
            user_id=admin_user.id,
            content="hello world",
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)

        record = ContentModerationService(db_session).enqueue(
            target_type="comment",
            target_id=comment.id,
            target_version=comment.updated_at.isoformat(),
            trigger_action="create",
            snapshot={"content": comment.content},
            created_by_user_id=admin_user.id,
        )
        _create_mock_trace(db_session, "cm-test-unknown-field")
        mock_output = ModerationAgentOutput(
            verdict="block",
            risk_level="high",
            categories=["辱骂"],
            reason="Bad",
            flagged_spans=[
                FlaggedSpan(
                    field="unknown_field",
                    text="hello",
                    start=0,
                    end=5,
                    category="辱骂",
                    confidence=0.95,
                )
            ],
            suggested_action="mask_text",
        )

        with patch.object(
            ContentModerationAgent,
            "moderate",
            return_value=(mock_output, "cm-test-unknown-field"),
        ):
            await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        db_session.refresh(comment)
        assert refreshed.status == "action_failed"
        assert comment.content == "hello world"

    @pytest.mark.asyncio
    async def test_execute_moderation_missing_trace_does_not_crash(
        self,
        db_session: Session,
        admin_user,
    ):
        comment = Comment(
            target_type="blog_post",
            target_id=1,
            user_id=admin_user.id,
            content="trace test",
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)

        record = ContentModerationService(db_session).enqueue(
            target_type="comment",
            target_id=comment.id,
            target_version=comment.updated_at.isoformat(),
            trigger_action="create",
            snapshot={"content": comment.content},
            created_by_user_id=admin_user.id,
        )

        with patch.object(
            ContentModerationAgent,
            "moderate",
            return_value=(None, "cm-missing-trace"),
        ):
            await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        assert refreshed.status == "review_failed"
        assert refreshed.trace_id is None

    @pytest.mark.asyncio
    async def test_execute_moderation_review_failed_copies_trace_error(
        self,
        db_session: Session,
        admin_user,
    ):
        comment = Comment(
            target_type="blog_post",
            target_id=1,
            user_id=admin_user.id,
            content="json fail",
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)

        record = ContentModerationService(db_session).enqueue(
            target_type="comment",
            target_id=comment.id,
            target_version=comment.updated_at.isoformat(),
            trigger_action="create",
            snapshot={"content": comment.content},
            created_by_user_id=admin_user.id,
        )
        from app.crud import agent_trace as trace_crud
        trace_crud.create_agent_trace(
            db_session,
            trace_id="cm-test-review-failed",
            status="failed",
            error_type="JSONDecodeError",
            error_message="bad json",
            output_message="invalid json {{{",
        )

        with patch.object(
            ContentModerationAgent,
            "moderate",
            return_value=(None, "cm-test-review-failed"),
        ):
            await ContentModerationService.execute_moderation(db_session, record.id)

        refreshed = cm_crud.get_moderation_record_by_id(db_session, record.id)
        assert refreshed.status == "review_failed"
        assert refreshed.error_type == "JSONDecodeError"
        assert refreshed.error_message == "bad json"
        assert refreshed.moderation_result == {"raw_output": "invalid json {{{"}

    def test_retry_only_allowed_statuses(self, db_session: Session, moderation_service, admin_user):
        record = moderation_service.enqueue(
            target_type="comment",
            target_id=1,
            target_version="v1",
            trigger_action="create",
            snapshot={"content": "test"},
            created_by_user_id=admin_user.id,
        )
        original_task_id = record.task_id

        # pending 状态不允许重试
        with pytest.raises(ValueError, match="不允许重试"):
            moderation_service.retry(record.id)

        # 手动改为失败状态
        from app.crud import content_moderation as cm_crud
        cm_crud.update_moderation_record(db_session, record.id, status="review_failed")

        retried = moderation_service.retry(record.id)
        assert retried.id == record.id
        assert retried.status == "pending"
        assert retried.trigger_action == "retry"
        assert retried.task_id != original_task_id


# ------------------------------------------------------------------
# Sanitizer 测试
# ------------------------------------------------------------------

class TestContentSanitizer:
    def test_sanitize_exact_match(self):
        snapshot = {"content": "Hello bad world"}
        spans = [FlaggedSpan(field="content", text="bad", start=6, end=9, category="辱骂", confidence=0.9)]
        sanitized, results, failed = sanitize_content(snapshot, spans)
        assert sanitized["content"] == "Hello *** world"
        assert len(failed) == 0
        assert results[0]["replaced_count"] == 1

    def test_sanitize_fuzzy_match(self):
        snapshot = {"content": "Hello bad world"}
        spans = [FlaggedSpan(field="content", text="bad", start=999, end=999, category="辱骂", confidence=0.9)]
        sanitized, results, failed = sanitize_content(snapshot, spans)
        assert sanitized["content"] == "Hello *** world"
        assert len(failed) == 0
        assert results[0]["replaced_count"] == 1

    def test_sanitize_fallback_full_mask(self):
        snapshot = {"content": "Hello world"}
        spans = [FlaggedSpan(field="content", text="nonexistent", start=0, end=11, category="辱骂", confidence=0.9)]
        sanitized, results, failed = sanitize_content(snapshot, spans)
        # 全部匹配失败，降级为整字段替换
        assert sanitized["content"] == "***********"
        assert len(failed) == 1
        assert results[0]["replaced_count"] == 1

    def test_sanitize_no_spans(self):
        snapshot = {"content": "Hello world"}
        sanitized, results, failed = sanitize_content(snapshot, [])
        assert sanitized["content"] == "Hello world"
        assert len(results) == 0
        assert len(failed) == 0

    def test_sanitize_multiple_fields(self):
        snapshot = {"title": "Bad title", "content": "Bad content"}
        spans = [
            FlaggedSpan(field="title", text="Bad", start=0, end=3, category="辱骂", confidence=0.9),
            FlaggedSpan(field="content", text="Bad", start=0, end=3, category="辱骂", confidence=0.9),
        ]
        sanitized, results, failed = sanitize_content(snapshot, spans)
        assert sanitized["title"] == "*** title"
        assert sanitized["content"] == "*** content"
        assert len(failed) == 0
