import asyncio
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.crud import user_profile as profile_crud
from app.crud.conversation_message import list_conversation_messages
from app.infrastructure.llm_client import get_llm_small_client
from app.prompts.chat_prompts import (
    PROFILE_JUDGE_PROMPT,
    PROFILE_UPDATE_PROMPT,
)

logger = logging.getLogger(__name__)


class UserProfileService:
    """用户画像服务。

    每个用户仅保留一条画像记录，存于普通表 user_profiles 中。
    画像更新由 small 模型根据对话历史判断并执行。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_profile_text(self, user_id: int) -> str:
        """获取用户画像文本，无则返回空字符串。

        若画像非空，末尾附加数据库中的 updated_at 时间戳，
        便于 LLM 判断画像时效性。
        """
        record = profile_crud.get_user_profile(self.db, user_id)
        if not record or not record.profile_text:
            return ""
        ts = record.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"{record.profile_text}\n（画像更新时间：{ts}）"

    @staticmethod
    def _build_compact_aware_transcript(messages: list) -> str:
        """构造压缩态对话 transcript，含 compact summary 及其后新消息。"""
        latest_summary_index = None
        for index, msg in enumerate(messages):
            if msg.role == "assistant" and msg.meta and msg.meta.get("compact_summary"):
                latest_summary_index = index

        transcript_parts: list[str] = []
        if latest_summary_index is not None:
            summary = messages[latest_summary_index]
            transcript_parts.append(f"compact_summary: {summary.content}")
            for retained in (summary.meta or {}).get("retained_messages") or []:
                if not isinstance(retained, dict):
                    continue
                role = retained.get("role")
                content = retained.get("content") or ""
                if role in {"user", "assistant"} and content:
                    transcript_parts.append(f"{role}: {content}")
            messages = messages[latest_summary_index + 1:]

        for msg in messages:
            if msg.role == "system":
                continue
            if msg.role == "assistant" and msg.meta and msg.meta.get("tool_calls"):
                continue
            if msg.role == "tool":
                continue
            transcript_parts.append(f"{msg.role}: {msg.content}")

        return "\n".join(transcript_parts)

    async def maybe_update_user_profile(
        self, user_id: int, conversation_id: int
    ) -> None:
        """根据对话历史判断是否值得更新用户画像，值得则更新。"""
        try:
            messages = await asyncio.to_thread(
                list_conversation_messages,
                self.db,
                conversation_id,
                skip=0,
                limit=None,
            )
            if not messages:
                return

            transcript = self._build_compact_aware_transcript(messages)
            if not transcript:
                return

            # 第一步：判断是否有值得记录的信息
            judge_response = await get_llm_small_client().ainvoke([
                SystemMessage(content=PROFILE_JUDGE_PROMPT),
                HumanMessage(content=transcript),
            ])
            judge_result = (
                judge_response.content.strip()
                if isinstance(judge_response.content, str)
                else ""
            )
            judge_clean = judge_result.lower().strip(".,!?。！？ \t\n")
            if judge_clean not in ("true", "是", "是的", "yes", "1", "对", "对的", "正确"):
                logger.debug(
                    "画像判断为无需更新: user=%s conv=%s",
                    user_id,
                    conversation_id,
                )
                return

            # 第二步：读取旧画像，让 small 模型生成新画像
            old_profile = self.get_profile_text(user_id)
            update_prompt = PROFILE_UPDATE_PROMPT.format(
                old_profile=old_profile or "（暂无）"
            )

            update_response = await get_llm_small_client().ainvoke([
                SystemMessage(content=update_prompt),
                HumanMessage(content=transcript),
            ])
            new_profile = (
                update_response.content.strip()
                if isinstance(update_response.content, str)
                else ""
            )
            if not new_profile or new_profile == old_profile:
                logger.debug(
                    "画像无变化或生成空值: user=%s conv=%s",
                    user_id,
                    conversation_id,
                )
                return

            # 第三步：更新数据库
            await asyncio.to_thread(
                profile_crud.upsert_user_profile,
                self.db,
                user_id,
                new_profile,
            )
            logger.info(
                "已更新用户画像: user=%s conv=%s", user_id, conversation_id
            )
        except Exception:
            logger.exception(
                "更新用户画像失败: user=%s conv=%s", user_id, conversation_id
            )
