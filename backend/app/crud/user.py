from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    根据用户ID获取用户
    Args:
        db: 数据库会话
        user_id: 用户ID
    Returns:
        User | None: 用户对象或None
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """
    根据用户名获取用户
    Args:
        db: 数据库会话
        username: 用户名
    Returns:
        User | None: 用户对象或None
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    根据邮箱获取用户
    Args:
        db: 数据库会话
        email: 邮箱
    Returns:
        User | None: 用户对象或None
    """
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """
    获取用户列表
    Args:
        db: 数据库会话
        skip: 跳过数量
        limit: 限制数量
    Returns:
        list[User]: 用户列表
    """
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    创建用户
    Args:
        db: 数据库会话
        user_in: 用户创建请求
    Returns:
        User: 用户对象
    """
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        permission=getattr(user_in, "permission", 0))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    """
    更新用户
    Args:
        db: 数据库会话
        db_user: 用户对象
        user_in: 用户更新请求
    Returns:
        User: 用户对象
    """
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


def delete_user(db: Session, user_id: int) -> int:
    """
    删除用户
    Args:
        db: 数据库会话
        user_id: 用户ID
    Returns:
        int: 删除数量
    """
    deleted = db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    db.commit()
    return deleted