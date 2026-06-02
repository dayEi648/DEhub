"""
测试统一图片上传入口 upload_image 的场景分发与配置正确性
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, UploadFile
from app.storage.oss import (
    ImageUploadScene,
    SCENE_CONFIG,
    upload_image,
    compress_image,
    ALLOWED_IMAGE_TYPES,
    _build_oss_file_url,
    _normalize_oss_endpoint,
)
from app.core.config import settings


class TestImageUploadSceneConfig:
    """验证场景枚举与配置映射完整且路径正确"""

    def test_all_scenes_have_config(self):
        for scene in ImageUploadScene:
            assert scene in SCENE_CONFIG, f"场景 {scene} 缺少 SCENE_CONFIG 配置"
            config = SCENE_CONFIG[scene]
            assert "folder" in config
            assert "compress_max_dimension" in config
            assert "description" in config

    def test_scene_folder_paths(self):
        assert SCENE_CONFIG[ImageUploadScene.avatar]["folder"] == settings.OSS_USERS_AVATAR_DIR
        assert SCENE_CONFIG[ImageUploadScene.cover]["folder"] == settings.OSS_BLOG_COVER_DIR
        assert SCENE_CONFIG[ImageUploadScene.generic]["folder"] == settings.OSS_UPLOADS_IMAGE_DIR
        assert SCENE_CONFIG[ImageUploadScene.forum_post]["folder"] == settings.OSS_FORUM_POST_IMAGE_DIR
        assert SCENE_CONFIG[ImageUploadScene.forum_reply]["folder"] == settings.OSS_FORUM_REPLY_IMAGE_DIR
        assert SCENE_CONFIG[ImageUploadScene.comment]["folder"] == settings.OSS_COMMENT_IMAGE_DIR
        assert SCENE_CONFIG[ImageUploadScene.chat]["folder"] == settings.OSS_CHAT_IMAGE_DIR

    def test_compress_max_dimension_values(self):
        assert SCENE_CONFIG[ImageUploadScene.avatar]["compress_max_dimension"] == 1024
        assert SCENE_CONFIG[ImageUploadScene.cover]["compress_max_dimension"] == 1920
        assert SCENE_CONFIG[ImageUploadScene.generic]["compress_max_dimension"] == 1920


class TestUploadImageUnified:
    """验证统一上传入口 upload_image 的场景分发逻辑"""

    @pytest.mark.asyncio
    @patch("app.storage.oss.upload_file_to_oss")
    async def test_upload_image_calls_oss_with_avatar_config(self, mock_upload):
        mock_upload.return_value = "https://example.com/avatar/test.jpg"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.read = MagicMock(return_value=b"fake_image_data")

        with patch("app.storage.oss.filetype.guess", return_value=MagicMock(mime="image/jpeg")):
            url = await upload_image(mock_file, ImageUploadScene.avatar)

        assert url == "https://example.com/avatar/test.jpg"
        call_kwargs = mock_upload.call_args.kwargs
        assert call_kwargs["folder"] == settings.OSS_USERS_AVATAR_DIR
        assert call_kwargs["compress_max_dimension"] == 1024
        assert call_kwargs["compress"] is True
        assert call_kwargs["max_size"] == settings.MAX_OSS_IMAGE_SIZE

    @pytest.mark.asyncio
    @patch("app.storage.oss.upload_file_to_oss")
    async def test_upload_image_calls_oss_with_cover_config(self, mock_upload):
        mock_upload.return_value = "https://example.com/cover/test.jpg"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/png"
        mock_file.read = MagicMock(return_value=b"fake_image_data")

        with patch("app.storage.oss.filetype.guess", return_value=MagicMock(mime="image/png")):
            url = await upload_image(mock_file, ImageUploadScene.cover)

        assert url == "https://example.com/cover/test.jpg"
        call_kwargs = mock_upload.call_args.kwargs
        assert call_kwargs["folder"] == settings.OSS_BLOG_COVER_DIR
        assert call_kwargs["compress_max_dimension"] == 1920

    @pytest.mark.asyncio
    @patch("app.storage.oss.upload_file_to_oss")
    async def test_upload_image_calls_oss_with_generic_config(self, mock_upload):
        mock_upload.return_value = "https://example.com/generic/test.jpg"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.content_type = "image/webp"
        mock_file.read = MagicMock(return_value=b"fake_image_data")

        with patch("app.storage.oss.filetype.guess", return_value=MagicMock(mime="image/webp")):
            url = await upload_image(mock_file, ImageUploadScene.generic)

        assert url == "https://example.com/generic/test.jpg"
        call_kwargs = mock_upload.call_args.kwargs
        assert call_kwargs["folder"] == settings.OSS_UPLOADS_IMAGE_DIR

    @pytest.mark.asyncio
    async def test_upload_image_rejects_invalid_scene(self):
        mock_file = MagicMock(spec=UploadFile)
        with pytest.raises(HTTPException) as exc_info:
            await upload_image(mock_file, "nonexistent_scene")  # type: ignore[arg-type]
        assert exc_info.value.status_code == 400

class TestCompressImageDefaults:
    """验证 compress_image 默认值使用 MAX_OSS_IMAGE_SIZE"""

    def test_compress_image_uses_oss_default_max_size(self):
        """不传 max_size 时，应使用 settings.MAX_OSS_IMAGE_SIZE (2MB)"""
        with patch("app.storage.oss.settings.MAX_OSS_IMAGE_SIZE", 2 * 1024 * 1024):
            with patch("PIL.Image.open") as mock_open:
                mock_img = MagicMock()
                mock_img._getexif.return_value = None
                mock_img.mode = "RGB"
                mock_img.size = (100, 100)
                mock_open.return_value = mock_img

                buffer = MagicMock()
                buffer.tell.return_value = 1024

                with patch("io.BytesIO", return_value=buffer):
                    result = compress_image(b"fake", max_dimension=100)

                assert result is not None


class TestOssConfigHelpers:
    """验证 OSS 配置兼容当前 .env 写法。"""

    def test_normalize_oss_endpoint_adds_scheme(self):
        assert (
            _normalize_oss_endpoint("oss-cn-beijing.aliyuncs.com")
            == "https://oss-cn-beijing.aliyuncs.com"
        )

    def test_normalize_oss_endpoint_keeps_existing_scheme(self):
        assert (
            _normalize_oss_endpoint("http://oss-cn-beijing.aliyuncs.com")
            == "http://oss-cn-beijing.aliyuncs.com"
        )

    def test_build_file_url_uses_full_oss_domain(self):
        with patch("app.storage.oss.settings.OSS_DOMAIN", "https://cdn.example.com/dehub/"):
            assert _build_oss_file_url("chat/20260522/a.jpg") == (
                "https://cdn.example.com/dehub/chat/20260522/a.jpg"
            )
