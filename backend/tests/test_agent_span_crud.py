"""AgentSpan CRUD 单元测试。"""

from datetime import datetime, timezone

from app.crud import agent_span as span_crud
from app.crud import agent_trace as trace_crud


def test_batch_create_agent_spans_resolves_tmp_parent_ids(db_session):
    trace = trace_crud.create_agent_trace(
        db_session,
        trace_id="trace-parent-test",
        conversation_id=None,
        user_id=1,
        graph_name="chat_agent",
        status="completed",
        started_at=datetime.now(timezone.utc),
    )

    created = span_crud.batch_create_agent_spans(
        db_session,
        trace.trace_id,
        [
            {
                "tmp_span_id": "parent",
                "span_type": "tool",
                "span_name": "search_web",
                "status": "completed",
                "started_at": datetime.now(timezone.utc),
                "ended_at": datetime.now(timezone.utc),
            },
            {
                "tmp_span_id": "child",
                "parent_tmp_span_id": "parent",
                "span_type": "web_search",
                "span_name": "query_expansion",
                "status": "completed",
                "started_at": datetime.now(timezone.utc),
                "ended_at": datetime.now(timezone.utc),
            },
        ],
    )

    assert len(created) == 2
    parent, child = created
    assert parent.parent_span_id is None
    assert child.parent_span_id == parent.id


def test_batch_create_agent_spans_keeps_legacy_parent_id(db_session):
    trace = trace_crud.create_agent_trace(
        db_session,
        trace_id="trace-legacy-parent-test",
        conversation_id=None,
        user_id=1,
        graph_name="chat_agent",
        status="completed",
        started_at=datetime.now(timezone.utc),
    )

    parent = span_crud.batch_create_agent_spans(
        db_session,
        trace.trace_id,
        [
            {
                "span_type": "tool",
                "span_name": "search_web",
                "status": "completed",
                "started_at": datetime.now(timezone.utc),
                "ended_at": datetime.now(timezone.utc),
            },
        ],
    )[0]

    child = span_crud.batch_create_agent_spans(
        db_session,
        trace.trace_id,
        [
            {
                "span_type": "llm",
                "span_name": "deepseek-chat",
                "status": "completed",
                "started_at": datetime.now(timezone.utc),
                "ended_at": datetime.now(timezone.utc),
                "parent_span_id": parent.id,
            },
        ],
    )[0]

    assert child.parent_span_id == parent.id
