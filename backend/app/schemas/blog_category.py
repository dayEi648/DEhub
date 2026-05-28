from pydantic import BaseModel, ConfigDict, Field


class BlogCategoryBase(BaseModel):
    """分类基础字段"""
    name: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=255)
    description: str | None = None


class BlogCategoryCreate(BlogCategoryBase):
    """创建分类请求"""
    slug: str | None = Field(default=None, max_length=255)


class BlogCategoryUpdate(BaseModel):
    """更新分类请求：全可选"""
    name: str | None = Field(default=None, min_length=1, max_length=64)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class BlogCategoryResponse(BlogCategoryBase):
    """分类响应"""
    id: int

    model_config = ConfigDict(from_attributes=True)


class BlogCategoryBrief(BaseModel):
    """分类精简信息（用于嵌套展示）"""
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class BlogCategoryWithPostCount(BlogCategoryResponse):
    """分类响应（附带文章数量）"""
    post_count: int = 0
