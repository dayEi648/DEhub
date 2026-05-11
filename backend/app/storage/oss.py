import oss2
import uuid
import mimetypes
from datetime import datetime
from fastapi import HTTPException, UploadFile
from app.core.config import settings

# 初始化OSS客户端
auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)

# 允许的文件类型
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']

def generate_file_path(file: UploadFile, folder: str) -> str:
    """
    生成文件路径
    Args:
        file: 上传文件
        folder: 文件夹
    Returns:
        str: 文件路径
    """
    ext = mimetypes.guess_extension(file.content_type) or ".bin"
    date_str = datetime.now().strftime("%Y%m%d")
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"{folder}/{date_str}/{unique_name}"

async def upload_file_to_oss(
    file: UploadFile, 
    folder: str, 
    allowed_types: set[str], 
    max_size: int) -> str:
    """
    上传文件到OSS
    Args:
        file: 上传文件
        folder: 文件夹
        allowed_types: 允许的文件类型
        max_size: 最大文件大小
    Returns:
        str: 文件路径
    """
    # 校验文件类型
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    # 读取并校验文件大小
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"文件大小超过限制，最大支持 {max_size // 1024 // 1024} MB")

    # 生成文件路径
    file_path = generate_file_path(file, folder)

    # 上传文件
    try:
        result = bucket.put_object(file_path, content, headers={'Content-Type': file.content_type})
        if not result.status == 200:
            raise HTTPException(status_code=500, detail="上传文件失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")

    # 构造访问URL
    if settings.OSS_DOMAIN:
        url = f"{settings.OSS_DOMAIN}/{file_path}"
    else:
        url = f"{settings.OSS_ENDPOINT}/{settings.OSS_BUCKET_NAME}/{file_path}"

    return url

# 删除文件
async def delete_file_from_oss(file_path: str) -> None:
    """
    删除文件从OSS
    Args:
        file_path: 文件路径
    Returns:
        None
    """
    try:
        result = bucket.delete_object(file_path)
        if not result.status == 204:
            raise HTTPException(status_code=500, detail="删除文件失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


# 便捷函数
async def upload_user_avatar(file: UploadFile) -> str:
    """
    上传用户头像
    Args:
        file: 上传文件
    Returns:
        str: 文件URL
    """
    return await upload_file_to_oss(
        file, settings.OSS_USERS_AVATAR_DIR, ALLOWED_IMAGE_TYPES, settings.MAX_USER_AVATAR_SIZE)

# 将OSS url 转为 file_path
def convert_oss_url_to_file_path(oss_url: str) -> str:
    """
    将OSS url转为 file_path
    Args:
        oss_url: OSS url
    Returns:
        str: file_path
    """
    return oss_url.replace(settings.OSS_DOMAIN, "") if settings.OSS_DOMAIN else oss_url