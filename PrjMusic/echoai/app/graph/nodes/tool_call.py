"""
工具调用节点。
根据意图执行联网搜索、音乐操作等工具。
"""
import re

from app.graph.state import AgentState
from app.graph.tools.music_tools import (
    MusicToolError,
    add_to_playlist,
    get_music_by_id,
    get_user_playlists,
    play_music,
    search_music,
)
from app.graph.tools.search_tools import WebSearchError, web_search
from app.services.spring_client import AuthError


async def tool_call_node(state: AgentState) -> dict:
    """
    工具调用节点。
    根据 intent 分发到具体工具执行。
    结果统一写入 state["tool_results"]。
    """
    intent = state.get("intent", "")
    user_input = state.get("user_input", "").strip()
    user_id = state["user_id"]
    jwt_token = state.get("jwt_token", "")

    if intent == "web_search":
        return await _do_web_search(user_input)

    if intent == "music_action":
        return await _do_music_action(user_input, user_id, jwt_token)

    return {"tool_results": []}


async def _do_web_search(user_input: str) -> dict:
    """执行联网搜索。"""
    # 简单提取搜索关键词：去掉常见前缀
    query = re.sub(r"^(搜索|查一下|查询|帮我搜|请问).*[?？]?", "", user_input).strip()
    if not query:
        query = user_input

    try:
        results = await web_search(query, num_results=5)
    except WebSearchError as e:
        return {
            "tool_results": [
                {"tool": "web_search", "status": "error", "message": str(e)}
            ]
        }

    return {
        "tool_results": [
            {
                "tool": "web_search",
                "status": "ok",
                "query": query,
                "results": results,
            }
        ]
    }


async def _do_music_action(
    user_input: str, user_id: int, jwt_token: str
) -> dict:
    """
    执行音乐操作。
    基于关键词匹配判断具体动作：
    - "播放" → play_music
    - "加入/收藏/添加" → add_to_playlist
    - 其他 → search_music
    """
    input_lower = user_input.lower()

    # 1. 播放
    if "播放" in input_lower or "听" in input_lower:
        # 尝试提取音乐 ID（数字）或音乐名
        music_id = _extract_music_id(user_input)
        if music_id:
            result = await play_music(music_id)
            if result:
                return {
                    "tool_results": [
                        {"tool": "play_music", "status": "ok", "data": result}
                    ]
                }
            return {
                "tool_results": [
                    {"tool": "play_music", "status": "not_found", "message": "音乐不存在"}
                ]
            }

        # 无明确 ID，尝试搜索后推荐第一首
        keyword = _extract_keyword(user_input, ["播放", "听", "一下", "这首", "首歌"])
        results = await search_music(keyword, limit=1)
        if results:
            music = results[0]
            return {
                "tool_results": [
                    {
                        "tool": "play_music",
                        "status": "ok",
                        "data": {
                            "action": "play",
                            "music_id": music["id"],
                            "music_name": music["name"],
                            "author_ids": music.get("author_ids", []),
                            "cover_url": music["cover_url"],
                            "file_url": music["file_url"],
                            "vip": music["vip"],
                        },
                    }
                ]
            }
        return {
            "tool_results": [
                {"tool": "play_music", "status": "not_found", "message": f"未找到匹配的音乐: {keyword}"}
            ]
        }

    # 2. 加入歌单 / 收藏
    if any(k in input_lower for k in ["加入", "收藏", "添加", "放进"]):
        return await _handle_add_to_playlist(user_input, user_id, jwt_token)

    # 3. 默认：搜索音乐
    keyword = _extract_keyword(user_input, ["搜索", "找", "推荐", "有没有", "首歌"])
    results = await search_music(keyword, limit=10)
    return {
        "tool_results": [
            {
                "tool": "search_music",
                "status": "ok",
                "keyword": keyword,
                "results": results,
            }
        ]
    }


async def _handle_add_to_playlist(
    user_input: str, user_id: int, jwt_token: str
) -> dict:
    """处理收藏/加入歌单请求。"""
    # 获取用户歌单列表
    playlists = await get_user_playlists(user_id)
    if not playlists:
        return {
            "tool_results": [
                {"tool": "add_to_playlist", "status": "no_playlist", "message": "您还没有创建歌单"}
            ]
        }

    # 尝试提取音乐 ID
    music_id = _extract_music_id(user_input)
    if not music_id:
        # 尝试按音乐名匹配（简化处理：直接返回歌单列表让前端选择）
        return {
            "tool_results": [
                {
                    "tool": "add_to_playlist",
                    "status": "need_select",
                    "message": "请指定要收藏的歌曲",
                    "playlists": playlists,
                }
            ]
        }

    # 确定目标歌单：用户指定了歌单名则匹配，否则默认使用 "喜欢" 歌单
    target_playlist = None
    for pl in playlists:
        if pl["is_like"]:
            target_playlist = pl
            break

    # 如果用户输入中提到了歌单名，尝试匹配（第一个匹配胜出）
    for pl in playlists:
        if pl["name"] in user_input:
            target_playlist = pl
            break

    if not target_playlist:
        target_playlist = playlists[0]  # fallback 到第一个歌单

    # 执行添加
    try:
        await add_to_playlist(target_playlist["id"], music_id, user_id, jwt_token)
    except AuthError as e:
        return {
            "tool_results": [
                {"tool": "add_to_playlist", "status": "auth_error", "message": str(e)}
            ]
        }
    except MusicToolError as e:
        return {
            "tool_results": [
                {"tool": "add_to_playlist", "status": "error", "message": str(e)}
            ]
        }

    music = await get_music_by_id(music_id)
    return {
        "tool_results": [
            {
                "tool": "add_to_playlist",
                "status": "ok",
                "playlist_id": target_playlist["id"],
                "playlist_name": target_playlist["name"],
                "music_id": music_id,
                "music_name": music["name"] if music else "未知",
            }
        ]
    }


def _extract_music_id(text: str) -> int | None:
    """从文本中提取音乐 ID（连续数字）。"""
    # 优先匹配 "ID 123"、"编号123" 等模式
    patterns = [
        r"(?:id|ID|编号)\s*[:=]?\s*(\d+)",
        r"音乐\s*(\d+)",
        r"歌曲\s*(\d+)",
        r"#\s*(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return int(m.group(1))

    # fallback：提取最后一个连续数字（避免匹配到句首编号等非 ID 数字）
    nums = re.findall(r"\d+", text)
    if nums:
        # 如果只有一个数字且文本较短，可能是 ID
        if len(nums) == 1 and len(text) < 30:
            return int(nums[0])
    return None


def _extract_keyword(text: str, stopwords: list[str]) -> str:
    """从文本中提取搜索关键词（去掉停用词）。"""
    result = text
    for sw in stopwords:
        result = result.replace(sw, "")
    # 按词级别去除尾部停用词，避免 strip() 按字符集误处理
    result = re.sub(r"^(的|一下|这首|首歌|那首|给我|帮我|我想|我要|的\s*)", "", result)
    result = re.sub(r"(的|一下|这首|首歌|那首|给我|帮我|我想|我要|的\s*)$", "", result)
    return result.strip() or text
