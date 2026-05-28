"""
会话管理路由。
提供会话的 CRUD、历史消息查询、心跳续期和内存清理接口。
"""
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, CurrentUser
from app.services.memory_service import memory_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(user: CurrentUser = Depends(get_current_user)):
    """查询当前用户的会话列表（排除已删除）。"""
    sessions = await memory_service.get_sessions(user.user_id)
    return {"code": 200, "msg": "ok", "data": sessions}


@router.post("")
async def create_session(user: CurrentUser = Depends(get_current_user)):
    """创建新会话。"""
    session_id = await memory_service.create_session(user.user_id)
    return {"code": 200, "msg": "ok", "data": {"session_id": session_id}}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str, user: CurrentUser = Depends(get_current_user)
):
    """软删除指定会话。"""
    success = await memory_service.soft_delete_session(
        session_id, user.user_id
    )
    if not success:
        raise HTTPException(
            status_code=404, detail="会话不存在或无权删除"
        )
    return {"code": 200, "msg": "删除成功", "data": None}


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    page_num: int = 1,
    page_size: int = 20,
    user: CurrentUser = Depends(get_current_user),
):
    """分页读取会话历史消息（按时间倒序）。"""
    messages = await memory_service.get_session_messages(
        session_id, user.user_id, page_num, page_size
    )
    return {"code": 200, "msg": "ok", "data": messages}


@router.post("/{session_id}/heartbeat")
async def heartbeat(
    session_id: str, user: CurrentUser = Depends(get_current_user)
):
    """续期 Redis 中该会话消息的缓存 TTL。"""
    await memory_service.heartbeat(user.user_id, session_id)
    return {"code": 200, "msg": "ok", "data": None}


@router.delete("/{session_id}/memory")
async def clear_memory(
    session_id: str, user: CurrentUser = Depends(get_current_user)
):
    """清理 Redis 中该会话的缓存（不影响 PG 持久化数据）。"""
    await memory_service.clear_redis_memory(user.user_id, session_id)
    return {"code": 200, "msg": "ok", "data": None}
