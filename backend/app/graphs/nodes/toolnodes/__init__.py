# LangChain Tool 节点定义（供 LLM Tool Calling 使用）
from app.graphs.nodes.toolnodes.blog_search import search_blog
from app.graphs.nodes.toolnodes.openapi_codegen import generate_openapi_call_example
from app.graphs.nodes.toolnodes.openapi_search import search_openapi_docs
from app.graphs.nodes.toolnodes.user_actions import (
    favorite_blog_post,
    follow_forum_zone,
    get_blog_post_detail,
    list_forum_zones,
    list_my_blog_favorites,
    list_my_zone_follows,
    unfavorite_blog_post,
    unfollow_forum_zone,
)
from app.graphs.nodes.toolnodes.web_search import search_web
from app.graphs.tool_registry import ToolMetadata, ToolRegistry, ToolRisk, ToolScope

# ------------------------------------------------------------------
# 全局工具注册中心（模块导入时完成注册）
# ------------------------------------------------------------------
registry = ToolRegistry()

# ---------- 搜索类（已有）----------

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

# ---------- 用户操作类（新增）----------

registry.register(
    ToolMetadata(
        name=favorite_blog_post.name,
        tool=favorite_blog_post,
        risk=ToolRisk.IDEMPOTENT,
        scope=ToolScope.AUTHENTICATED,
        concurrency_safe=False,
        category="user_action",
    )
)

registry.register(
    ToolMetadata(
        name=unfavorite_blog_post.name,
        tool=unfavorite_blog_post,
        risk=ToolRisk.IDEMPOTENT,
        scope=ToolScope.AUTHENTICATED,
        concurrency_safe=False,
        category="user_action",
    )
)

registry.register(
    ToolMetadata(
        name=list_forum_zones.name,
        tool=list_forum_zones,
        risk=ToolRisk.READONLY,
        scope=ToolScope.PUBLIC,
        concurrency_safe=True,
        category="info",
    )
)

registry.register(
    ToolMetadata(
        name=follow_forum_zone.name,
        tool=follow_forum_zone,
        risk=ToolRisk.IDEMPOTENT,
        scope=ToolScope.AUTHENTICATED,
        concurrency_safe=False,
        category="user_action",
    )
)

registry.register(
    ToolMetadata(
        name=unfollow_forum_zone.name,
        tool=unfollow_forum_zone,
        risk=ToolRisk.IDEMPOTENT,
        scope=ToolScope.AUTHENTICATED,
        concurrency_safe=False,
        category="user_action",
    )
)

registry.register(
    ToolMetadata(
        name=get_blog_post_detail.name,
        tool=get_blog_post_detail,
        risk=ToolRisk.READONLY,
        scope=ToolScope.PUBLIC,
        concurrency_safe=True,
        category="info",
    )
)

registry.register(
    ToolMetadata(
        name=list_my_blog_favorites.name,
        tool=list_my_blog_favorites,
        risk=ToolRisk.READONLY,
        scope=ToolScope.AUTHENTICATED,
        concurrency_safe=True,
        category="user_action",
    )
)

registry.register(
    ToolMetadata(
        name=list_my_zone_follows.name,
        tool=list_my_zone_follows,
        risk=ToolRisk.READONLY,
        scope=ToolScope.AUTHENTICATED,
        concurrency_safe=True,
        category="user_action",
    )
)

__all__ = [
    "search_blog",
    "search_web",
    "search_openapi_docs",
    "generate_openapi_call_example",
    "favorite_blog_post",
    "unfavorite_blog_post",
    "list_forum_zones",
    "follow_forum_zone",
    "unfollow_forum_zone",
    "get_blog_post_detail",
    "list_my_blog_favorites",
    "list_my_zone_follows",
    "registry",
]
