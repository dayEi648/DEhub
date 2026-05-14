import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from app.storage import oss as oss_module
from app.storage.oss import (
    convert_oss_url_to_file_path,
    upload_file_to_oss,
    delete_file_from_oss,
    compress_image,
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


# ---------- compress_image 测试 ----------

class TestCompressImage:
    def test_pillow_not_installed(self, monkeypatch):
        """Pillow 未安装时应抛出 500"""
        original_import = __builtins__["__import__"]

        def mock_import(name, *args, **kwargs):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError("No module named 'PIL'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)
        with pytest.raises(HTTPException) as exc_info:
            compress_image(b"fake", 1024)
        assert exc_info.value.status_code == 500
        assert "图片压缩服务不可用" in exc_info.value.detail

    def _mock_pil(self, mock_img):
        """构造可注入 sys.modules 的 mock PIL 模块"""
        from unittest.mock import MagicMock
        import sys

        mock_pil = MagicMock()
        mock_pil.Image.open.return_value = mock_img
        mock_pil.Image.new.return_value = mock_img
        return mock_pil

    def test_compress_success(self):
        """正常压缩应返回 JPEG 字节"""
        from unittest.mock import MagicMock, patch
        import sys

        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.size = (800, 600)
        mock_img._getexif.return_value = None

        def fake_thumbnail(size, filter):
            mock_img.size = (800, 600)

        mock_img.thumbnail = fake_thumbnail

        def fake_save(fp, *args, **kwargs):
            fp.write(b"compressed_jpeg_bytes")

        mock_img.save = fake_save

        mock_pil = self._mock_pil(mock_img)
        with patch.dict(sys.modules, {"PIL": mock_pil, "PIL.Image": mock_pil.Image}):
            result = compress_image(b"fake_png", 1024 * 1024)
            assert result == b"compressed_jpeg_bytes"

    def test_compress_exif_orientation(self):
        """EXIF 方向标记应被正确应用"""
        from unittest.mock import MagicMock, patch
        import sys

        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.size = (600, 800)
        mock_img._getexif.return_value = {274: 6}

        rotated_img = MagicMock()
        rotated_img.mode = "RGB"
        rotated_img.size = (800, 600)
        rotated_img._getexif.return_value = None

        def fake_rotate(angle, expand=False):
            return rotated_img

        mock_img.rotate = fake_rotate

        def fake_thumbnail(size, filter):
            pass

        mock_img.thumbnail = fake_thumbnail
        rotated_img.thumbnail = fake_thumbnail

        def fake_save(fp, *args, **kwargs):
            fp.write(b"rotated_jpeg")

        rotated_img.save = fake_save

        mock_pil = self._mock_pil(mock_img)
        mock_pil.Image.open.return_value = mock_img
        with patch.dict(sys.modules, {"PIL": mock_pil, "PIL.Image": mock_pil.Image}):
            result = compress_image(b"fake", 1024 * 1024)
            assert result == b"rotated_jpeg"

    def test_compress_rgba_to_rgb(self):
        """RGBA 透明图应转为白底 RGB"""
        from unittest.mock import MagicMock, patch
        import sys

        mock_bg = MagicMock()
        mock_bg.mode = "RGB"
        mock_bg.size = (500, 500)
        mock_bg._getexif.return_value = None

        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_img.size = (500, 500)
        mock_img._getexif.return_value = None
        mock_img.split.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

        def fake_paste(src, mask=None):
            pass

        mock_bg.paste = fake_paste

        def fake_thumbnail(size, filter):
            pass

        mock_bg.thumbnail = fake_thumbnail

        def fake_save(fp, *args, **kwargs):
            fp.write(b"rgb_jpeg")

        mock_bg.save = fake_save

        mock_pil = self._mock_pil(mock_img)
        mock_pil.Image.new.return_value = mock_bg
        mock_pil.Image.open.return_value = mock_img
        with patch.dict(sys.modules, {"PIL": mock_pil, "PIL.Image": mock_pil.Image}):
            result = compress_image(b"fake", 1024 * 1024)
            assert result == b"rgb_jpeg"

    def test_compress_still_oversized_raises(self):
        """压缩后仍超过限制应抛出 413"""
        from unittest.mock import MagicMock, patch
        import sys

        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_img.size = (50, 50)
        mock_img._getexif.return_value = None

        def fake_thumbnail(size, filter):
            mock_img.size = (50, 50)

        mock_img.thumbnail = fake_thumbnail

        def fake_save(fp, *args, **kwargs):
            fp.write(b"x" * 10000)

        mock_img.save = fake_save

        mock_pil = self._mock_pil(mock_img)
        with patch.dict(sys.modules, {"PIL": mock_pil, "PIL.Image": mock_pil.Image}):
            with pytest.raises(HTTPException) as exc_info:
                compress_image(b"fake", 100)
            assert exc_info.value.status_code == 413
            assert "压缩后仍超过" in exc_info.value.detail


# ---------- upload_file_to_oss compress 测试 ----------

class TestUploadFileToOssCompress:
    @pytest.fixture(autouse=True)
    def patch_settings(self, monkeypatch):
        monkeypatch.setattr(oss_module.settings, "OSS_DOMAIN", "https://cdn.example.com")
        monkeypatch.setattr(oss_module.settings, "OSS_BUCKET_NAME", "my-bucket")

    @pytest.fixture
    def fake_png(self):
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 200

    def _make_upload_file(self, content: bytes, content_type: str, filename: str = "test"):
        mock_file = MagicMock()
        mock_file.content_type = content_type
        mock_file.read = AsyncMock(return_value=content)
        mock_file.filename = filename
        return mock_file

    @pytest.mark.asyncio
    async def test_compress_enabled_calls_compress_and_uploads_jpeg(self, fake_png):
        """开启压缩时应调用 compress_image 并上传 JPEG"""
        file = self._make_upload_file(fake_png, "image/png", "test.png")

        mock_result = MagicMock()
        mock_result.status = 200

        with patch.object(oss_module, "compress_image", return_value=b"compressed_jpeg") as mock_compress:
            with patch.object(oss_module.bucket, "put_object", return_value=mock_result) as mock_put:
                url = await upload_file_to_oss(
                    file, "avatars", ALLOWED_IMAGE_TYPES, 1024 * 1024, compress=True
                )
                mock_compress.assert_called_once_with(fake_png, 1024 * 1024, 1024)
                assert url.startswith("https://cdn.example.com/avatars/")
                # 验证 Content-Type 为 jpeg
                call_kwargs = mock_put.call_args[1]
                assert call_kwargs.get("headers", {}).get("Content-Type") == "image/jpeg"

    @pytest.mark.asyncio
    async def test_compress_enabled_uses_given_max_dimension(self, fake_png):
        """应传递自定义的 compress_max_dimension"""
        file = self._make_upload_file(fake_png, "image/png", "test.png")

        mock_result = MagicMock()
        mock_result.status = 200

        with patch.object(oss_module, "compress_image", return_value=b"compressed") as mock_compress:
            with patch.object(oss_module.bucket, "put_object", return_value=mock_result):
                await upload_file_to_oss(
                    file, "avatars", ALLOWED_IMAGE_TYPES, 1024 * 1024,
                    compress=True, compress_max_dimension=512
                )
                mock_compress.assert_called_once_with(fake_png, 1024 * 1024, 512)

    @pytest.mark.asyncio
    async def test_compress_disabled_oversized_blocked(self, fake_png):
        """未开启压缩时超大文件仍应被拦截"""
        file = self._make_upload_file(fake_png, "image/png", "test.png")
        with pytest.raises(HTTPException) as exc_info:
            await upload_file_to_oss(file, "test", ALLOWED_IMAGE_TYPES, 50, compress=False)
        assert exc_info.value.status_code == 413
