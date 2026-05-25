from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.form_parser import parse_json_form_payload
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLoginResponse, UserLogin, UserLogout, RefreshTokenRequest, UserRegister, UserListResponse, ChangePasswordRequest
from app.services.user_service import UserService
from app.models.user import User
from app.core.security import get_current_user, get_token_from_header

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    创建用户（管理员专属）
    Args:
        user_in: 用户创建请求
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        UserResponse: 用户响应
    """
    service = UserService(db)
    return service.create_user(user_in, current_user)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    获取用户
    若用户已注销，仅管理员及以上可查看
    """
    service = UserService(db)
    return service.get_user(user_id, current_user)

@router.get("/", response_model=UserListResponse)
def list_users(
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
    include_deleted: bool = Query(default=False, description="是否包含已注销用户"),
    username: str | None = Query(default=None, description="用户名模糊筛选"),
    email: str | None = Query(default=None, description="邮箱模糊筛选"),
    permission: int | None = Query(default=None, ge=0, le=2, description="权限值筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserListResponse:
    """
    获取用户列表（支持分页与筛选）
    """
    service = UserService(db)
    return service.list_users(
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        username=username,
        email=email,
        permission=permission,
        current_user=current_user,
    )

def parse_user_update(user_in: str = Form(..., description="用户更新请求的 JSON 字符串")) -> UserUpdate:
    """解析前端传来的 user_in JSON 字符串为 UserUpdate 模型"""
    return parse_json_form_payload(user_in, UserUpdate)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate = Depends(parse_user_update),
    file: UploadFile | None = File(None, description="头像文件，前端限制 20MB，后端自动压缩至 5MB 以下"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    更新用户
    Args:
        user_id: 用户ID
        user_in: 用户更新请求
        file: 头像文件
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        UserResponse: 用户响应
    """
    service = UserService(db)
    return await service.update_user(user_id, user_in, current_user, file)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_token_from_header),
) -> None:
    """
    注销用户（逻辑删除，管理员或本人）
    注销后该用户所有已签发的 token 将自动失效
    """
    service = UserService(db)
    service.soft_delete_user(user_id, current_user, access_token=token)
    return None


@router.delete("/{user_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    硬删除用户（从数据库彻底移除，管理员专属）
    """
    service = UserService(db)
    service.hard_delete_user(user_id, current_user)
    return None

@router.post("/login", response_model=UserLoginResponse)
def login(user_login: UserLogin, db: Session = Depends(get_db)) -> UserLoginResponse:
    """
    登录
    Args:
        user_login: 用户登录请求
        db: 数据库会话
    Returns:
        UserLoginResponse: 用户登录响应
    """
    service = UserService(db)
    return service.login_user(user_login)

@router.post("/refresh-token", response_model=UserLoginResponse)
async def refresh_access_token(req: RefreshTokenRequest, db: Session = Depends(get_db)) -> UserLoginResponse:
    """
    刷新访问令牌
    Args:
        req: 刷新令牌请求
        db: 数据库会话
    Returns:
        UserLoginResponse: 用户登录响应
    """
    if not req.refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌不能为空")
    service = UserService(db)
    return await service.refresh_access_token(req.refresh_token)

@router.post("/logout", status_code=204)
async def logout(
    user_logout: UserLogout,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_token_from_header),
) -> None:
    """
    登出
    Args:
        user_logout: 用户登出请求（可选 refresh_token）
        db: 数据库会话
        current_user: 当前登录用户
        token: 访问令牌（来自 Authorization Header）
    Returns:
        None
    """
    service = UserService(db)
    await service.logout_user(token, user_logout)

@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_token_from_header),
) -> None:
    """
    修改当前登录用户密码
    修改成功后，该用户所有已有 Token 将自动失效，需重新登录
    Args:
        password_data: 密码修改请求
        db: 数据库会话
        current_user: 当前登录用户
        token: 访问令牌（来自 Authorization Header）
    """
    service = UserService(db)
    service.change_password(current_user, password_data, access_token=token)


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_register: UserRegister, db: Session = Depends(get_db)) -> UserResponse:
    """
    注册用户
    Args:
        user_register: 用户注册请求
        db: 数据库会话
    Returns:
        UserResponse: 用户响应
    """
    service = UserService(db)
    return service.register_user(user_register)
