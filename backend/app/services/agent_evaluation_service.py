"""Agent 输出质量评估服务。

使用 LLM-as-Judge 对 Agent Trace 进行多维度自动评估。
评估完全异步，不影响主响应延迟。
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import SystemMessage

from app.core.config import settings
from app.crud import agent_evaluation as eval_crud
from app.crud import agent_span as span_crud
from app.crud import agent_trace as trace_crud
from app.db.session import SessionLocal
from app.infrastructure.llm_client import get_llm_small_client
from app.prompts.eval_prompts import (
    render_coherence_eval_prompt,
    render_helpfulness_eval_prompt,
    render_relevance_eval_prompt,
)

logger = logging.getLogger(__name__)


class AgentEvaluationService:
    """Agent 质量评估服务。

    所有方法均为静态方法，内部自行管理 Session，便于后台任务调用。
    """

    @staticmethod
    def should_evaluate() -> bool:
        """根据配置判断是否需要执行评估。"""
        if not getattr(settings, "AI_CHAT_EVAL_ENABLED", True):
            return False
        rate = getattr(settings, "AI_CHAT_EVAL_SAMPLE_RATE", 1.0)
        if rate <= 0:
            return False
        if rate >= 1.0:
            return True
        return random.random() < rate

    @staticmethod
    async def evaluate_trace_async(trace_id: str) -> None:
        """对指定 trace 执行完整的多维度评估。

        步骤：
        1. 读取 trace 和 spans
        2. 执行 relevance + helpfulness + coherence 的 LLM 评估
        3. 计算 tool_accuracy 规则评估
        4. 批量写入 agent_evaluations
        """
        logger.info("开始评估 trace: %s", trace_id)

        try:
            with SessionLocal() as db:
                trace = trace_crud.get_agent_trace_by_trace_id(db, trace_id)
                if not trace:
                    logger.warning("评估时找不到 trace: %s", trace_id)
                    return

                # 跳过失败的 trace（通常没有有意义的输出可评估）
                if trace.status == "failed":
                    logger.debug("跳过失败 trace 的评估: %s", trace_id)
                    return

                spans = span_crud.list_agent_spans_by_trace(db, trace_id)
                spans_data = [
                    {
                        "span_type": s.span_type,
                        "span_name": s.span_name,
                        "status": s.status,
                        "input_data": s.input_data,
                        "output_data": s.output_data,
                        "error_info": s.error_info,
                        "token_usage": s.token_usage,
                    }
                    for s in spans
                ]

                evaluations: list[dict[str, Any]] = []
                model_name = settings.LLM_SMALL_MODEL or "unknown"

                # ---- LLM 评估维度 ----
                llm_dimensions = [
                    ("relevance", render_relevance_eval_prompt),
                    ("helpfulness", render_helpfulness_eval_prompt),
                    ("coherence", render_coherence_eval_prompt),
                ]

                for dimension, prompt_renderer in llm_dimensions:
                    try:
                        if dimension == "coherence":
                            prompt = prompt_renderer(output_message=trace.output_message)
                        else:
                            prompt = prompt_renderer(
                                input_message=trace.input_message,
                                output_message=trace.output_message,
                                tool_calls_count=trace.tool_calls_count or 0,
                                spans=spans_data,
                            )

                        score, reason = await AgentEvaluationService._call_llm_judge(
                            prompt, dimension
                        )

                        evaluations.append({
                            "trace_id": trace_id,
                            "conversation_id": trace.conversation_id,
                            "dimension": dimension,
                            "score": score,
                            "reason": reason,
                            "evaluator_model": model_name,
                        })
                        logger.debug(
                            "trace=%s dimension=%s score=%.2f", trace_id, dimension, score
                        )
                    except Exception:
                        logger.exception(
                            "LLM 评估失败: trace=%s dimension=%s", trace_id, dimension
                        )

                # ---- 规则评估：tool_accuracy ----
                try:
                    tool_accuracy = AgentEvaluationService._calculate_tool_accuracy(
                        spans_data
                    )
                    evaluations.append({
                        "trace_id": trace_id,
                        "conversation_id": trace.conversation_id,
                        "dimension": "tool_accuracy",
                        "score": tool_accuracy,
                        "reason": (
                            f"工具调用成功率: {tool_accuracy:.2f} "
                            f"(成功 {sum(1 for s in spans_data if s['span_type'] == 'tool' and s['status'] == 'completed')} / "
                            f"总计 {sum(1 for s in spans_data if s['span_type'] == 'tool')})"
                        ),
                        "evaluator_model": "rule",
                    })
                except Exception:
                    logger.exception("规则评估失败: trace=%s", trace_id)

                # ---- Phase 4: 自动标记异常 trace ----
                try:
                    should_flag = AgentEvaluationService._should_flag_trace(
                        trace, evaluations, spans_data
                    )
                    if should_flag:
                        trace_crud.update_agent_trace(db, trace_id, is_flagged=True)
                        logger.info("trace=%s 被自动标记为异常", trace_id)
                except Exception:
                    logger.exception("自动标记异常 trace 失败: trace=%s", trace_id)

                # ---- 批量写入 ----
                if evaluations:
                    try:
                        eval_crud.batch_create_agent_evaluations(db, evaluations)
                        logger.info(
                            "trace=%s 评估完成，写入 %d 条记录", trace_id, len(evaluations)
                        )
                    except Exception:
                        logger.exception("评估结果写入失败: trace=%s", trace_id)

        except Exception:
            logger.exception("评估任务异常: trace=%s", trace_id)

    @staticmethod
    async def _call_llm_judge(prompt: str, dimension: str) -> tuple[float, str]:
        """调用 small model 执行单次评估。

        Returns:
            (score, reason)
        """
        llm = get_llm_small_client()
        response = await llm.ainvoke([SystemMessage(content=prompt)])
        content = response.content.strip() if response.content else ""

        # 尝试提取 JSON
        score = 0.0
        reason = "解析失败"

        # 尝试从 markdown code block 中提取
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                cleaned = part.strip()
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                if cleaned.startswith("{"):
                    content = cleaned
                    break

        try:
            parsed = json.loads(content)
            raw_score = parsed.get("score")
            if isinstance(raw_score, (int, float)):
                score = max(0.0, min(1.0, float(raw_score)))
            reason = parsed.get("reason", "未提供理由")
            if not isinstance(reason, str):
                reason = str(reason)
            # 截断理由
            if len(reason) > 500:
                reason = reason[:500] + "..."
        except json.JSONDecodeError:
            logger.warning("评估 JSON 解析失败: dimension=%s content=%s", dimension, content[:200])
            # 尝试简单正则提取分数
            import re
            match = re.search(r"(\d+\.?\d*)", content)
            if match:
                try:
                    score = max(0.0, min(1.0, float(match.group(1))))
                    reason = content[:200]
                except ValueError:
                    pass

        return score, reason

    @staticmethod
    def _should_flag_trace(
        trace,
        evaluations: list[dict],
        spans: list[dict],
    ) -> bool:
        """判断 trace 是否应被标记为异常。

        规则：
        1. trace 状态为 failed
        2. 任一 LLM 评估维度得分 < 0.5
        3. 有工具调用且未全部成功（tool_accuracy < 1.0）
        """
        if trace.status == "failed":
            return True

        for ev in evaluations:
            if ev.get("dimension") in ("relevance", "helpfulness", "coherence"):
                if ev.get("score", 1.0) < 0.5:
                    return True

        tool_spans = [s for s in spans if s.get("span_type") == "tool"]
        if tool_spans:
            success = sum(1 for s in tool_spans if s.get("status") == "completed")
            if success < len(tool_spans):
                return True

        return False

    @staticmethod
    def _calculate_tool_accuracy(spans: list[dict]) -> float:
        """计算工具执行成功率（规则评估）。"""
        tool_spans = [s for s in spans if s.get("span_type") == "tool"]
        if not tool_spans:
            return 1.0  # 没有工具调用视为完美

        success = sum(1 for s in tool_spans if s.get("status") == "completed")
        return round(success / len(tool_spans), 2)
