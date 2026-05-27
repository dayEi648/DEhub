from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.ai_conversation import AIConversation


def get_ai_conversation_by_id(db: Session, conversation_id: int) -> AIConversation | None:
    return db.query(AIConversation).filter(AIConversation.id == conversation_id).first()


def create_ai_conversation(db: Session, user_id: int, title: str) -> AIConversation:
    conv = AIConversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def delete_ai_conversation(
    db: Session, conversation_id: int, auto_commit: bool = True
) -> int:
    conv = db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
    if conv is None:
        return 0
    db.delete(conv)
    if auto_commit:
        db.commit()
    return 1


def update_conversation_title(
    db: Session, conversation_id: int, title: str
) -> int:
    result = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id)
        .update(
            {"title": title, "updated_at": func.now()},
            synchronize_session=False,
        )
    )
    db.commit()
    return result


def update_last_message_at(
    db: Session, conversation_id: int
) -> int:
    result = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id)
        .update(
            {"last_message_at": func.now(), "updated_at": func.now()},
            synchronize_session=False,
        )
    )
    db.commit()
    return result


def list_ai_conversations_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 20
) -> tuple[list[AIConversation], int]:
    query = db.query(AIConversation).filter(
        AIConversation.user_id == user_id,
    )
    total = query.count()
    items = query.order_by(AIConversation.created_at.desc()).offset(skip).limit(limit).all()
    return items, total
