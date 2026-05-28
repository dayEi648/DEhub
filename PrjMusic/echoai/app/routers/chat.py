"""
AI 对话路由。
提供非流式和 SSE 流式对话接口，接入 LangGraph 意图路由与记忆系统。
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import SystemMessage

from app.dependencies import CurrentUser, get_current_user
from app.graph.graph_builder import graph
from app.models.schemas import ChatRequest
from app.services.llm_service import LLMError, llm_service
from app.services.memory_service import memory_service
from app.utils.redis_pool import redis_client

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = """你是"回声记忆"（EchoMemory）平台的 AI 音乐助手。
你可以和用户聊天、推荐音乐、回答音乐相关问题。
请用友好、自然的语气回复，适当使用 Markdown 格式。

重要约束：
1. 推荐音乐、专辑或歌单时，不要提供音频文件的直链（如 .mp3 链接）。
2. 如果用户想试听或查看详情，请引导用户点击页面上的音乐卡片。
3. 如需在回复中提供链接，必须使用 Markdown 链接格式，如：[歌曲名](/music/123)、[专辑名](/album/456)、[歌单名](/playlist/789)。
   禁止直接输出 '/music/123' 这样的原始路径文本。
4. 禁止在回复中暴露任何系统内部实现细节，包括但不限于"标签"、"意图"、"检索结果"、"工具结果"、"情绪分析"等术语。
5. 基于用户听歌偏好推荐时，应使用"根据你的听歌习惯"、"为你挑选了"等自然表达，绝不要提及具体的标签名称。"""


async def _get_or_create_session(
    user_id: int, session_id: str | None, first_message: str
) -> str:
    """获取或创建会话。"""
    if session_id:
        sessions = await memory_service.get_sessions(user_id)
        if not any(str(s["session_id"]) == session_id for s in sessions):
            raise HTTPException(
                status_code=404, detail="会话不存在或无权访问"
            )
        return session_id

    new_session_id = await memory_service.create_session(user_id)
    import asyncio

    asyncio.create_task(
        memory_service.auto_title(new_session_id, first_message)
    )
    return new_session_id


async def _acquire_lock(session_id: str) -> bool:
    """尝试获取 Redis 分布式锁（60秒自动释放）。"""
    lock_key = f"session_lock:{session_id}"
    acquired = await redis_client.client.set(lock_key, "1", nx=True, ex=60)
    return acquired is not None


async def _release_lock(session_id: str):
    """释放 Redis 分布式锁。"""
    lock_key = f"session_lock:{session_id}"
    await redis_client.client.delete(lock_key)


def _strip_internal_fields(obj):
    """递归删除对象中的内部字段（file_url、tags 等），避免 LLM 看到内部实现后误用。"""
    if isinstance(obj, dict):
        return {
            k: _strip_internal_fields(v)
            for k, v in obj.items()
            if k not in ("file_url", "tags")
        }
    elif isinstance(obj, list):
        return [_strip_internal_fields(i) for i in obj]
    return obj


def _build_tool_context(state: dict) -> str:
    """基于 Graph 最终状态构造工具/检索上下文文本（已脱敏内部字段）。"""
    parts = []

    docs = state.get("retrieved_docs", [])
    if docs:
        docs_text = "\n".join(
            [f"- {d.get('content', '')[:200]}" for d in docs]
        )
        parts.append(f"参考信息：\n{docs_text}")

    tools = state.get("tool_results", [])
    if tools:
        tools_text = "\n".join(
            [
                f"- {json.dumps(_strip_internal_fields(t), ensure_ascii=False)[:300]}"
                for t in tools
            ]
        )
        parts.append(f"查询结果：\n{tools_text}")

    return "\n\n".join(parts) if parts else ""


def _check_auth_error(tool_results: list[dict]) -> str | None:
    """检查工具结果中是否包含鉴权错误。"""
    for tr in tool_results:
        if tr.get("status") == "auth_error":
            return tr.get("message", "登录已过期，请重新登录后重试")
    return None


async def _run_graph(
    session_id: str,
    user_id: int,
    user_message: str,
    jwt_token: str,
) -> dict:
    """
    执行 LangGraph（entry → understand → route → action），返回最终状态。
    不涉及 LLM 生成，生成由外层统一处理。
    """
    history = await memory_service.load_messages(
        session_id, user_id, limit=20
    )

    initial_state = {
        "user_id": user_id,
        "session_id": session_id,
        "jwt_token": jwt_token,
        "messages": [SystemMessage(content=SYSTEM_PROMPT)] + history,
        "user_input": user_message,
        "intent": "",
        "emotion_tags": [],
        "interest_tags": [],
        "retrieved_docs": [],
        "tool_results": [],
        "response": "",
        "streaming": False,
    }

    return await graph.ainvoke(initial_state)


async def _build_llm_messages(final_state: dict) -> list:
    """基于 Graph 最终状态构造 LLM 消息列表，注入长期记忆摘要。"""
    messages = list(final_state["messages"])

    # 注入长期记忆摘要（若有）
    session_id = final_state.get("session_id")
    if session_id:
        summary = await memory_service.get_context_summary(session_id)
        if summary:
            messages.append(
                SystemMessage(content=f"【历史会话摘要】\n{summary}")
            )

    tool_context = _build_tool_context(final_state)
    if tool_context:
        messages.append(
            SystemMessage(content=f"【上下文信息】\n{tool_context}")
        )
    return messages


@router.post("")
async def chat(
    request: ChatRequest, user: CurrentUser = Depends(get_current_user)
):
    """
    非流式对话接口。
    完整执行 Graph + LLM 生成，返回最终回复。
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    msg = request.message.strip()
    session_id = await _get_or_create_session(
        user.user_id, request.session_id, msg
    )

    # 并发锁
    if not await _acquire_lock(session_id):
        return {
            "code": 429,
            "msg": "当前会话正在处理中，请稍后再试",
            "data": {"type": "session_lock"},
        }

    try:
        # 1. 执行 Graph（意图分析 + 工具/检索）
        final_state = await _run_graph(
            session_id, user.user_id, msg, user.token
        )

        # 检查工具鉴权错误
        auth_err = _check_auth_error(final_state.get("tool_results", []))
        if auth_err:
            await _release_lock(session_id)
            return {
                "code": 401,
                "msg": auth_err,
                "data": {"auth_error": True},
            }

        # 2. 先保存用户消息（避免 LLM 异常导致消息丢失）
        await memory_service.save_message(
            session_id, user.user_id, "user", msg
        )

        # 3. 调用 LLM 生成回复
        messages = await _build_llm_messages(final_state)
        try:
            reply = await llm_service.achat(messages)
        except LLMError as e:
            await memory_service.save_message(
                session_id, user.user_id, "assistant", f"[生成失败] {e}"
            )
            return {"code": 500, "msg": str(e), "data": None}

        # 4. 保存 AI 回复
        await memory_service.save_message(
            session_id, user.user_id, "assistant", reply
        )
        await memory_service.generate_summary(session_id)

        return {
            "code": 200,
            "msg": "ok",
            "data": {
                "reply": reply,
                "session_id": session_id,
                "intent": final_state.get("intent", "chat"),
                "tool_results": final_state.get("tool_results", []),
            },
        }
    finally:
        await _release_lock(session_id)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest, user: CurrentUser = Depends(get_current_user)
):
    """
    SSE 流式对话接口。
    执行 Graph 后，通过 LLM 流式生成回复。
    锁在流式生成器结束时释放。
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    msg = request.message.strip()
    session_id = await _get_or_create_session(
        user.user_id, request.session_id, msg
    )

    if not await _acquire_lock(session_id):
        return {
            "code": 429,
            "msg": "当前会话正在处理中，请稍后再试",
            "data": {"type": "session_lock"},
        }

    try:
        # 1. 执行 Graph
        final_state = await _run_graph(
            session_id, user.user_id, msg, user.token
        )

        # 检查工具鉴权错误
        auth_err = _check_auth_error(final_state.get("tool_results", []))
        if auth_err:
            await _release_lock(session_id)
            return {
                "code": 401,
                "msg": auth_err,
                "data": {"auth_error": True},
            }

        # 先保存用户消息（避免流式过程中异常导致丢失）
        await memory_service.save_message(
            session_id, user.user_id, "user", msg
        )

        messages = await _build_llm_messages(final_state)

        # 2. 流式生成
        async def event_generator():
            full_reply = []

            # 先发送工具结果事件（如果有）
            tool_results = final_state.get("tool_results", [])
            if tool_results:
                yield f"event: tool_end\ndata: {json.dumps({'tool_results': tool_results}, ensure_ascii=False)}\n\n"

            try:
                async for chunk in llm_service.astream(messages):
                    full_reply.append(chunk)
                    yield f"event: message_delta\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                # 保存完整 AI 回复
                complete_reply = "".join(full_reply)
                await memory_service.save_message(
                    session_id, user.user_id, "assistant", complete_reply
                )
                await memory_service.generate_summary(session_id)

                yield f"event: done\ndata: {json.dumps({'session_id': session_id, 'intent': final_state.get('intent', 'chat')}, ensure_ascii=False)}\n\n"
            except LLMError as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            finally:
                # 流式结束时释放锁（客户端断开也会触发 finally）
                await _release_lock(session_id)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )
    except Exception:
        # Graph 执行阶段异常，直接释放锁后抛出
        await _release_lock(session_id)
        raise
