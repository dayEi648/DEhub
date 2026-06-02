from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    username: str | None = None,
    email: str | None = None,
    permission: int | None = None,
) -> tuple[list[User], int]:
    query = db.query(User)
    if not include_deleted:
        query = query.filter(User.is_deleted == False)
    if username:
        escaped_username = username.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(User.username.ilike(f"%{escaped_username}%", escape="\\"))
    if email:
        escaped_email = email.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(User.email.ilike(f"%{escaped_email}%", escape="\\"))
    if permission is not None:
        query = query.filter(User.permission == permission)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_user(db: Session, user_in: UserCreate) -> User:
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        permission=user_in.permission if user_in.permission is not None else 0,
        personal_profile=user_in.personal_profile)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    # 只更新传了的字段
    update_data = user_in.model_dump(exclude_unset=True)
    # 如果更新密码，需要哈希后存入 hashed_password 字段
    if "password" in update_data:
        password_value = update_data.pop("password")
        if password_value is not None:
            update_data["hashed_password"] = get_password_hash(password_value)
        
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def soft_delete_user(db: Session, user_id: int) -> int:
    result = db.query(User).filter(
        User.id == user_id,
        User.is_deleted == False
    ).update({"is_deleted": True}, synchronize_session=False)
    db.commit()
    return result


def hard_delete_user(db: Session, user_id: int, auto_commit: bool = True) -> int:
    deleted = db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    if auto_commit:
        db.commit()
    return deleted
