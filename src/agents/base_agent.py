"""Abstract base agent interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass
class ToolCall:
    """Represents a tool invocation."""

    name: str
    arguments: dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResponse:
    """Response from an agent."""

    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    conversation_id: Optional[str] = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseAgent(ABC):
    """Abstract base class for agents."""

    def __init__(self, name: str = "agent"):
        self.name = name
        self._tools: dict[str, dict[str, Any]] = {}

    def register_tool(self, name: str, func: Callable[..., Any], description: str = "") -> None:
        """Register a tool for the agent to use."""
        self._tools[name] = {
            "func": func,
            "description": description,
        }

    @property
    def available_tools(self) -> list[str]:
        return list(self._tools.keys())

    @abstractmethod
    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> AgentResponse:
        """Send a message to the agent and get a response.

        Args:
            message: User message
            conversation_id: Optional ID to continue existing conversation

        Returns:
            AgentResponse with content and any tool calls made
        """
        pass

    @abstractmethod
    async def reset(self, conversation_id: Optional[str] = None) -> None:
        """Reset agent state/memory.

        Args:
            conversation_id: If provided, only reset that conversation
        """
        pass
