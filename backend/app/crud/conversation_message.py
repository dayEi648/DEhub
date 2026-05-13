from sqlalchemy.orm import Session
from app.models.conversation_message import ConversationMessage


def create_conversation_message(
    db: Session, conversation_id: int, role: str, content: str
) -> ConversationMessage:
    """创建单条对话消息。"""
    msg = ConversationMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_conversation_messages(
    db: Session, conversation_id: int, skip: int = 0, limit: int = 100
) -> list[ConversationMessage]:
    """按时间正序查询某对话的消息列表。"""
    return (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_recent_conversation_messages(
    db: Session, conversation_id: int, limit: int = 100
) -> list[ConversationMessage]:
    """查询某对话的最近 N 条消息，返回结果按时间正序排列（适合作为 LLM 上下文）。"""
    msgs = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(msgs))
