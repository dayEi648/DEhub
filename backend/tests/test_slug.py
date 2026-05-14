import pytest
from unittest.mock import MagicMock

from app.utils.slug import generate_slug, generate_unique_slug


class TestGenerateSlug:
    def test_english_simple(self):
        """英文标题应转为小写并用连字符连接"""
        assert generate_slug("Hello World") == "hello-world"

    def test_chinese_preserved(self):
        """中文字符应原样保留"""
        assert generate_slug("我的第一篇博客") == "我的第一篇博客"

    def test_mixed_chinese_english(self):
        """中英文混合应正确处理"""
        assert generate_slug("Hello 世界") == "hello-世界"

    def test_special_chars_removed(self):
        """特殊字符应被移除"""
        assert generate_slug("a!@#b") == "ab"

    def test_multiple_spaces_collapsed(self):
        """多个空格应合并为单个连字符"""
        assert generate_slug("a   b") == "a-b"

    def test_underscore_to_hyphen(self):
        """下划线应转为连字符"""
        assert generate_slug("a_b_c") == "a-b-c"

    def test_empty_string(self):
        """空字符串应返回 untitled"""
        assert generate_slug("") == "untitled"

    def test_whitespace_only(self):
        """仅空白字符应返回 untitled"""
        assert generate_slug("   ") == "untitled"

    def test_consecutive_hyphens_collapsed(self):
        """连续连字符应合并"""
        assert generate_slug("a---b") == "a-b"

    def test_leading_trailing_hyphens_removed(self):
        """首尾连字符应去除"""
        assert generate_slug("-abc-") == "abc"

    def test_leading_trailing_spaces(self):
        """首尾空格应去除"""
        assert generate_slug("  hello world  ") == "hello-world"

    def test_numbers_preserved(self):
        """数字应保留"""
        assert generate_slug("Chapter 1 Introduction") == "chapter-1-introduction"

    def test_very_long_text_truncated(self):
        """超过 100 字符的文本应截断"""
        long_text = "a" * 150
        result = generate_slug(long_text)
        assert len(result) <= 100
        assert result == "a" * 100

    def test_truncation_removes_trailing_hyphen(self):
        """截断时若尾部为连字符应去除"""
        text = "a-" * 60  # 约 120 字符，截断后尾部可能是连字符
        result = generate_slug(text)
        assert not result.endswith("-")

    def test_unicode_normalization(self):
        """组合字符应被规范化"""
        # é 可以是 U+00E9 或 U+0065 U+0301
        assert generate_slug("caf\u00e9") == generate_slug("caf\u0065\u0301")

    def test_mixed_punctuation(self):
        """混合标点应被正确处理"""
        assert generate_slug("What's New?!?") == "whats-new"


class TestGenerateUniqueSlug:
    def test_first_attempt_succeeds(self):
        """当 slug 不存在时，直接返回基础 slug"""
        db = MagicMock()
        checker = MagicMock(return_value=None)

        result = generate_unique_slug(db, "Hello World", exists_checker=checker)

        assert result == "hello-world"
        checker.assert_called_once_with(db, "hello-world")

    def test_second_attempt_with_suffix(self):
        """当基础 slug 存在时，追加 -1"""
        db = MagicMock()
        checker = MagicMock(side_effect=[MagicMock(), None])

        result = generate_unique_slug(db, "Hello World", exists_checker=checker)

        assert result == "hello-world-1"
        assert checker.call_count == 2
        checker.assert_any_call(db, "hello-world")
        checker.assert_any_call(db, "hello-world-1")

    def test_multiple_conflicts(self):
        """当多个 slug 都存在时，持续递增后缀"""
        db = MagicMock()
        # 前 3 次都存在，第 4 次不存在
        checker = MagicMock(side_effect=[MagicMock(), MagicMock(), MagicMock(), None])

        result = generate_unique_slug(db, "Hello World", exists_checker=checker)

        assert result == "hello-world-3"
        assert checker.call_count == 4

    def test_invalid_checker_raises(self):
        """传入非 callable 的 checker 应抛出 ValueError"""
        with pytest.raises(ValueError, match="exists_checker must be a callable"):
            generate_unique_slug(MagicMock(), "test", exists_checker="not-callable")

    def test_safety_limit(self):
        """超过最大尝试次数应抛出 RuntimeError"""
        db = MagicMock()
        checker = MagicMock(return_value=MagicMock())  # 永远存在

        with pytest.raises(RuntimeError, match="Unable to generate a unique slug"):
            generate_unique_slug(db, "test", exists_checker=checker)
