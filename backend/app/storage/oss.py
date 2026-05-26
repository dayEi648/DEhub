import io
import oss2
import uuid
import mimetypes
import asyncio
import filetype
import re
from enum import Enum
from urllib.parse import urlparse
from datetime import datetime
from fastapi import HTTPException, UploadFile
from app.core.config import settings

_bucket: oss2.Bucket | None = None

# 允许的文件类型
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
INITIAL_JPEG_QUALITY = 92
MIN_JPEG_QUALITY = 30
JPEG_QUALITY_STEP = 5
MIN_IMAGE_DIMENSION = 100
RESIZE_SCALE_FACTOR = 0.8
FINAL_RESIZE_QUALITY = 85


def _normalize_oss_endpoint(endpoint: str) -> str:
    """OSS SDK endpoint must include a URL scheme."""
    endpoint = endpoint.strip()
    if not endpoint:
        return endpoint
    parsed = urlparse(endpoint)
    if parsed.scheme:
        return endpoint
    return f"https://{endpoint}"


def _get_oss_bucket() -> oss2.Bucket:
    """Create the OSS client lazily so imports do not depend on external config."""
    global _bucket
    if _bucket is not None:
        return _bucket

    required_config = {
        "OSS_ACCESS_KEY_ID": settings.OSS_ACCESS_KEY_ID,
        "OSS_ACCESS_KEY_SECRET": settings.OSS_ACCESS_KEY_SECRET,
        "OSS_ENDPOINT": settings.OSS_ENDPOINT,
        "OSS_BUCKET_NAME": settings.OSS_BUCKET_NAME,
    }
    missing = [name for name, value in required_config.items() if not value]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"OSS配置缺失: {', '.join(missing)}",
        )

    auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
    _bucket = oss2.Bucket(
        auth,
        _normalize_oss_endpoint(settings.OSS_ENDPOINT),
        settings.OSS_BUCKET_NAME,
    )
    return _bucket


def _build_oss_file_url(file_path: str) -> str:
    if settings.OSS_DOMAIN:
        return f"{settings.OSS_DOMAIN.rstrip('/')}/{file_path}"

    endpoint = _normalize_oss_endpoint(settings.OSS_ENDPOINT).rstrip("/")
    return f"{endpoint}/{settings.OSS_BUCKET_NAME}/{file_path}"


class ImageUploadScene(str, Enum):
    """图片上传场景枚举，决定保存到 OSS 的路径和压缩策略"""

    avatar = "avatar"
    cover = "cover"
    generic = "generic"
    forum_post = "forum_post"
    forum_reply = "forum_reply"
    comment = "comment"
    chat = "chat"


# 场景配置：映射每个场景到 OSS 目录、压缩最大边长
SCENE_CONFIG: dict[ImageUploadScene, dict] = {
    ImageUploadScene.avatar: {
        "folder": settings.OSS_USERS_AVATAR_DIR,
        "compress_max_dimension": 1024,
        "description": "用户头像",
    },
    ImageUploadScene.cover: {
        "folder": settings.OSS_BLOG_COVER_DIR,
        "compress_max_dimension": 1920,
        "description": "博客封面",
    },
    ImageUploadScene.generic: {
        "folder": settings.OSS_UPLOADS_IMAGE_DIR,
        "compress_max_dimension": 1920,
        "description": "通用图片",
    },
    ImageUploadScene.forum_post: {
        "folder": settings.OSS_FORUM_POST_IMAGE_DIR,
        "compress_max_dimension": 1920,
        "description": "论坛帖子内嵌图片",
    },
    ImageUploadScene.forum_reply: {
        "folder": settings.OSS_FORUM_REPLY_IMAGE_DIR,
        "compress_max_dimension": 1920,
        "description": "论坛回复内嵌图片",
    },
    ImageUploadScene.comment: {
        "folder": settings.OSS_COMMENT_IMAGE_DIR,
        "compress_max_dimension": 1920,
        "description": "评论内嵌图片",
    },
    ImageUploadScene.chat: {
        "folder": settings.OSS_CHAT_IMAGE_DIR,
        "compress_max_dimension": 1920,
        "description": "AI对话内嵌图片",
    },
}


def generate_file_path(content_type: str, folder: str) -> str:
    """
    生成文件路径
    Args:
        content_type: 文件 MIME 类型
        folder: 文件夹
    Returns:
        str: 文件路径
    """
    ext = mimetypes.guess_extension(content_type) or ".bin"
    date_str = datetime.now().strftime("%Y%m%d")
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"{folder}/{date_str}/{unique_name}"


def compress_image(content: bytes, max_size: int | None = None, max_dimension: int = 1024) -> bytes:
    """
    压缩图片，确保输出大小不超过 max_size
    Args:
        content: 原始图片字节
        max_size: 允许的最大字节数，默认使用 settings.MAX_OSS_IMAGE_SIZE (5MB)
        max_dimension: 最大边长限制
    Returns:
        bytes: 压缩后的 JPEG 字节
    Raises:
        HTTPException: Pillow 未安装或压缩后仍超限
    """
    if max_size is None:
        max_size = settings.MAX_OSS_IMAGE_SIZE

    try:
        from PIL import Image
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="图片压缩服务不可用，请联系管理员安装 Pillow"
        ) from exc

    img = Image.open(io.BytesIO(content))

    # 应用 EXIF 方向修正
    try:
        exif = img._getexif()
        if exif:
            orientation = exif.get(274)
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
    except Exception:
        pass

    # 透明背景转白底 RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode in ('RGBA', 'LA'):
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # 限制最大边长
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    # 循环降低 JPEG 质量，直到满足大小限制
    quality = INITIAL_JPEG_QUALITY
    while quality >= MIN_JPEG_QUALITY:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        if buffer.tell() <= max_size:
            return buffer.getvalue()
        quality -= JPEG_QUALITY_STEP

    # 质量已最低仍超限，进一步缩小尺寸
    current_width, current_height = img.size
    while buffer.tell() > max_size and current_width > MIN_IMAGE_DIMENSION and current_height > MIN_IMAGE_DIMENSION:
        current_width = int(current_width * RESIZE_SCALE_FACTOR)
        current_height = int(current_height * RESIZE_SCALE_FACTOR)
        resized = img.resize((current_width, current_height), Image.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, format='JPEG', quality=FINAL_RESIZE_QUALITY, optimize=True)

    if buffer.tell() > max_size:
        raise HTTPException(
            status_code=413,
            detail="图片压缩后仍超过大小限制"
        )

    return buffer.getvalue()


async def upload_file_to_oss(
    file: UploadFile,
    folder: str,
    allowed_types: set[str],
    max_size: int,
    compress: bool = False,
    compress_max_dimension: int = 1024,
) -> str:
    """
    上传文件到OSS
    Args:
        file: 上传文件
        folder: 文件夹
        allowed_types: 允许的文件类型
        max_size: 最大文件大小
        compress: 是否先压缩图片再上传
        compress_max_dimension: 压缩时的最大边长限制
    Returns:
        str: 文件访问 URL
    """
    # 校验文件类型（基于客户端声明）
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    content = await file.read()

    # 通过文件头校验真实文件类型
    kind = filetype.guess(content[:2048])
    if kind is None or kind.mime not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    actual_content_type = file.content_type

    if compress and kind.mime in ALLOWED_IMAGE_TYPES:
        content = compress_image(content, max_size, compress_max_dimension)
        actual_content_type = "image/jpeg"
    elif len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制，最大支持 {max_size // 1024 // 1024} MB"
        )

    # 生成文件路径
    file_path = generate_file_path(actual_content_type, folder)

    # 上传文件
    try:
        bucket = _get_oss_bucket()
        result = await asyncio.to_thread(
            bucket.put_object,
            file_path,
            content,
            headers={'Content-Type': actual_content_type}
        )
        if result.status != 200:
            raise HTTPException(status_code=500, detail="上传文件失败")
    except HTTPException:
        raise
    except oss2.exceptions.OssError as e:
        raise HTTPException(status_code=500, detail=f"OSS上传失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")

    return _build_oss_file_url(file_path)


async def upload_image(file: UploadFile, scene: ImageUploadScene) -> str:
    """
    统一图片上传入口，根据场景自动选择路径和压缩策略
    Args:
        file: 上传文件
        scene: 上传场景枚举
    Returns:
        str: 文件访问 URL
    """
    config = SCENE_CONFIG.get(scene)
    if not config:
        raise HTTPException(status_code=400, detail=f"未知的上传场景: {scene}")

    return await upload_file_to_oss(
        file,
        folder=config["folder"],
        allowed_types=ALLOWED_IMAGE_TYPES,
        max_size=settings.MAX_OSS_IMAGE_SIZE,
        compress=True,
        compress_max_dimension=config["compress_max_dimension"],
    )


async def delete_file_from_oss(file_path: str) -> None:
    """
    删除文件从OSS（异步版本）
    Args:
        file_path: 文件路径
    Returns:
        None
    """
    if not file_path:
        return
    try:
        bucket = _get_oss_bucket()
        result = await asyncio.to_thread(bucket.delete_object, file_path)
        if result.status != 204:
            raise HTTPException(status_code=500, detail="删除文件失败")
    except HTTPException:
        raise
    except oss2.exceptions.OssError as e:
        # 忽略文件不存在错误，其余 OSS 错误抛出
        if e.status != 404:
            raise HTTPException(status_code=500, detail=f"OSS删除失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


def delete_file_from_oss_sync(file_path: str) -> None:
    """
    删除文件从OSS（同步版本，供同步Service方法使用）
    Args:
        file_path: 文件路径
    Returns:
        None
    """
    if not file_path:
        return
    try:
        bucket = _get_oss_bucket()
        result = bucket.delete_object(file_path)
        if result.status != 204:
            raise HTTPException(status_code=500, detail="删除文件失败")
    except HTTPException:
        raise
    except oss2.exceptions.OssError as e:
        # 忽略文件不存在错误，其余 OSS 错误抛出
        if e.status != 404:
            raise HTTPException(status_code=500, detail=f"OSS删除失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


def convert_oss_url_to_file_path(oss_url: str) -> str:
    """
    将OSS url转为 file_path
    Args:
        oss_url: OSS url
    Returns:
        str: file_path
    """
    if not oss_url:
        return ""
    # 若配置了 OSS_DOMAIN 且 URL 以其开头，直接截取
    if settings.OSS_DOMAIN and oss_url.startswith(settings.OSS_DOMAIN):
        file_path = oss_url[len(settings.OSS_DOMAIN):]
        return file_path.lstrip("/")
    # 兜底：通过 URL 解析提取 path
    parsed = urlparse(oss_url)
    path = parsed.path.lstrip("/")
    # 若路径以 bucket 名开头，去掉 bucket 前缀
    if settings.OSS_BUCKET_NAME and path.startswith(settings.OSS_BUCKET_NAME + "/"):
        path = path[len(settings.OSS_BUCKET_NAME) + 1:]
    return path

_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _is_oss_url(url: str) -> bool:
    """判断 URL 是否属于当前配置的 OSS。"""
    if not url:
        return False
    if settings.OSS_DOMAIN and url.startswith(settings.OSS_DOMAIN):
        return True
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if settings.OSS_BUCKET_NAME and path.startswith(settings.OSS_BUCKET_NAME + "/"):
        return True
    endpoint_host = urlparse(_normalize_oss_endpoint(settings.OSS_ENDPOINT)).netloc
    if endpoint_host and parsed.netloc == endpoint_host:
        return True
    return False


def extract_oss_image_urls_from_markdown(content_md: str) -> list[str]:
    """
    从 Markdown 正文中提取属于当前 OSS 的图片 URL。

    Args:
        content_md: Markdown 格式正文
    Returns:
        list[str]: OSS 图片 URL 列表（去重）
    """
    if not content_md:
        return []
    urls = [match.group(2).strip() for match in _MD_IMAGE_RE.finditer(content_md)]
    oss_urls = [url for url in urls if _is_oss_url(url)]
    # 去重保持顺序
    seen = set()
    result = []
    for url in oss_urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result
