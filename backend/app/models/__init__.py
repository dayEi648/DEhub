# 集中导入所有模型，确保 SQLAlchemy mapper 正确注册
from app.models.agent_evaluation import AgentEvaluation
from app.models.agent_span import AgentSpan
from app.models.agent_trace import AgentTrace
from app.models.ai_conversation import AIConversation
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.models.blog_post_embedding import BlogPostEmbedding
from app.models.content_moderation_record import ContentModerationRecord
from app.models.openapi_document import OpenAPIDocument
from app.models.openapi_endpoint_embedding import OpenAPIEndpointEmbedding
from app.models.user_profile import UserProfile
from app.models.comment import Comment
from app.models.conversation_message import ConversationMessage
from app.models.forum_post import ForumPost
from app.models.forum_reply import ForumReply
from app.models.forum_zone import ForumZone
from app.models.user import User
from app.models.user_comment_like import UserCommentLike
from app.models.user_forum_reply_like import UserForumReplyLike
from app.models.user_blog_post_favorite import UserBlogPostFavorite
from app.models.system_log import SystemLog
from app.models.user_zone_follow import UserZoneFollow
from app.models.user_post_favorite import UserPostFavorite
from app.models.oss_cleanup_task import OssCleanupTask

__all__ = [
    "AgentEvaluation",
    "AgentSpan",
    "AgentTrace",
    "AIConversation",
    "BlogCategory",
    "BlogPost",
    "BlogPostEmbedding",
    "ContentModerationRecord",
    "OpenAPIDocument",
    "OpenAPIEndpointEmbedding",
    "UserProfile",
    "Comment",
    "ConversationMessage",
    "ForumPost",
    "ForumReply",
    "ForumZone",
    "User",
    "UserCommentLike",
    "UserForumReplyLike",
    "UserBlogPostFavorite",
    "SystemLog",
    "UserZoneFollow",
    "UserPostFavorite",
    "OssCleanupTask",
]
