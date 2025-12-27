"""Conversation memory management."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """A conversation with message history."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, **metadata: Any) -> Message:
        msg = Message(role=role, content=content, metadata=metadata)
        self.messages.append(msg)
        return msg

    def get_context(self, max_messages: int = 20) -> list[dict[str, str]]:
        """Get recent messages formatted for LLM context."""
        recent = self.messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]


class ConversationMemory:
    """In-memory conversation storage."""

    def __init__(self, max_conversations: int = 100):
        self._conversations: dict[str, Conversation] = {}
        self._max = max_conversations

    def create(self) -> Conversation:
        """Create a new conversation."""
        conv = Conversation()
        self._conversations[conv.id] = conv
        self._cleanup()
        return conv

    def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return self._conversations.get(conversation_id)

    def get_or_create(self, conversation_id: Optional[str] = None) -> Conversation:
        """Get existing or create new conversation."""
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]
        return self.create()

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def _cleanup(self) -> None:
        """Remove oldest conversations if over limit."""
        if len(self._conversations) > self._max:
            sorted_convs = sorted(
                self._conversations.items(),
                key=lambda x: x[1].created_at,
            )
            for conv_id, _ in sorted_convs[: len(sorted_convs) - self._max]:
                del self._conversations[conv_id]
