from pydantic import BaseModel
from datetime import datetime

class BlogPostSearchResult(BaseModel):
    """向量检索结果 Schema"""

    post_id: int
    title: str
    slug: str
    summary: str | None
    category_name: str
    similarity_score: float

    model_config = {"from_attributes": True}