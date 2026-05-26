# LangChain Tool 节点定义（供 LLM Tool Calling 使用）
from app.graphs.nodes.toolnodes.blog_search import search_blog
from app.graphs.nodes.toolnodes.openapi_codegen import generate_openapi_call_example
from app.graphs.nodes.toolnodes.openapi_search import search_openapi_docs
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

registry.register(
    ToolMetadata(
        name=search_openapi_docs.name,
        tool=search_openapi_docs,
        risk=ToolRisk.READONLY,
        scope=ToolScope.ADMIN,
        concurrency_safe=True,
        category="search",
    )
)

registry.register(
    ToolMetadata(
        name=generate_openapi_call_example.name,
        tool=generate_openapi_call_example,
        risk=ToolRisk.READONLY,
        scope=ToolScope.ADMIN,
        concurrency_safe=True,
        category="codegen",
    )
)

__all__ = [
    "search_blog",
    "search_web",
    "search_openapi_docs",
    "generate_openapi_call_example",
    "registry",
]
