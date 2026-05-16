import logging
import threading

from app.db.session import SessionLocal
from app.crud import user_memory_embedding as mem_crud
from app.infrastructure.embedding_client import get_embedding_client
from app.infrastructure.llm_client import get_llm_client
from app.prompts.chat_prompts import get_chat_system_prompt
from app.graphs.nodes.toolnodes import search_blog, search_web
from app.graphs.states.chat_state import ChatState


def retrieve_memory_node(state: ChatState) -> dict:
    """
    检索用户记忆节点。

    根据当前用户输入的 query，从向量库中检索相似度 > 0.6（余弦距离 < 0.4）
    且创建时间在 1 年以内的最多 3 条用户画像记录。

    Args:
        state: 对话状态，需包含 user_id 和 messages

    Returns:
        dict: {"retrieved_memories": ["记忆文本1", "记忆文本2", ...]}
        即使没有结果也返回空列表，确保覆盖 checkpoint 中的旧值。
    """
    user_id = state.get("user_id", 0)
    if user_id <= 0:
        return {"retrieved_memories": []}

    messages = state.get("messages", [])
    if not messages:
        return {"retrieved_memories": []}

    # 取最后一条消息的内容作为 query（即当前用户输入）
    last_msg = messages[-1]
    query_text = last_msg.content
    if isinstance(query_text, list):
        # LangChain Message content 可能为 list，提取文本部分
        query_text = " ".join(str(x) for x in query_text if isinstance(x, str))
    if not query_text or not str(query_text).strip():
        return {"retrieved_memories": []}

    # 向量化 query
    try:
        embedding = get_embedding_client().embed_query(str(query_text).strip())
    except Exception:
        logging.getLogger(__name__).exception("用户记忆嵌入查询失败")
        return {"retrieved_memories": []}

    # 检索相似记忆（相似度 > 0.6 即距离 < 0.4）
    db = SessionLocal()
    try:
        results = mem_crud.search_user_memories(
            db=db,
            user_id=user_id,
            query_embedding=embedding,
            top_k=3,
            max_distance=0.4,
        )
        memories = [record.content_text for record, _distance in results]
        return {"retrieved_memories": memories}
    except Exception:
        logging.getLogger(__name__).exception("用户记忆向量检索失败")
        return {"retrieved_memories": []}
    finally:
        db.close()


_llm_with_tools = None
_llm_lock = threading.Lock()


def _get_llm_with_tools():
    """获取已绑定 tools 的 LLM 实例（全局单例缓存，线程安全）。"""
    global _llm_with_tools
    if _llm_with_tools is not None:
        return _llm_with_tools
    with _llm_lock:
        if _llm_with_tools is not None:
            return _llm_with_tools
        _llm_with_tools = get_llm_client().bind_tools([search_blog, search_web])
        return _llm_with_tools


def agent_node(state: ChatState) -> dict:
    """
    Agent 节点（带 Tool-Calling 的对话节点）。

    根据 state 中是否包含检索到的记忆，动态选择 prompt 模板，
    并调用绑定了 tools 的 LLM。LLM 可自主决定是否调用工具。

    Args:
        state: 对话状态

    Returns:
        dict: {"messages": [AIMessage]}（可能包含 tool_calls）
    """
    memories = state.get("retrieved_memories", [])
    prompt = get_chat_system_prompt(memories)

    messages = state.get("messages")
    if not messages:
        return {"messages": []}

    llm = _get_llm_with_tools()
    chain = prompt | llm
    response = chain.invoke({"messages": messages})
    return {"messages": [response]}
