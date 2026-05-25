"""user_profile_service 单元测试。"""

from unittest.mock import MagicMock

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
