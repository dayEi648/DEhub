# LangChain Tool 节点定义（供 LLM Tool Calling 使用）
from app.graphs.nodes.toolnodes.blog_search import search_blog
from app.graphs.nodes.toolnodes.web_search import search_web

__all__ = ["search_blog", "search_web"]
