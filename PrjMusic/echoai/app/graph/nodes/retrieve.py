"""
RAG 检索节点。
基于 echovector 向量知识库，对 user_input 做 Embedding 相似度搜索。
"""
from app.graph.state import AgentState
from app.services.vector_store import VectorStoreError, vector_store


async def retrieve_node(state: AgentState) -> dict:
    """
    RAG 检索节点。
    对当前用户输入做 Embedding，查询 kb_documents 获取相关知识片段。

    结果写入 state["retrieved_docs"]，供后续生成节点使用。
    """
    user_input = state.get("user_input", "").strip()
    if not user_input:
        return {"retrieved_docs": []}

    try:
        docs = await vector_store.similarity_search(query=user_input, top_k=5)
    except VectorStoreError as e:
        # 检索失败不阻断主流程，返回空结果
        return {"retrieved_docs": []}
    except Exception:
        return {"retrieved_docs": []}

    retrieved = [
        {
            "source": "kb",
            "doc_id": d["doc_id"],
            "title": d.get("title"),
            "content": d["content"],
            "similarity": d["similarity"],
        }
        for d in docs
    ]
    return {"retrieved_docs": retrieved}
