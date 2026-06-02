from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile


def get_user_profile(db: Session, user_id: int) -> UserProfile | None:
    """获取指定用户的画像记录。"""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def upsert_user_profile(
    db: Session, user_id: int, profile_text: str
) -> UserProfile:
    """创建或更新用户画像记录（使用原子级 UPSERT，避免并发竞态）。"""
    stmt = (
        insert(UserProfile)
        .values(user_id=user_id, profile_text=profile_text)
        .on_conflict_do_update(
            index_elements=["user_id"],
            set_={"profile_text": profile_text},
        )
    )
    db.execute(stmt)
    db.commit()
    record = get_user_profile(db, user_id)
    if record is None:
        raise RuntimeError(f"upsert_user_profile 失败后无法读取记录: user_id={user_id}")
    return record
