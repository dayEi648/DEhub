# 集中导入所有模型，确保 SQLAlchemy mapper 正确注册
from app.models.ai_conversation import AIConversation
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.models.blog_post_embedding import BlogPostEmbedding
from app.models.user_memory_embedding import UserMemoryEmbedding
from app.models.comment import Comment
from app.models.conversation_message import ConversationMessage
from app.models.forum_post import ForumPost
from app.models.forum_reply import ForumReply
from app.models.forum_zone import ForumZone
from app.models.user import User
from app.models.user_comment_like import UserCommentLike
from app.models.user_blog_post_favorite import UserBlogPostFavorite
from app.models.user_zone_follow import UserZoneFollow
from app.models.user_post_favorite import UserPostFavorite

__all__ = [
    "AIConversation",
    "BlogCategory",
    "BlogPost",
    "BlogPostEmbedding",
    "Comment",
    "ConversationMessage",
    "ForumPost",
    "ForumReply",
    "ForumZone",
    "User",
    "UserCommentLike",
    "UserBlogPostFavorite",
    "UserZoneFollow",
    "UserPostFavorite",
]
