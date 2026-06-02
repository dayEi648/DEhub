"""内容审核统一入口服务。

负责：
- 创建审核记录并调度后台任务
- 执行审核（调用 Agent → 更新记录 → 执行处置）
- 重试失败的审核
- 所有写操作均在独立 Session 中执行，用于后台任务隔离
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import agent_trace as trace_crud
from app.crud import content_moderation as cm_crud
from app.db.session import SessionLocal
from app.infrastructure.background_tasks import background_task_manager
from app.infrastructure.cache_invalidator import BlogCacheInvalidator, ForumCacheInvalidator
from app.models.blog_post import BlogPost
from app.models.comment import Comment
from app.models.content_moderation_record import ContentModerationRecord
from app.models.forum_post import ForumPost
from app.models.forum_reply import ForumReply
from app.models.forum_zone import ForumZone
from app.models.user import User
from app.schemas.content_moderation import FlaggedSpan
from app.services.blog_post_embedding_service import BlogPostEmbeddingService
from app.services.content_moderation_agent import ContentModerationAgent
from app.services.content_moderation_sanitizer import sanitize_content

logger = logging.getLogger(__name__)

# 可审核的目标类型映射（用于校验）
VALID_TARGET_TYPES = {
    "user",
    "blog_post",
    "forum_zone",
    "forum_post",
    "forum_reply",
    "comment",
}

# 各目标类型对应的审核字段
TARGET_FIELDS: dict[str, list[str]] = {
    "user": ["username", "personal_profile"],
    "blog_post": ["title", "summary", "content_md", "tags"],
    "forum_zone": ["zone_name", "description"],
    "forum_post": ["title", "content"],
    "forum_reply": ["content"],
    "comment": ["content"],
}


class ContentModerationService:
    """内容审核服务。"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def enqueue(
        self,
        target_type: str,
        target_id: int,
        target_version: str,
        trigger_action: str,
        snapshot: dict[str, str],
        created_by_user_id: int | None = None,
    ) -> ContentModerationRecord | None:
        """将内容加入审核队列。

        在当前 Session 中创建 pending 记录，并调度后台审核任务。
        """
        if not settings.CONTENT_MODERATION_ENABLED:
            logger.info(
                "内容审核已禁用，跳过入队: target=%s:%d version=%s",
                target_type, target_id, target_version,
            )
            return None

        if target_type not in VALID_TARGET_TYPES:
            raise ValueError(f"不支持的内容类型: {target_type}")

        # 幂等保护：同一版本已存在则跳过
        existing = _get_existing_record(
            self.db,
            target_type=target_type,
            target_id=target_id,
            target_version=target_version,
        )
        if existing:
            logger.debug(
                "审核任务已存在，跳过: target=%s:%d version=%s",
                target_type, target_id, target_version,
            )
            return existing

        task_id = str(uuid.uuid4())
        try:
            record = cm_crud.create_moderation_record(
                self.db,
                task_id=task_id,
                target_type=target_type,
                target_id=target_id,
                target_version=target_version,
                trigger_action=trigger_action,
                original_snapshot=snapshot,
                created_by_user_id=created_by_user_id,
            )
        except IntegrityError:
            self.db.rollback()
            existing = _get_existing_record(
                self.db,
                target_type=target_type,
                target_id=target_id,
                target_version=target_version,
            )
            if existing:
                logger.debug(
                    "审核任务并发创建后已存在，复用已有记录: target=%s:%d version=%s",
                    target_type, target_id, target_version,
                )
                return existing
            raise

        # 调度后台审核任务
        try:
            background_task_manager.create_task(
                _run_moderation_task(record.id),
                name=f"content_moderation.{task_id}",
            )
        except RuntimeError:
            # 无运行中的事件循环（如单元测试同步调用），不调度后台任务
            logger.debug("无运行中的事件循环，跳过后台任务调度: task_id=%s", task_id)

        logger.info(
            "审核任务已入队: id=%d task_id=%s target=%s:%d",
            record.id, task_id, target_type, target_id,
        )
        return record

    def retry(self, record_id: int) -> ContentModerationRecord:
        """重试一条失败的审核记录。

        仅允许对 review_failed / action_failed / stale 状态进行重试。
        重置原记录为 pending 并重新调度后台任务。
        """
        if not settings.CONTENT_MODERATION_ENABLED:
            raise ValueError("内容审核已禁用")

        old = cm_crud.get_moderation_record_by_id(self.db, record_id)
        if not old:
            raise ValueError(f"审核记录不存在: {record_id}")
        if old.status not in ("review_failed", "action_failed", "stale"):
            raise ValueError(f"记录状态不允许重试: {old.status}")

        # 生成新 task_id，重置状态
        new_task_id = str(uuid.uuid4())
        record = cm_crud.update_moderation_record(
            self.db,
            record_id,
            task_id=new_task_id,
            status="pending",
            trigger_action="retry",
            trace_id=None,
            risk_level="none",
            categories=None,
            moderation_result=None,
            action_plan=None,
            action_result=None,
            model_name=None,
            error_type=None,
            error_message=None,
            started_at=None,
            finished_at=None,
        )
        if not record:
            raise ValueError(f"审核记录更新失败: {record_id}")

        # 重新调度后台任务
        try:
            background_task_manager.create_task(
                _run_moderation_task(record.id),
                name=f"content_moderation.{new_task_id}",
            )
        except RuntimeError:
            logger.debug("无运行中的事件循环，跳过后台任务调度: task_id=%s", new_task_id)

        return record

    # ------------------------------------------------------------------
    # 静态/类方法：供后台任务调用
    # ------------------------------------------------------------------

    @staticmethod
    async def execute_moderation(db: Session, record_id: int) -> None:
        """执行单条审核记录的后台审核流程。

        该方法应在独立 Session 中调用（如后台任务）。
        """
        record = cm_crud.get_moderation_record_by_id(db, record_id)
        if not record:
            logger.warning("审核记录不存在: %d", record_id)
            return
        if record.status != "pending":
            logger.debug("审核记录状态非 pending，跳过: %d", record_id)
            return

        # 1. 标记为 running
        cm_crud.update_moderation_record(
            db, record.id, status="running", started_at=datetime.now(timezone.utc)
        )

        # 2. 检查版本是否已过期（staleness）
        current_version = await _resolve_current_version(
            db, record.target_type, record.target_id
        )
        if current_version and current_version != record.target_version:
            _mark_record_stale(
                db,
                record=record,
                current_version=current_version,
                trace_id=None,
            )
            return

        # 3. 调用审核 Agent
        agent = ContentModerationAgent()
        agent_output, trace_id = await agent.moderate(
            content_snapshot=record.original_snapshot,
            target_type=record.target_type,
            user_id=record.created_by_user_id,
        )
        resolved_trace_id, trace_error_type, trace_error_message, raw_output = (
            _resolve_trace_context(db, trace_id)
        )

        if agent_output is None:
            # Agent 调用或解析失败
            cm_crud.update_moderation_record(
                db,
                record.id,
                status="review_failed",
                trace_id=resolved_trace_id,
                model_name=agent.model_name,
                moderation_result={"raw_output": raw_output} if raw_output else None,
                error_type=trace_error_type,
                error_message=trace_error_message,
                finished_at=datetime.now(timezone.utc),
            )
            return

        # 3.5 再次检查版本，避免审核期间内容被新版本覆盖
        latest_version = await _resolve_current_version(
            db, record.target_type, record.target_id
        )
        if latest_version and latest_version != record.target_version:
            _mark_record_stale(
                db,
                record=record,
                current_version=latest_version,
                trace_id=resolved_trace_id,
            )
            return

        # 4. 保存审核结果
        moderation_result = agent_output.model_dump()
        cm_crud.update_moderation_record(
            db,
            record.id,
            trace_id=resolved_trace_id,
            model_name=agent.model_name,
            risk_level=agent_output.risk_level,
            categories=agent_output.categories,
            moderation_result=moderation_result,
        )

        # 5.  verdict = pass，直接完成
        if agent_output.verdict == "pass":
            cm_crud.update_moderation_record(
                db,
                record.id,
                status="passed",
                finished_at=datetime.now(timezone.utc),
            )
            return

        # 6. verdict = block，构建并执行处置计划
        action_plan = _build_action_plan(record, agent_output)
        cm_crud.update_moderation_record(
            db, record.id, action_plan=action_plan
        )

        action_result = await _apply_action(
            db, record, agent_output, record.original_snapshot
        )
        cm_crud.update_moderation_record(
            db, record.id, action_result=action_result
        )

        # 检查处置是否全部成功
        if action_result.get("failed"):
            cm_crud.update_moderation_record(
                db,
                record.id,
                status="action_failed",
                finished_at=datetime.now(timezone.utc),
                error_type="ActionFailed",
                error_message=action_result.get("error_message"),
            )
        else:
            cm_crud.update_moderation_record(
                db,
                record.id,
                status="blocked",
                finished_at=datetime.now(timezone.utc),
            )


# ------------------------------------------------------------------
# 内部辅助函数
# ------------------------------------------------------------------

async def _run_moderation_task(record_id: int) -> None:
    """后台任务入口：在独立 Session 中执行审核。"""
    try:
        with SessionLocal() as db:
            await ContentModerationService.execute_moderation(db, record_id)
    except Exception:
        logger.exception("后台审核任务异常: record_id=%d", record_id)


def _get_existing_record(
    db: Session,
    *,
    target_type: str,
    target_id: int,
    target_version: str,
) -> ContentModerationRecord | None:
    return (
        db.query(ContentModerationRecord)
        .filter(
            ContentModerationRecord.target_type == target_type,
            ContentModerationRecord.target_id == target_id,
            ContentModerationRecord.target_version == target_version,
        )
        .first()
    )


def _resolve_trace_context(
    db: Session,
    trace_id: str | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """解析已持久化的 trace，上游持久化失败时避免外键错误。"""
    if not trace_id:
        return None, None, None, None

    trace = trace_crud.get_agent_trace_by_trace_id(db, trace_id)
    if not trace:
        logger.warning("审核 trace 未落库，跳过关联: trace_id=%s", trace_id)
        return None, None, None, None

    return trace_id, trace.error_type, trace.error_message, trace.output_message


def _mark_record_stale(
    db: Session,
    *,
    record: ContentModerationRecord,
    current_version: str,
    trace_id: str | None,
) -> None:
    cm_crud.update_moderation_record(
        db,
        record.id,
        status="stale",
        trace_id=trace_id,
        finished_at=datetime.now(timezone.utc),
        error_type="StalenessError",
        error_message="目标内容已被更新，当前审核版本已过期",
    )

    snapshot = _build_snapshot(db, record.target_type, record.target_id)
    if snapshot:
        ContentModerationService(db).enqueue(
            target_type=record.target_type,
            target_id=record.target_id,
            target_version=current_version,
            trigger_action=record.trigger_action,
            snapshot=snapshot,
            created_by_user_id=record.created_by_user_id,
        )


async def _resolve_current_version(
    db: Session, target_type: str, target_id: int
) -> str | None:
    """获取目标对象的当前版本（updated_at ISO 格式）。"""
    model_map = {
        "user": User,
        "blog_post": BlogPost,
        "forum_zone": ForumZone,
        "forum_post": ForumPost,
        "forum_reply": ForumReply,
        "comment": Comment,
    }
    model = model_map.get(target_type)
    if not model:
        return None
    obj = db.query(model).filter(model.id == target_id).first()
    if not obj:
        return None
    updated_at = getattr(obj, "updated_at", None)
    if updated_at:
        return updated_at.isoformat()
    return None


def _build_snapshot(db: Session, target_type: str, target_id: int) -> dict[str, str] | None:
    """从数据库构建当前内容的审核字段快照。"""
    model_map = {
        "user": User,
        "blog_post": BlogPost,
        "forum_zone": ForumZone,
        "forum_post": ForumPost,
        "forum_reply": ForumReply,
        "comment": Comment,
    }
    model = model_map.get(target_type)
    if not model:
        return None
    obj = db.query(model).filter(model.id == target_id).first()
    if not obj:
        return None

    fields = TARGET_FIELDS.get(target_type, [])
    snapshot: dict[str, str] = {}
    for field in fields:
        value = getattr(obj, field, None)
        if value is not None:
            if isinstance(value, list):
                snapshot[field] = ", ".join(str(v) for v in value)
            else:
                snapshot[field] = str(value)
    return snapshot


def _build_action_plan(
    record: ContentModerationRecord, agent_output
) -> dict:
    """根据 Agent 输出构建处置计划。"""
    plan: dict = {
        "target_type": record.target_type,
        "target_id": record.target_id,
        "verdict": agent_output.verdict,
        "suggested_action": agent_output.suggested_action,
        "flagged_fields": list({span.field for span in agent_output.flagged_spans}),
    }
    if record.target_type == "blog_post":
        plan["actions"] = ["unpublish"]
    else:
        plan["actions"] = ["mask_text"]
    return plan


async def _apply_action(
    db: Session,
    record: ContentModerationRecord,
    agent_output,
    original_snapshot: dict[str, str],
) -> dict:
    """执行处置操作。

    Returns:
        action_result dict，包含处置前后对比和失败信息。
    """
    result: dict = {
        "target_type": record.target_type,
        "target_id": record.target_id,
        "old_values": {},
        "new_values": {},
        "failed": False,
        "error_message": None,
    }

    try:
        if record.target_type == "blog_post":
            await _unpublish_blog_post(db, record.target_id, result)
        else:
            await _mask_text_fields(
                db, record.target_type, record.target_id,
                agent_output.flagged_spans, original_snapshot, result
            )
    except Exception as exc:
        result["failed"] = True
        result["error_message"] = str(exc)[:1000]
        logger.exception("处置失败: record_id=%d", record.id)

    return result


async def _unpublish_blog_post(
    db: Session, post_id: int, result: dict
) -> None:
    """将博客文章回草稿并清理向量/缓存。"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise ValueError(f"博客文章不存在: {post_id}")

    old_status = post.status
    if old_status != "published":
        # 已经不是发布状态，无需处理
        result["old_values"]["status"] = old_status
        result["new_values"]["status"] = old_status
        return

    post.status = "draft"
    db.commit()

    # 删除向量索引
    embed_service = BlogPostEmbeddingService(db)
    await asyncio.to_thread(embed_service.delete_post_embedding, post_id)

    # 失效缓存
    BlogCacheInvalidator.invalidate_all()

    result["old_values"]["status"] = old_status
    result["new_values"]["status"] = "draft"
    result["embedding_deleted"] = True
    result["cache_invalidated"] = True


async def _mask_text_fields(
    db: Session,
    target_type: str,
    target_id: int,
    flagged_spans: list[FlaggedSpan],
    original_snapshot: dict[str, str],
    result: dict,
) -> None:
    """对非博客内容执行敏感片段替换。"""
    model_map = {
        "user": User,
        "forum_zone": ForumZone,
        "forum_post": ForumPost,
        "forum_reply": ForumReply,
        "comment": Comment,
    }
    model = model_map.get(target_type)
    if not model:
        raise ValueError(f"不支持的内容类型: {target_type}")

    obj = db.query(model).filter(model.id == target_id).first()
    if not obj:
        raise ValueError(f"目标对象不存在: {target_type}:{target_id}")

    # 使用 Sanitizer 执行替换
    sanitized, replace_results, failed_spans = sanitize_content(
        original_snapshot, flagged_spans
    )

    # 写入数据库
    for field, new_value in sanitized.items():
        old_value = getattr(obj, field, None)
        if old_value is not None and str(old_value) != new_value:
            setattr(obj, field, new_value)
            result["old_values"][field] = str(old_value)
            result["new_values"][field] = new_value

    db.commit()

    # 失效相关缓存
    if target_type == "user":
        # 用户资料变更可能影响依赖用户展示的博客/论坛缓存
        BlogCacheInvalidator.invalidate_all()
        ForumCacheInvalidator.invalidate_forum_zones()
    elif target_type == "forum_zone":
        ForumCacheInvalidator.invalidate_forum_zones()
    elif target_type == "forum_post":
        zone_id = getattr(obj, "zone_id", None)
        ForumCacheInvalidator.invalidate_forum_posts(zone_id=zone_id)
    elif target_type == "forum_reply":
        post_id = getattr(obj, "post_id", None)
        if post_id:
            post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
            zone_id = getattr(post, "zone_id", None) if post else None
            ForumCacheInvalidator.invalidate_forum_posts(zone_id=zone_id)
    elif target_type == "comment":
        BlogCacheInvalidator.invalidate_blog_posts()

    result["replaced_spans"] = [
        {"field": r["field"], "replaced_count": r["replaced_count"]}
        for r in replace_results
    ]
    if failed_spans:
        result["failed_spans"] = failed_spans
        # 如果有失败但成功替换数 > 0，不算完全失败
        total_replaced = sum(r["replaced_count"] for r in replace_results)
        if total_replaced == 0:
            result["failed"] = True
            result["error_message"] = "所有敏感片段均无法定位"
