from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

# 创建请求，必须传密码
class UserCreate(UserBase):
    password: str

# 更新请求：全可选
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

# 响应对象：不返回密码
class UserResponse(UserBase):
    id: int
    created_at: datetime

    # Pydantic v2 写法：允许从 ORM 对象读取属性
    model_config = ConfigDict(from_attributes=True)
