"""Simple in-memory store for agent context."""
from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class MemoryItem:
    """A single memory entry."""

    id: str
    content: str
    memory_type: str
    metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class MemoryStore:
    """Simple in-memory store for agent context."""

    def __init__(self) -> None:
        self.memories: List[MemoryItem] = []
        self.current_context: Dict[str, Any] = {}

    def add(self, content: str, memory_type: str, metadata: Dict | None = None) -> str:
        """Add a new memory."""
        item = MemoryItem(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=memory_type,
            metadata=metadata or {},
        )
        self.memories.append(item)
        return item.id

    def search(
        self, query: str, memory_type: str | None = None, limit: int = 5
    ) -> List[MemoryItem]:
        """Search memories by content."""
        results: List[MemoryItem] = []
        query_lower = query.lower()

        for item in reversed(self.memories):
            if query_lower in item.content.lower():
                if memory_type is None or item.memory_type == memory_type:
                    results.append(item)
                    if len(results) >= limit:
                        break

        return results

    def get_recent(
        self, memory_type: str | None = None, limit: int = 10
    ) -> List[MemoryItem]:
        """Get recent memories."""
        memories = self.memories

        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        return memories[-limit:]

    def update_context(self, key: str, value: Any) -> None:
        """Update current context."""
        self.current_context[key] = value

    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        return self.current_context.copy()

    def clear(self) -> None:
        """Clear all memories."""
        self.memories.clear()
        self.current_context.clear()

