"""user_profile_service 单元测试。"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.user_profile_service import UserProfileService


class TestUserProfileCompactAwareTranscript:
    """测试用户画像更新使用 compact-aware 历史。"""

    @staticmethod
    def _message(role: str, content: str, meta: dict | None = None) -> MagicMock:
        msg = MagicMock()
        msg.role = role
        msg.content = content
        msg.meta = meta
        return msg

    def test_uses_latest_compact_summary_and_new_messages_only(self):
        messages = [
            self._message("user", "压缩前旧问题"),
            self._message("assistant", "压缩前旧回答"),
            self._message(
                "assistant",
                "真实摘要",
                {
                    "compact_summary": True,
                    "retained_messages": [
                        {"role": "user", "content": "最近问题"},
                        {"role": "assistant", "content": "最近回答"},
                    ],
                },
            ),
            self._message("user", "压缩后新问题"),
            self._message("assistant", "工具前说明", {"tool_calls": [{"name": "web_search"}]}),
            self._message("tool", "工具结果"),
            self._message("assistant", "压缩后新回答"),
        ]

        transcript = UserProfileService._build_compact_aware_transcript(messages)

        assert "真实摘要" in transcript
        assert "最近问题" in transcript
        assert "最近回答" in transcript
        assert "压缩后新问题" in transcript
        assert "压缩后新回答" in transcript
        assert "压缩前旧问题" not in transcript
        assert "工具前说明" not in transcript
        assert "工具结果" not in transcript


class TestGetProfileText:
    """测试 get_profile_text 返回带时间戳的画像文本。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = UserProfileService(self.mock_db)

    @patch("app.services.user_profile_service.profile_crud.get_user_profile")
    def test_get_profile_text_includes_timestamp(self, mock_get_profile):
        """画像非空时，末尾应附加 updated_at 时间戳。"""
        mock_record = MagicMock()
        mock_record.profile_text = "用户喜欢 Python 和 Vue。"
        mock_record.updated_at = datetime(2026, 6, 1, 10, 30, 0, tzinfo=timezone.utc)
        mock_get_profile.return_value = mock_record

        result = self.service.get_profile_text(1)

        assert "用户喜欢 Python 和 Vue。" in result
        assert "画像更新时间：2026-06-01 10:30:00" in result

    @patch("app.services.user_profile_service.profile_crud.get_user_profile")
    def test_get_profile_text_empty_returns_empty(self, mock_get_profile):
        """画像为空或无记录时，返回空字符串，不附加时间戳。"""
        mock_record = MagicMock()
        mock_record.profile_text = ""
        mock_record.updated_at = datetime(2026, 6, 1, 10, 30, 0, tzinfo=timezone.utc)
        mock_get_profile.return_value = mock_record

        result = self.service.get_profile_text(1)
        assert result == ""

    @patch("app.services.user_profile_service.profile_crud.get_user_profile")
    def test_get_profile_text_none_returns_empty(self, mock_get_profile):
        """无记录时返回空字符串。"""
        mock_get_profile.return_value = None

        result = self.service.get_profile_text(1)
        assert result == ""
