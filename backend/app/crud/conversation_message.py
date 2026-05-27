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
    """构建可见消息的 SQL 过滤条件（与 ChatService._is_visible_message 对齐）。"""
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
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .filter(_visible_message_filter())
        .count()
    )


def count_conversation_messages(db: Session, conversation_id: int) -> int:
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .count()
    )


def count_conversation_messages_by_role(
    db: Session, conversation_id: int, role: str
) -> int:
    return (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.role == role,
        )
        .count()
    )


def delete_conversation_message(db: Session, message_id: int) -> bool:
    result = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.id == message_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result > 0
