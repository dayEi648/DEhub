# LangChain Tool 节点定义（供 LLM Tool Calling 使用）
from app.graphs.nodes.toolnodes.blog_search import search_blog
from app.graphs.nodes.toolnodes.web_search import search_web
from app.graphs.tool_registry import ToolMetadata, ToolRegistry, ToolRisk, ToolScope

# ------------------------------------------------------------------
# 全局工具注册中心（模块导入时完成注册）
# ------------------------------------------------------------------
registry = ToolRegistry()

registry.register(
    ToolMetadata(
        name=search_blog.name,
        tool=search_blog,
        risk=ToolRisk.READONLY,
        scope=ToolScope.PUBLIC,
        concurrency_safe=True,
        category="search",
    )
)

registry.register(
    ToolMetadata(
        name=search_web.name,
        tool=search_web,
        risk=ToolRisk.READONLY,
        scope=ToolScope.PUBLIC,
        concurrency_safe=True,
        category="search",
    )
)

__all__ = ["search_blog", "search_web", "registry"]
