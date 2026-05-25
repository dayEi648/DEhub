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
