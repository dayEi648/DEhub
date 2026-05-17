from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile


def get_user_profile(db: Session, user_id: int) -> UserProfile | None:
    """获取指定用户的画像记录。"""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def upsert_user_profile(
    db: Session, user_id: int, profile_text: str
) -> UserProfile:
    """创建或更新用户画像记录。"""
    record = get_user_profile(db, user_id)
    if record is None:
        record = UserProfile(user_id=user_id, profile_text=profile_text)
        db.add(record)
    else:
        record.profile_text = profile_text
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(record)
    return record
