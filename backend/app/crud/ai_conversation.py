from sqlalchemy.orm import Session
from app.models.ai_conversation import AIConversation


def get_ai_conversation_by_id(db: Session, conversation_id: int) -> AIConversation | None:
    """根据 ID 获取对话（不校验删除状态，由调用方决定）。"""
    return db.query(AIConversation).filter(AIConversation.id == conversation_id).first()


def create_ai_conversation(db: Session, user_id: int, title: str) -> AIConversation:
    """创建新对话。"""
    conv = AIConversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def delete_ai_conversation(db: Session, conversation_id: int) -> int:
    """物理删除对话及其级联消息，返回删除行数。"""
    conv = db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
    if conv is None:
        return 0
    db.delete(conv)
    db.commit()
    return 1


def update_summary_message_count(
    db: Session, conversation_id: int, count: int
) -> int:
    """更新对话的 summary_message_count 字段。"""
    result = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id)
        .update({"summary_message_count": count}, synchronize_session=False)
    )
    db.commit()
    return result


def update_conversation_title(
    db: Session, conversation_id: int, title: str
) -> int:
    """更新对话标题。"""
    result = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id)
        .update({"title": title}, synchronize_session=False)
    )
    db.commit()
    return result


def update_last_message_at(
    db: Session, conversation_id: int
) -> int:
    """更新对话的 last_message_at 为当前时间。"""
    from sqlalchemy import func
    result = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id)
        .update({"last_message_at": func.now()}, synchronize_session=False)
    )
    db.commit()
    return result


def list_ai_conversations_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> tuple[list[AIConversation], int]:
    """查询某用户的未删除对话列表，返回 (items, total)。"""
    query = db.query(AIConversation).filter(
        AIConversation.user_id == user_id,
    )
    total = query.count()
    items = query.order_by(AIConversation.created_at.desc()).offset(skip).limit(limit).all()
    return items, total
