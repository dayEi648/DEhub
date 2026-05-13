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


def soft_delete_ai_conversation(db: Session, conversation_id: int) -> int:
    """软删除对话，返回更新行数。"""
    result = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id)
        .update({"is_deleted": True}, synchronize_session=False)
    )
    db.commit()
    return result


def list_ai_conversations_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> tuple[list[AIConversation], int]:
    """查询某用户的未删除对话列表，返回 (items, total)。"""
    query = db.query(AIConversation).filter(
        AIConversation.user_id == user_id,
        AIConversation.is_deleted == False,
    )
    total = query.count()
    items = query.order_by(AIConversation.created_at.desc()).offset(skip).limit(limit).all()
    return items, total
