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
        """获取用户画像文本，无则返回空字符串。"""
        record = profile_crud.get_user_profile(self.db, user_id)
        return record.profile_text if record else ""

    async def maybe_update_user_profile(
        self, user_id: int, conversation_id: int
    ) -> None:
        """判断当前对话是否值得更新用户画像，如值得则执行更新。

        流程：
        1. 从数据库读取对话完整历史
        2. 交给 small 模型判断是否有值得记录的信息（true/false）
        3. false → 直接返回
        4. true → 读取旧画像 → small 模型生成新画像 → upsert
        """
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

            transcript = "\n".join(
                f"{msg.role}: {msg.content}" for msg in messages
            )

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
