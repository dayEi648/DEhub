import asyncio
import logging
from typing import Any

from fastapi import HTTPException, status
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.base import RunnableConfig
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import func

from app.crud import ai_conversation as conv_crud
from app.models.ai_conversation import AIConversation
from app.models.conversation_message import ConversationMessage
from app.prompts.chat_prompts import (
    DEFAULT_SYSTEM,
    MEMORY_REFERENCE_HEADER,
    MEMORY_SUMMARY_LABEL,
    MEMORY_TURN_LABEL,
    SECURITY_CONSTRAINTS,
    TITLE_GENERATION,
)
from app.services.user_memory_service import UserMemoryService
from app.tools import search_blog, search_web

logger = logging.getLogger(__name__)

_TITLE_MAX_LENGTH = 30


class ChatState(MessagesState):
    """LangGraph 对话状态定义。

    继承 MessagesState（自动含 messages 字段与 add_messages reducer），
    扩展用户、对话、记忆等业务字段。
    """

    user_id: int
    conversation_id: int | None
    effective_system_prompt: str | None
    long_term_memories: list[str]
    blog_knowledge: list[str]
    retrieved_sources: list[dict]
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


def _build_system_prompt(memory_prompts: list[str]) -> str | None:
    """将默认 System Prompt 与长期记忆拼接，并追加安全约束。"""
    sections: list[str] = []

    sections.append(DEFAULT_SYSTEM.strip())

    if memory_prompts:
        memory_text = "\n---\n".join(memory_prompts)
        sections.append(f"{MEMORY_REFERENCE_HEADER}\n{memory_text}")

    base = "\n\n".join(sections)
    return f"{base}\n\n{SECURITY_CONSTRAINTS}"


def _require_owner(conv: AIConversation, user_id: int) -> None:
    """校验当前用户是否为对话所有者。"""
    if conv.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该对话",
        )


# ===================================================================
# 工具注册表
# ===================================================================

TOOL_REGISTRY = {
    "search_blog": search_blog,
    "search_web": search_web,
}


# ===================================================================
# 节点工厂函数
# ===================================================================


def _build_prepare_node(llm_small: BaseChatModel):
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
            title_msg = await llm_small.ainvoke(
                [
                    SystemMessage(content=TITLE_GENERATION),
                    HumanMessage(content=title_prompt),
                ]
            )
            title = title_msg.content.strip()
            title = " ".join(title.split())  # 规范化所有空白字符
            if len(title) > _TITLE_MAX_LENGTH:
                title = title[:_TITLE_MAX_LENGTH]
        except Exception:
            logger.warning("Title generation failed, using fallback")
            title = title_prompt[:_TITLE_MAX_LENGTH] if title_prompt else "New Chat"

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
                "blog_knowledge": [],
                "effective_system_prompt": state.get("system_prompt"),
            }

        last_message = messages[-1]
        query = (last_message.content or "") if isinstance(last_message, HumanMessage) else ""

        memory_service = UserMemoryService(db)
        memories = await memory_service.search_relevant_memories(
            user_id=user_id,
            query=query,
            top_k=3,
            exclude_conversation_id=conversation_id,
        )
        memory_texts = _format_memories(memories)
        effective = _build_system_prompt(memory_texts)
        return {
            "long_term_memories": memory_texts,
            "blog_knowledge": [],
            "effective_system_prompt": effective,
        }

    return retrieve_memories_node


def _build_call_model_node(llm: BaseChatModel):
    """构建【调用 LLM】节点。

    返回 Runnable 序列，使外层 astream_events 能穿透到 LLM 内部，
    从而捕获真正的 token 级流式事件（on_chat_model_stream）。
    """

    def _prepare_messages(state: ChatState) -> list:
        messages = list(state.get("messages", []))
        effective_system = state.get("effective_system_prompt")
        if effective_system:
            messages = [SystemMessage(content=effective_system), *messages]
        return messages

    def _wrap_output(msg) -> dict[str, Any]:
        return {"messages": [msg]}

    return RunnableLambda(_prepare_messages) | llm | RunnableLambda(_wrap_output)


def _build_tools_node():
    """构建【工具执行】节点（通用 registry 调用）。"""

    async def tools_node(state: ChatState, config: RunnableConfig) -> dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_msg = messages[-1]
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            return {}

        tool_results: list[ToolMessage] = []
        retrieved_sources: list[dict] = []

        # 构造带 collector 的 config，供 tool 写入来源等元数据
        base_configurable = dict(config.get("configurable", {}))
        base_configurable["_sources_collector"] = retrieved_sources
        config_with_collector = {**config, "configurable": base_configurable}

        for tc in last_msg.tool_calls:
            tool_func = TOOL_REGISTRY.get(tc["name"])
            if tool_func is None:
                tool_results.append(
                    ToolMessage(
                        content=f"未知工具: {tc['name']}",
                        tool_call_id=tc["id"],
                    )
                )
                continue

            try:
                result = await tool_func.ainvoke(tc["args"], config_with_collector)
                content = result if isinstance(result, str) else str(result)
            except Exception:
                logger.exception("Tool %s 执行失败", tc["name"])
                content = f"工具 {tc['name']} 执行失败。"

            tool_results.append(ToolMessage(content=content, tool_call_id=tc["id"]))

        return {"messages": tool_results, "retrieved_sources": retrieved_sources}

    return tools_node


def _should_continue(state: ChatState) -> str:
    """条件边：判断 model 节点输出是否包含 tool_calls。"""
    messages = state.get("messages", [])
    if not messages:
        return "persist"

    last_msg = messages[-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"
    return "persist"


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

        # 获取数据库中已有的最近消息，用于去重
        from app.crud import conversation_message as msg_crud

        existing_msgs = await asyncio.to_thread(
            msg_crud.get_recent_conversation_messages,
            db,
            conversation_id,
            limit=20,
        )
        existing_set = {(m.role, m.content) for m in existing_msgs}

        try:
            for msg in messages:
                role = None
                content = ""
                meta = None

                if isinstance(msg, HumanMessage):
                    role = "user"
                    content = msg.content or ""
                elif isinstance(msg, AIMessage):
                    role = "assistant"
                    content = msg.content or ""
                    meta = {}
                    if getattr(msg, "tool_calls", None):
                        meta["tool_calls"] = msg.tool_calls
                    # 保存 reasoning_content（DeepSeek 等 thinking 模型要求后续请求原样传回）
                    reasoning_content = msg.additional_kwargs.get("reasoning_content")
                    if reasoning_content:
                        meta["reasoning_content"] = reasoning_content
                    # 仅在最后一条 assistant 消息上附加检索来源
                    if state.get("retrieved_sources") and msg is messages[-1]:
                        meta["retrieved_sources"] = state["retrieved_sources"]
                    if not meta:
                        meta = None
                elif isinstance(msg, ToolMessage):
                    role = "tool"
                    content = msg.content or ""
                    meta = {"tool_call_id": msg.tool_call_id}

                if role and (role, content) not in existing_set:
                    db.add(
                        ConversationMessage(
                            conversation_id=conversation_id,
                            role=role,
                            content=content,
                            meta=meta,
                        )
                    )

            # 更新对话的 updated_at 时间戳
            conv.updated_at = func.now()
            await asyncio.to_thread(db.commit)
        except Exception:
            await asyncio.to_thread(db.rollback)
            logger.exception("持久化对话消息失败")
            raise

        # 找到最近的一对真正的 user/assistant 消息用于长期记忆同步
        user_msg = None
        assistant_msg = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls and assistant_msg is None:
                assistant_msg = msg
            elif isinstance(msg, HumanMessage) and user_msg is None:
                user_msg = msg
            if user_msg and assistant_msg:
                break

        # 异步触发长期记忆同步（使用独立 session）
        if user_msg and assistant_msg:
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

_graph_cache: dict[str, CompiledStateGraph] = {}


def _build_graph_key(llm: BaseChatModel, llm_small: BaseChatModel) -> str:
    """基于模型配置生成 Graph 缓存键，支持热更新时自动失效。"""
    return f"{llm.model_name}:{llm_small.model_name}"


def build_chat_graph(
    llm: BaseChatModel,
    llm_small: BaseChatModel,
    checkpointer: Any | None = None,
) -> CompiledStateGraph:
    """
    编译对话 StateGraph（按模型配置缓存）。

    Args:
        llm: 主对话模型（BaseChatModel）
        llm_small: 小模型（用于标题生成和 query 拆分）
        checkpointer: LangGraph Checkpointer 实例（如 RedisCheckpointSaver）

    Returns:
        编译后的 StateGraph（已绑定 checkpointer）
    """
    key = _build_graph_key(llm, llm_small)
    if key in _graph_cache:
        return _graph_cache[key]

    builder = StateGraph(ChatState)

    llm_with_tools = llm.bind_tools([search_blog, search_web])

    builder.add_node("prepare", _build_prepare_node(llm_small))
    builder.add_node("retrieve", _build_retrieve_node())
    builder.add_node("model", _build_call_model_node(llm_with_tools))
    builder.add_node("tools", _build_tools_node())
    builder.add_node("persist", _build_persist_node())

    builder.set_entry_point("prepare")
    builder.add_edge("prepare", "retrieve")
    builder.add_edge("retrieve", "model")
    builder.add_conditional_edges("model", _should_continue)
    builder.add_edge("tools", "model")
    builder.add_edge("persist", END)

    compiled = builder.compile(checkpointer=checkpointer)
    _graph_cache[key] = compiled
    return compiled


def invalidate_graph_cache() -> None:
    """清空 Graph 编译缓存。供配置热更新时调用。"""
    _graph_cache.clear()
