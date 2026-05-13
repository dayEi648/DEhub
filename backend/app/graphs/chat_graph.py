import asyncio
import logging
from typing import Any

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.base import RunnableConfig
from langgraph.graph import END, MessagesState, StateGraph
from sqlalchemy import func

from app.crud import ai_conversation as conv_crud
from app.crud import conversation_message as msg_crud
from app.infrastructure.langchain_adapter import CustomChatModel
from app.models.ai_conversation import AIConversation
from app.prompts.chat_prompts import (
    MEMORY_REFERENCE_HEADER,
    MEMORY_SUMMARY_LABEL,
    MEMORY_TURN_LABEL,
    TITLE_GENERATION,
)
from app.services.user_memory_service import UserMemoryService

logger = logging.getLogger(__name__)

_TITLE_MAX_LENGTH = 30


class ChatState(MessagesState):
    """LangGraph 对话状态定义。

    继承 MessagesState（自动含 messages 字段与 add_messages reducer），
    扩展用户、对话、记忆等业务字段。
    """

    user_id: int
    conversation_id: int | None
    system_prompt: str | None
    effective_system_prompt: str | None
    long_term_memories: list[str]
    conversation: Any
    title_prompt: str | None


# ===================================================================
# 节点工厂函数
# ===================================================================


def _format_memories(memories: list) -> list[str]:
    """将记忆记录列表格式化为文本块列表。"""
    if not memories:
        return []
    return [
        f"{MEMORY_SUMMARY_LABEL if mem.memory_type == 'summary' else MEMORY_TURN_LABEL} {mem.content_text}"
        for mem in memories
    ]


def _build_system_prompt(
    original_system: str | None, memory_prompts: list[str]
) -> str | None:
    """将原始 System Prompt 与长期记忆拼接。"""
    if not memory_prompts:
        return original_system
    memory_text = "\n---\n".join(memory_prompts)
    memory_section = f"{MEMORY_REFERENCE_HEADER}\n{memory_text}"
    base = original_system.strip() if original_system else ""
    if base:
        return f"{base}\n\n{memory_section}"
    return memory_section


def _require_owner(conv: AIConversation, user_id: int) -> None:
    """校验当前用户是否为对话所有者。"""
    if conv.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该对话",
        )


def _build_prepare_node(llm_small: CustomChatModel):
    """构建【获取/创建对话】节点。"""

    async def prepare_conversation_node(
        state: ChatState, config: RunnableConfig
    ) -> dict[str, Any]:
        db = config["configurable"]["db"]
        conversation_id = state.get("conversation_id")
        user_id = state["user_id"]

        if conversation_id is not None:
            conv = await asyncio.to_thread(
                conv_crud.get_ai_conversation_by_id, db, conversation_id
            )
            if conv is None or conv.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="对话不存在",
                )
            _require_owner(conv, user_id)
            return {"conversation": conv}

        # 新建对话：生成标题
        title_prompt = state.get("title_prompt", "")
        try:
            title = await llm_small.ainvoke(
                [
                    SystemMessage(content=TITLE_GENERATION),
                    HumanMessage(content=title_prompt),
                ]
            )
            title = title.content.strip().replace("\n", " ")
            if len(title) > _TITLE_MAX_LENGTH:
                title = title[:_TITLE_MAX_LENGTH]
        except Exception:
            logger.warning("Title generation failed, using fallback")
            title = title_prompt[:_TITLE_MAX_LENGTH]

        conv = await asyncio.to_thread(
            conv_crud.create_ai_conversation, db, user_id, title
        )
        return {"conversation": conv, "conversation_id": conv.id}

    return prepare_conversation_node


def _build_retrieve_node():
    """构建【检索长期记忆】节点。"""

    async def retrieve_memories_node(
        state: ChatState, config: RunnableConfig
    ) -> dict[str, Any]:
        db = config["configurable"]["db"]
        user_id = state["user_id"]
        conversation_id = state.get("conversation_id")

        # 从 messages 中提取最后一条用户输入作为 query
        messages = state.get("messages", [])
        if not messages:
            return {
                "long_term_memories": [],
                "effective_system_prompt": state.get("system_prompt"),
            }

        last_message = messages[-1]
        query = last_message.content or "" if isinstance(last_message, HumanMessage) else ""

        memory_service = UserMemoryService(db)
        memories = await memory_service.search_relevant_memories(
            user_id=user_id,
            query=query,
            top_k=3,
            exclude_conversation_id=conversation_id,
        )
        memory_texts = _format_memories(memories)
        effective = _build_system_prompt(
            state.get("system_prompt"), memory_texts
        )
        return {
            "long_term_memories": memory_texts,
            "effective_system_prompt": effective,
        }

    return retrieve_memories_node


def _build_call_model_node(llm: CustomChatModel):
    """构建【调用 LLM】节点。"""

    async def call_model_node(state: ChatState, config: RunnableConfig) -> dict[str, Any]:
        messages = list(state.get("messages", []))
        effective_system = state.get("effective_system_prompt")

        if effective_system:
            messages = [SystemMessage(content=effective_system), *messages]

        chunks = []
        async for chunk in llm.astream(messages):
            chunks.append(chunk.content)

        full_content = "".join(chunks)
        return {"messages": [AIMessage(content=full_content)]}

    return call_model_node


async def _run_memory_sync(
    user_id: int,
    conversation_id: int,
    user_content: str,
    assistant_content: str,
) -> None:
    """使用独立数据库会话执行记忆同步后台任务。"""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        svc = UserMemoryService(db)
        await svc.sync_turn_memory(
            user_id, conversation_id, user_content, assistant_content
        )
        await svc.sync_conversation_summary(user_id, conversation_id)
    finally:
        await asyncio.to_thread(db.close)


def _build_persist_node():
    """构建【持久化】节点。"""

    async def persist_node(state: ChatState, config: RunnableConfig) -> dict[str, Any]:
        db = config["configurable"]["db"]
        conv = state.get("conversation")
        if not conv:
            return {}

        conversation_id = conv.id
        messages = state.get("messages", [])

        # 找到最近的一对 user/assistant 消息写入 DB
        # messages 是由 add_messages reducer 维护的完整列表
        if len(messages) >= 2:
            # 倒数第二条应为 user，倒数第一条应为 assistant
            user_msg = messages[-2]
            assistant_msg = messages[-1]
            if isinstance(user_msg, HumanMessage):
                await asyncio.to_thread(
                    msg_crud.create_conversation_message,
                    db,
                    conversation_id,
                    "user",
                    user_msg.content or "",
                )
            if isinstance(assistant_msg, AIMessage):
                await asyncio.to_thread(
                    msg_crud.create_conversation_message,
                    db,
                    conversation_id,
                    "assistant",
                    assistant_msg.content or "",
                )
        elif len(messages) == 1 and isinstance(messages[0], HumanMessage):
            # 只有 user 消息（理论上不应发生，因为 call_model 会追加 AI 消息）
            await asyncio.to_thread(
                msg_crud.create_conversation_message,
                db,
                conversation_id,
                "user",
                messages[0].content or "",
            )

        # 更新对话的 updated_at 时间戳
        conv.updated_at = func.now()

        try:
            await asyncio.to_thread(db.commit)
        except Exception:
            await asyncio.to_thread(db.rollback)
            logger.exception("持久化对话消息失败")
            raise

        # 异步触发长期记忆同步（使用独立 session）
        if len(messages) >= 2:
            user_msg = messages[-2]
            assistant_msg = messages[-1]
            if isinstance(user_msg, HumanMessage) and isinstance(
                assistant_msg, AIMessage
            ):
                asyncio.create_task(
                    _fire_and_forget(
                        _run_memory_sync(
                            state["user_id"],
                            conversation_id,
                            user_msg.content or "",
                            assistant_msg.content or "",
                        )
                    )
                )

        return {}

    return persist_node


async def _fire_and_forget(coro) -> None:
    """包装协程，捕获异常并记录日志。"""
    try:
        await coro
    except Exception:
        logger.exception("长期记忆后台任务失败")


# ===================================================================
# Graph 构建工厂
# ===================================================================

_graph_instance: StateGraph | None = None


def build_chat_graph(
    llm: CustomChatModel,
    llm_small: CustomChatModel,
) -> StateGraph:
    """
    编译对话 StateGraph（单例缓存）。

    Args:
        llm: 主对话模型（CustomChatModel）
        llm_small: 小模型（用于标题生成）

    Returns:
        编译后的 StateGraph（尚未注入 checkpointer，由调用方注入）
    """
    global _graph_instance
    if _graph_instance is not None:
        return _graph_instance

    builder = StateGraph(ChatState)

    builder.add_node("prepare", _build_prepare_node(llm_small))
    builder.add_node("retrieve", _build_retrieve_node())
    builder.add_node("model", _build_call_model_node(llm))
    builder.add_node("persist", _build_persist_node())

    builder.set_entry_point("prepare")
    builder.add_edge("prepare", "retrieve")
    builder.add_edge("retrieve", "model")
    builder.add_edge("model", "persist")
    builder.add_edge("persist", END)

    _graph_instance = builder.compile()
    return _graph_instance
