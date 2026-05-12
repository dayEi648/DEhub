import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from app.storage import oss as oss_module
from app.storage.oss import (
    convert_oss_url_to_file_path,
    upload_file_to_oss,
    delete_file_from_oss,
    ALLOWED_IMAGE_TYPES,
)


# ---------- convert_oss_url_to_file_path 测试 ----------

class TestConvertOssUrlToFilePath:
    @pytest.fixture(autouse=True)
    def patch_settings(self, monkeypatch):
        monkeypatch.setattr(oss_module.settings, "OSS_DOMAIN", "https://cdn.example.com")
        monkeypatch.setattr(oss_module.settings, "OSS_BUCKET_NAME", "my-bucket")

    def test_with_matching_domain(self):
        url = "https://cdn.example.com/users/avatar/20250101/abc.jpg"
        assert convert_oss_url_to_file_path(url) == "users/avatar/20250101/abc.jpg"

    def test_empty_url(self):
        assert convert_oss_url_to_file_path("") == ""

    def test_no_domain_fallback_parse(self, monkeypatch):
        monkeypatch.setattr(oss_module.settings, "OSS_DOMAIN", "")
        url = "https://my-bucket.oss-cn-hangzhou.aliyuncs.com/users/avatar/20250101/abc.jpg"
        assert convert_oss_url_to_file_path(url) == "users/avatar/20250101/abc.jpg"

    def test_no_domain_no_bucket_in_path(self, monkeypatch):
        monkeypatch.setattr(oss_module.settings, "OSS_DOMAIN", "")
        monkeypatch.setattr(oss_module.settings, "OSS_BUCKET_NAME", "")
        url = "https://example.com/users/avatar/20250101/abc.jpg"
        assert convert_oss_url_to_file_path(url) == "users/avatar/20250101/abc.jpg"

    def test_replace_bug_fixed(self, monkeypatch):
        # 原 replace 会替换所有匹配子串；这里确认已修复（只替换开头）
        monkeypatch.setattr(oss_module.settings, "OSS_DOMAIN", "https://cdn.example.com")
        url = "https://cdn.example.com/static/cdn.example.com/file.jpg"
        assert convert_oss_url_to_file_path(url) == "static/cdn.example.com/file.jpg"


# ---------- upload_file_to_oss 测试 ----------

class TestUploadFileToOss:
    @pytest.fixture(autouse=True)
    def patch_settings(self, monkeypatch):
        monkeypatch.setattr(oss_module.settings, "OSS_DOMAIN", "https://cdn.example.com")
        monkeypatch.setattr(oss_module.settings, "OSS_BUCKET_NAME", "my-bucket")

    @pytest.fixture
    def fake_png(self):
        # PNG 文件头 magic bytes
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 200

    @pytest.fixture
    def fake_txt(self):
        return b"this is just a text file, not an image"

    def _make_upload_file(self, content: bytes, content_type: str, filename: str = "test"):
        mock_file = MagicMock()
        mock_file.content_type = content_type
        mock_file.read = AsyncMock(return_value=content)
        mock_file.filename = filename
        return mock_file

    @pytest.mark.asyncio
    async def test_forged_content_type_blocked(self, fake_txt):
        """伪造 Content-Type 为 image/jpeg 的文本文件应被 filetype 拦截"""
        file = self._make_upload_file(fake_txt, "image/jpeg", "test.jpg")
        with pytest.raises(HTTPException) as exc_info:
            await upload_file_to_oss(file, "test", ALLOWED_IMAGE_TYPES, 1024 * 1024)
        assert exc_info.value.status_code == 400
        assert "不支持的文件类型" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_real_png_allowed(self, fake_png):
        """真实的 PNG 文件应通过校验并上传"""
        file = self._make_upload_file(fake_png, "image/png", "test.png")

        mock_result = MagicMock()
        mock_result.status = 200

        with patch.object(oss_module.bucket, "put_object", return_value=mock_result):
            url = await upload_file_to_oss(file, "test", ALLOWED_IMAGE_TYPES, 1024 * 1024)
            assert url.startswith("https://cdn.example.com/test/")

    @pytest.mark.asyncio
    async def test_oversized_file_blocked(self, fake_png):
        file = self._make_upload_file(fake_png, "image/png", "test.png")
        with pytest.raises(HTTPException) as exc_info:
            await upload_file_to_oss(file, "test", ALLOWED_IMAGE_TYPES, 50)
        assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_oss_error_raised(self, fake_png):
        """OSS 侧报错应包装为 500"""
        file = self._make_upload_file(fake_png, "image/png", "test.png")

        def raise_oss_error(*args, **kwargs):
            err = oss_module.oss2.exceptions.OssError("Mock OSS error", {}, b"", {})
            err.status = 500
            raise err

        with patch.object(oss_module.bucket, "put_object", side_effect=raise_oss_error):
            with pytest.raises(HTTPException) as exc_info:
                await upload_file_to_oss(file, "test", ALLOWED_IMAGE_TYPES, 1024 * 1024)
            assert exc_info.value.status_code == 500
            assert "OSS上传失败" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_http_exception_not_wrapped(self, fake_png):
        """上游抛出的 HTTPException 不应被二次包装"""
        file = self._make_upload_file(fake_png, "image/png", "test.png")

        def raise_http(*args, **kwargs):
            raise HTTPException(status_code=418, detail="I'm a teapot")

        with patch.object(oss_module.bucket, "put_object", side_effect=raise_http):
            with pytest.raises(HTTPException) as exc_info:
                await upload_file_to_oss(file, "test", ALLOWED_IMAGE_TYPES, 1024 * 1024)
            assert exc_info.value.status_code == 418
            assert exc_info.value.detail == "I'm a teapot"


# ---------- delete_file_from_oss 测试 ----------

class TestDeleteFileFromOss:
    @pytest.mark.asyncio
    async def test_empty_path_returns_none(self):
        """空路径应直接返回，不调用 OSS"""
        with patch.object(oss_module.bucket, "delete_object") as mock_delete:
            await delete_file_from_oss("")
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_delete(self):
        mock_result = MagicMock()
        mock_result.status = 204
        with patch.object(oss_module.bucket, "delete_object", return_value=mock_result) as mock_delete:
            await delete_file_from_oss("users/avatar/20250101/abc.jpg")
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_404_ignored(self):
        """文件不存在（404）应静默忽略"""
        def raise_404(*args, **kwargs):
            err = oss_module.oss2.exceptions.OssError("NoSuchKey", {}, b"", {})
            err.status = 404
            raise err

        with patch.object(oss_module.bucket, "delete_object", side_effect=raise_404):
            await delete_file_from_oss("users/avatar/20250101/abc.jpg")

    @pytest.mark.asyncio
    async def test_other_oss_error_raised(self):
        """非 404 的 OSS 错误应抛出 500"""
        def raise_403(*args, **kwargs):
            err = oss_module.oss2.exceptions.OssError("AccessDenied", {}, b"", {})
            err.status = 403
            raise err

        with patch.object(oss_module.bucket, "delete_object", side_effect=raise_403):
            with pytest.raises(HTTPException) as exc_info:
                await delete_file_from_oss("users/avatar/20250101/abc.jpg")
            assert exc_info.value.status_code == 500
            assert "OSS删除失败" in exc_info.value.detail
