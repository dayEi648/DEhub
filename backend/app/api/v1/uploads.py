from fastapi import APIRouter, Depends, File, UploadFile

from app.core.security import get_current_user
from app.models.user import User
from app.storage.oss import upload_generic_image

router = APIRouter(prefix="/uploads", tags=["通用上传"])


@router.post("/image")
async def upload_image(
    file: UploadFile = File(..., description="图片文件，最大 5MB，支持自动压缩"),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    上传通用图片（登录用户可用）
    返回可直接引用的 OSS URL
    """
    url = await upload_generic_image(file)
    return {"url": url}
