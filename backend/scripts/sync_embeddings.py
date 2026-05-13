"""
博客文章向量批量同步脚本。

用法：
    cd backend && python -m scripts.sync_embeddings

功能：
    遍历所有已发布且未删除的博客文章，逐一调用 Embedding API 生成/更新向量。
    适用于：
    - 初次部署时初始化向量库
    - 更换 embedding model 后重刷全量向量
    - 修复向量库与业务库不一致的兜底手段
"""

import asyncio
import logging
import sys

sys.path.insert(0, ".")

from app.infrastructure.embedding_client import init_embedding_client, close_embedding_client
from app.services.vector_sync_service import sync_all_published_posts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("初始化 Embedding Client...")
    await init_embedding_client()
    try:
        logger.info("开始批量同步所有已发布文章的向量...")
        await sync_all_published_posts()
        logger.info("批量同步完成")
    finally:
        await close_embedding_client()


if __name__ == "__main__":
    asyncio.run(main())
