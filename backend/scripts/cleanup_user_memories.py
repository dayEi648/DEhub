"""
用户长期记忆过期清理脚本。

用法：
    cd backend && python -m scripts.cleanup_user_memories

功能：
    删除 user_memory_embeddings 表中创建时间超过 180 天（半年）的记忆记录。
    建议通过 cron 每周执行一次。
"""

import asyncio
import logging
import sys

sys.path.insert(0, ".")

from app.db.session import SessionLocal
from app.crud.user_memory_embedding import cleanup_expired_memories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    db = SessionLocal()
    try:
        logger.info("开始清理过期用户记忆...")
        deleted_count = await asyncio.to_thread(cleanup_expired_memories, db)
        logger.info("已清理 %s 条过期记忆", deleted_count)
    finally:
        await asyncio.to_thread(db.close)


if __name__ == "__main__":
    asyncio.run(main())
