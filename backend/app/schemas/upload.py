from pydantic import BaseModel


class UploadImageResponse(BaseModel):
    """通用图片上传响应。"""

    url: str

