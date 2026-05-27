from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.models.conversation_message import ConversationMessage


def create_conversation_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> ConversationMessage:
    """创建单条对话消息。"""
    msg = ConversationMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        meta=metadata,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_conversation_messages(
    db: Session, conversation_id: int, skip: int = 0, limit: int | None = 100
) -> list[ConversationMessage]:
    """按时间正序查询某对话的消息列表。"""
    query = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .offset(skip)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def _visible_message_filter():
    """构建可见消息的 SQL 过滤条件。

    可见消息定义（与 ChatService._is_visible_message 对齐）：
    - user 角色始终可见
    - assistant 角色：compact_summary 标记的始终可见；
      其他 assistant 需有非空内容且不包含 tool_calls
    - system / tool 角色不可见
    """
    return or_(
        ConversationMessage.role == "user",
        and_(
            ConversationMessage.role == "assistant",
            ConversationMessage.meta.contains({"compact_summary": True}),
        ),
        and_(
            ConversationMessage.role == "assistant",
            ConversationMessage.content != "",
            or_(
                ConversationMessage.meta.is_(None),
                ~ConversationMessage.meta.has_key("tool_calls"),
            ),
        ),
    )


def list_visible_conversation_messages(
    db: Session, conversation_id: int, skip: int = 0, limit: int | None = 100
) -> list[ConversationMessage]:
    """按时间正序查询某对话的可见消息列表（先过滤后分页）。"""
    query = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .filter(_visible_message_filter())
        .order_by(ConversationMessage.created_at.asc())
        .offset(skip)
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def count_visible_conversation_messages(db: Session, conversation_id: int) -> int:
    """统计某对话的可见消息总条数。"""
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .filter(_visible_message_filter())
        .count()
    )


def count_conversation_messages(db: Session, conversation_id: int) -> int:
    """统计某对话的消息总条数。"""
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .count()
    )


def count_conversation_messages_by_role(
    db: Session, conversation_id: int, role: str
) -> int:
    """按角色统计某对话的消息数量。"""
    return (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.role == role,
        )
        .count()
    )


def delete_conversation_message(db: Session, message_id: int) -> bool:
    """删除单条对话消息。

    Args:
        db: 数据库会话
        message_id: 消息 ID

    Returns:
        是否成功删除
    """
    result = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.id == message_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result > 0
