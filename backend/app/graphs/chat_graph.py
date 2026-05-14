import asyncio
import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.base import RunnableConfig
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import func

from app.core.config import settings
from app.crud import ai_conversation as conv_crud
from langchain_core.language_models.chat_models import BaseChatModel
from app.models.ai_conversation import AIConversation
from app.models.conversation_message import ConversationMessage
from app.prompts.chat_prompts import (
    BLOG_KNOWLEDGE_HEADER,
    BLOG_KNOWLEDGE_LABEL,
    DEFAULT_SYSTEM,
    MEMORY_REFERENCE_HEADER,
    MEMORY_SUMMARY_LABEL,
    MEMORY_TURN_LABEL,
    SECURITY_CONSTRAINTS,
    TITLE_GENERATION,
    WEB_SEARCH_HEADER,
    WEB_SEARCH_LABEL,
    WEB_SEARCH_QUERY_SPLIT,
)
from app.services.user_memory_service import UserMemoryService
from app.services.vector_search_service import BlogVectorSearchService
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


def _format_blog_knowledge(results: list) -> list[str]:
    """将博客检索结果格式化为文本块列表。"""
    if not results:
        return []
    formatted: list[str] = []
    for result in results:
        title = result.title or ""
        slug = result.slug or ""
        summary = result.summary or ""
        parts = [f"{BLOG_KNOWLEDGE_LABEL} {title}"]
        if slug:
            parts.append(f"链接：/blog/{slug}")
        if summary:
            parts.append(summary)
        formatted.append("\n".join(parts))
    return formatted


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
# 联网搜索辅助函数
# ===================================================================

_IQS_ENDPOINT = "https://cloud-iqs.aliyuncs.com/search/unified"
_IQS_TIMEOUT = 30


async def _iqs_search_single(query: str, api_key: str) -> list[dict]:
    """对单个 query 调用阿里云 IQS Search，返回 pageItems 列表。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "engineType": "Generic",
        "numResults": 10,
        "contents": {
            "mainText": False,
            "markdownText": False,
            "richMainBody": False,
            "summary": False,
            "rerankScore": True,
        },
    }
    async with httpx.AsyncClient(timeout=_IQS_TIMEOUT) as client:
        resp = await client.post(_IQS_ENDPOINT, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("pageItems", [])


async def _split_search_queries(query: str, llm_small: BaseChatModel) -> list[str]:
    """使用 small LLM 将用户 query 拆分为 1~5 个搜索片段。"""
    try:
        msg = await llm_small.ainvoke(
            [
                SystemMessage(content=WEB_SEARCH_QUERY_SPLIT),
                HumanMessage(content=query),
            ]
        )
        lines = [line.strip() for line in (msg.content or "").splitlines() if line.strip()]
        return lines[:5] if lines else [query]
    except Exception:
        logger.warning("Query 拆分失败，回退到原始 query")
        return [query]


def _format_web_search_results(results: list[dict]) -> str:
    """将 IQS pageItems 列表格式化为文本块。"""
    if not results:
        return "未找到相关网络搜索结果。"

    lines: list[str] = []
    for item in results:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        hostname = item.get("hostname", "")
        parts = [f"{WEB_SEARCH_LABEL} {title}"]
        if hostname:
            parts.append(f"来源：{hostname}")
        if snippet:
            parts.append(snippet)
        if link:
            parts.append(f"链接：{link}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


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

    统一使用 .ainvoke() 调用 LLM，由外层 astream_events 捕获流式 token。
    """

    async def call_model_node(state: ChatState, config: RunnableConfig) -> dict[str, Any]:
        messages = list(state.get("messages", []))
        effective_system = state.get("effective_system_prompt")

        if effective_system:
            messages = [SystemMessage(content=effective_system), *messages]

        response = await llm.ainvoke(messages)
        return {"messages": [response]}

    return call_model_node


def _build_tools_node(llm_small: BaseChatModel):
    """构建【工具执行】节点。"""

    async def tools_node(state: ChatState, config: RunnableConfig) -> dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_msg = messages[-1]
        if not isinstance(last_msg, AIMessage) or not last_msg.tool_calls:
            return {}

        db = config["configurable"]["db"]
        tool_results: list[ToolMessage] = []

        retrieved_sources: list[dict] = []

        for tc in last_msg.tool_calls:
            if tc["name"] == "search_blog":
                query = tc["args"].get("query", "")
                try:
                    blog_service = BlogVectorSearchService(db)
                    blog_results = await blog_service.search(query, top_k=3)
                    knowledge = _format_blog_knowledge(blog_results)
                    content = "\n\n".join(knowledge) if knowledge else "未找到相关博客文章。"
                    retrieved_sources.extend(
                        [
                            {
                                "post_id": r.post_id,
                                "title": r.title,
                                "similarity_score": r.similarity_score,
                            }
                            for r in blog_results
                        ]
                    )
                except Exception:
                    logger.exception("博客向量检索失败")
                    content = "博客检索服务暂时不可用。"
                tool_results.append(ToolMessage(content=content, tool_call_id=tc["id"]))
            elif tc["name"] == "search_web":
                original_query = tc["args"].get("query", "")
                try:
                    # 1. 拆分 query
                    sub_queries = await _split_search_queries(original_query, llm_small)
                    # 2. 并行搜索
                    api_key = settings.IQS_API_KEY
                    tasks = [_iqs_search_single(q, api_key) for q in sub_queries]
                    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
                    # 3. 合并、去重、排序
                    seen_links: set[str] = set()
                    merged: list[dict] = []
                    for items in raw_results:
                        if isinstance(items, Exception):
                            logger.warning("某条子查询搜索失败: %s", items)
                            continue
                        for item in items:
                            link = item.get("link")
                            if link and link not in seen_links:
                                seen_links.add(link)
                                merged.append(item)
                    merged.sort(key=lambda x: x.get("rerankScore", 0), reverse=True)
                    # 4. 格式化
                    content = _format_web_search_results(merged)
                except Exception:
                    logger.exception("联网搜索执行失败")
                    content = "联网搜索服务暂时不可用。"
                tool_results.append(ToolMessage(content=content, tool_call_id=tc["id"]))
            else:
                tool_results.append(
                    ToolMessage(
                        content=f"未知工具: {tc['name']}",
                        tool_call_id=tc["id"],
                    )
                )

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
        llm_small: 小模型（用于标题生成）
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
    builder.add_node("tools", _build_tools_node(llm_small))
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
