from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.security import get_current_user
from app.models.user import User
from app.storage.oss import upload_image, ImageUploadScene

router = APIRouter(prefix="/uploads", tags=["通用上传"])


@router.post("/image")
async def upload_image_endpoint(
    file: UploadFile = File(..., description="图片文件，前端限制 20MB，后端自动压缩至 5MB 以下"),
    scene: ImageUploadScene = Query(default=ImageUploadScene.generic, description="上传场景"),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    上传通用图片（登录用户可用）
    根据场景保存到不同 OSS 路径，返回可直接引用的 OSS URL
    """
    url = await upload_image(file, scene)
    return {"url": url}
