from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from pydantic import Field

class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr

# 创建请求，必须传密码
class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)

# 更新请求：全可选
class UserUpdate(BaseModel):
    username: Optional[str] = Field(min_length=3, max_length=64, default=None)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(min_length=6, max_length=128, default=None)

# 响应对象：不返回密码
class UserResponse(UserBase):
    id: int
    created_at: datetime

    # Pydantic v2 写法：允许从 ORM 对象读取属性
    model_config = ConfigDict(from_attributes=True)
