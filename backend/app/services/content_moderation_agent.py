"""内容审核 Agent。

直接调用小模型进行审核判断，产出结构化结果。
通过 AgentMonitoringService 手动写入 trace/span，与现有监控体系打通。
不依赖 LangGraph 工作流（审核为单步判断，无多轮/工具调用需求）。
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.infrastructure.llm_client import create_llm_small_client
from app.prompts.content_moderation_prompts import render_moderation_prompt
from app.schemas.content_moderation import FlaggedSpan, ModerationAgentOutput
from app.services.agent_monitoring_service import AgentMonitoringService

logger = logging.getLogger(__name__)


class ContentModerationAgent:
    """内容审核 Agent。

    负责：
    1. 组装审核 prompt
    2. 调用小模型获取审核结论
    3. 解析并校验结构化输出
    4. 将调用过程记录到 agent_traces / agent_spans
    """

    def __init__(self) -> None:
        self.model_name = settings.CONTENT_MODERATION_MODEL or settings.LLM_SMALL_MODEL
        self.timeout = settings.CONTENT_MODERATION_TIMEOUT
        self.max_text_chars = settings.CONTENT_MODERATION_MAX_TEXT_CHARS

    async def moderate(
        self,
        content_snapshot: dict[str, str],
        target_type: str,
        user_id: int | None = None,
    ) -> tuple[ModerationAgentOutput | None, str | None]:
        """执行内容审核。

        Args:
            content_snapshot: 需要审核的字段快照。
            target_type: 内容类型标识。
            user_id: 触发审核的用户 ID（用于 trace）。

        Returns:
            ( ModerationAgentOutput, trace_id )
            - 若解析失败或模型调用异常，返回 (None, trace_id)
            - trace_id 始终返回，供上层关联审核记录
        """
        trace_id = f"cm-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc)
        system_prompt, user_prompt = render_moderation_prompt(content_snapshot, target_type)

        # 截断过长的 user_prompt
        if len(user_prompt) > self.max_text_chars:
            user_prompt = user_prompt[: self.max_text_chars] + "\n...[内容已截断]"

        raw_output = ""
        error_type: str | None = None
        error_message: str | None = None
        output_data: ModerationAgentOutput | None = None
        token_usage: dict = {}
        latency_ms: int | None = None

        try:
            client = create_llm_small_client(
                timeout=self.timeout,
                model=self.model_name,
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            llm_started = datetime.now(timezone.utc)
            response = await client.ainvoke(messages)
            llm_ended = datetime.now(timezone.utc)
            latency_ms = int((llm_ended - llm_started).total_seconds() * 1000)

            raw_output = str(response.content).strip()

            # 提取 token usage
            usage_meta = getattr(response, "usage_metadata", None) or {}
            resp_meta = getattr(response, "response_metadata", None) or {}
            token_usage_raw = resp_meta.get("token_usage") or {}
            token_usage = {
                "prompt_tokens": token_usage_raw.get("prompt_tokens")
                    or usage_meta.get("input_tokens", 0),
                "completion_tokens": token_usage_raw.get("completion_tokens")
                    or usage_meta.get("output_tokens", 0),
                "total_tokens": token_usage_raw.get("total_tokens")
                    or usage_meta.get("total_tokens", 0),
            }

            # 解析 JSON
            output_data = self._parse_output(raw_output)

        except Exception as exc:
            error_type = type(exc).__name__
            error_message = str(exc)[:1000]
            logger.exception("审核 Agent 调用异常: trace_id=%s", trace_id)

        ended_at = datetime.now(timezone.utc)
        if latency_ms is None and started_at:
            latency_ms = int((ended_at - started_at).total_seconds() * 1000)

        # 持久化 trace / span
        await self._persist_monitoring(
            trace_id=trace_id,
            user_id=user_id,
            status="failed" if error_type else "completed",
            input_prompt=user_prompt,
            raw_output=raw_output,
            error_type=error_type,
            error_message=error_message,
            started_at=started_at,
            ended_at=ended_at,
            latency_ms=latency_ms or 0,
            token_usage=token_usage,
        )

        return output_data, trace_id

    def _parse_output(self, raw_output: str) -> ModerationAgentOutput:
        """解析并校验模型的 JSON 输出。"""
        # 尝试提取 JSON 块（模型有时会包裹在 ```json 中）
        text = raw_output
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)

        # 基础校验
        verdict = data.get("verdict", "")
        risk_level = data.get("risk_level", "none")
        categories = data.get("categories", [])
        reason = data.get("reason", "")
        suggested_action = data.get("suggested_action", "none")
        flagged_spans_raw = data.get("flagged_spans", [])

        if verdict not in ("pass", "block"):
            raise ValueError(f"无效的 verdict: {verdict}")
        if risk_level not in ("none", "low", "medium", "high"):
            risk_level = "none"
        if suggested_action not in ("none", "unpublish_blog", "mask_text"):
            suggested_action = "none"

        # verdict 为 pass 时必须清空 flagged_spans
        flagged_spans: list[FlaggedSpan] = []
        if verdict == "block":
            for span in flagged_spans_raw:
                flagged_spans.append(
                    FlaggedSpan(
                        field=span.get("field", ""),
                        text=span.get("text", ""),
                        start=int(span.get("start", 0)),
                        end=int(span.get("end", 0)),
                        category=span.get("category", ""),
                        confidence=float(span.get("confidence", 0.0)),
                    )
                )
            if not flagged_spans:
                raise ValueError("verdict 为 block 时 flagged_spans 不能为空")
            if suggested_action == "none":
                suggested_action = "mask_text"

        return ModerationAgentOutput(
            verdict=verdict,
            risk_level=risk_level,
            categories=categories if isinstance(categories, list) else [],
            reason=reason,
            flagged_spans=flagged_spans,
            suggested_action=suggested_action,
        )

    async def _persist_monitoring(
        self,
        *,
        trace_id: str,
        user_id: int | None,
        status: str,
        input_prompt: str,
        raw_output: str,
        error_type: str | None,
        error_message: str | None,
        started_at: datetime,
        ended_at: datetime,
        latency_ms: int,
        token_usage: dict,
    ) -> None:
        """将审核调用过程持久化到 agent_traces / agent_spans。"""
        try:
            buf: dict = {
                "trace_id": trace_id,
                "user_id": user_id,
                "graph_name": "content_moderation",
                "status": status,
                "input_message": input_prompt[:500],
                "output_message": raw_output[:500],
                "total_tokens": token_usage.get("total_tokens", 0),
                "prompt_tokens": token_usage.get("prompt_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens", 0),
                "tool_calls_count": 0,
                "node_steps": 1,
                "latency_ms": latency_ms,
                "started_at": started_at,
                "ended_at": ended_at,
                "error_type": error_type,
                "error_message": error_message,
                "spans": [
                    {
                        "span_type": "llm",
                        "span_name": self.model_name,
                        "status": status,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "latency_ms": latency_ms,
                        "input_data": {"prompts_count": 2},
                        "output_data": {
                            "content_preview": raw_output[:200] if raw_output else None
                        },
                        "error_info": (
                            {"type": error_type, "message": error_message}
                            if error_type
                            else None
                        ),
                        "token_usage": token_usage,
                    }
                ],
            }
            await AgentMonitoringService.persist_trace_async(buf)
        except Exception:
            logger.exception("审核 Agent trace 持久化失败: trace_id=%s", trace_id)
