from pydantic import BaseModel, EmailStr, ConfigDict
from pydantic.networks import validate_email
from datetime import datetime
from typing import Optional
from pydantic import Field, field_validator

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr

# 创建请求，必须传密码
class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    permission: Optional[int] = Field(default=0, ge=0, le=2)
    avatar_url: Optional[str] = Field(default=None, max_length=128)
    personal_profile: Optional[str] = Field(default=None)

# 更新请求：全可选
class UserUpdate(BaseModel):
    username: Optional[str] = Field(min_length=3, max_length=64, default=None)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(min_length=6, max_length=128, default=None)
    permission: Optional[int] = Field(default=None, ge=0, le=2)
    avatar_url: Optional[str] = Field(default=None, max_length=128)
    personal_profile: Optional[str] = Field(default=None)

# 响应对象：不返回密码
class UserResponse(UserBase):
    id: int
    created_at: datetime
    permission: int
    is_deleted: bool
    avatar_url: Optional[str] = None
    personal_profile: Optional[str] = None

    # Pydantic v2 写法：允许从 ORM 对象读取属性
    model_config = ConfigDict(from_attributes=True)

# 登录请求
class UserLogin(BaseModel):
    account: str = Field(min_length=3, max_length=255, description="邮箱或用户名",)
    password: str = Field(min_length=6, max_length=128, description="密码")
    is_remember: bool = Field(default=False, description="是否记住登录")

    @field_validator('account')
    def validate_account(cls, v: str) -> str:
        """
        验证账号格式
        Args:
            v: 账号
        Returns:
            str: 账号
        Raises:
            ValueError: 邮箱格式不正确 或 用户名长度必须在3到64之间
        """
        v = v.strip()
        if '@' in v:
            try:
                validate_email(v)
            except Exception:
                raise ValueError("邮箱格式不正确")
            if len(v) > 255:
                raise ValueError("邮箱长度必须在3到255之间")
        else:
            if len(v) < 3 or len(v) > 64:
                raise ValueError("用户名长度必须在3到64之间")
        return v

# 登录响应
class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    user: UserResponse
    access_token_expires_in: int
    refresh_token_expires_in: Optional[int] = None

# 刷新令牌请求
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1, description="刷新令牌")

# 登出请求
class UserLogout(BaseModel):
    refresh_token: Optional[str] = None

# 注册请求
class UserRegister(UserCreate):
    pass