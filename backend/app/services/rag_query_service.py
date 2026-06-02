"""RAG Query 改写服务。

使用 small model 将用户原始查询改写为多条角度不同的精炼查询，
用于多查询并行检索，提升向量检索的召回率和精确率。
"""

import logging

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings
from app.infrastructure.llm_client import create_llm_small_client
from app.prompts.rag_prompts import render_blog_query_expansion_prompt

logger = logging.getLogger(__name__)


class RAGQueryService:
    """RAG 查询改写服务。

    负责将用户口语化/模糊的原始查询，改写为多条专业、精炼的检索查询。
    所有方法均为异步，内部异常降级处理，确保主流程不中断。
    """

    async def expand_queries(
        self, query: str, num_queries: int | None = None
    ) -> list[str]:
        """将用户查询改写为多条检索查询。

        流程：
        1. 调用 small model 生成多角度改写
        2. 解析输出为列表（按行分割，过滤空行）
        3. 若改写失败/解析失败，降级返回 [原query]

        Args:
            query: 用户原始查询
            num_queries: 期望生成的查询数量，默认读取配置

        Returns:
            list[str]: 改写后的查询列表（始终非空）
        """
        if not query or not query.strip():
            return []

        if not settings.RAG_QUERY_EXPANSION_ENABLED:
            return [query.strip()]

        effective_num = num_queries if num_queries is not None else settings.RAG_QUERY_EXPANSION_COUNT

        system_prompt, user_prompt = render_blog_query_expansion_prompt(
            query.strip(), num_queries=effective_num
        )

        try:
            client = create_llm_small_client(
                timeout=settings.RAG_QUERY_EXPANSION_TIMEOUT
            )
            response = await client.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
            raw_text = str(response.content).strip()
            expanded = self._parse_expansion_output(raw_text, effective_num)

            # 确保原 query 也在列表中（作为保底），但总数不超过 effective_num
            original = query.strip()
            if original not in expanded:
                expanded.insert(0, original)
            expanded = expanded[:effective_num]

            logger.info(
                "Query 改写成功: 原query='%s' -> %d 条改写", original, len(expanded)
            )
            return expanded
        except Exception:
            logger.warning("Query 改写失败，降级为单查询", exc_info=True)
            return [query.strip()]

    @staticmethod
    def _parse_expansion_output(raw_text: str, expected_count: int) -> list[str]:
        """解析 LLM 返回的改写文本为查询列表。

        解析规则：
        - 按行分割
        - 去除空行、编号前缀（如 "1."、"-"）、引号
        - 过滤过短（<2字）的查询
        - 去重（保持顺序）
        - 若结果不足 expected_count，用已有结果填充（允许重复但保留顺序）
        - 若结果为空，返回空列表（外层会降级为原query）

        Args:
            raw_text: LLM 原始输出
            expected_count: 期望的查询数量

        Returns:
            list[str]: 解析后的查询列表
        """
        lines = raw_text.splitlines()
        cleaned: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 去除常见编号前缀："1.", "1、", "-", "*"
            for prefix in ("-", "*", "•"):
                if line.startswith(prefix):
                    line = line[1:].strip()
                    break
            # 去除数字编号："1. " "1、" "1)"
            import re
            line = re.sub(r"^\d+[\.、\)）]\s*", "", line)
            # 去除引号
            line = line.strip("\"'\"'「」『』")
            if len(line) >= 2:
                cleaned.append(line)

        # 去重（保持顺序）
        seen: set[str] = set()
        unique: list[str] = []
        for q in cleaned:
            if q not in seen:
                seen.add(q)
                unique.append(q)

        # 若数量不足，用最后一个填充；若为空则返回空列表（外层降级）
        if not unique:
            return []
        while len(unique) < expected_count:
            unique.append(unique[-1])

        return unique[:expected_count]
