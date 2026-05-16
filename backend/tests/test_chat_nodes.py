"""chat_nodes 单元测试。"""

from unittest.mock import MagicMock, patch

from app.graphs.nodes.chat_nodes import agent_node


class TestAgentNode:
    """测试 agent_node 防御性编程。"""

    def test_agent_node_returns_empty_when_no_messages(self):
        """state 中没有 messages 时应返回空列表，不抛出 KeyError。"""
        state = {"retrieved_memories": [], "messages": []}
        result = agent_node(state)
        assert result == {"messages": []}

    def test_agent_node_returns_empty_when_messages_missing(self):
        """state 中缺少 messages 键时应返回空列表，不抛出 KeyError。"""
        state = {"retrieved_memories": []}
        result = agent_node(state)
        assert result == {"messages": []}
