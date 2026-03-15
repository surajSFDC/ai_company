"""Vector store for persistent memory with semantic search."""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import os

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


@dataclass
class MemoryDocument:
    """A document in the memory store."""

    id: str
    content: str
    metadata: Dict[str, Any]
    memory_type: str
    timestamp: datetime = field(default_factory=datetime.now)


class VectorMemoryStore:
    """Persistent memory store with semantic search.

    For a pure local setup we avoid external embedding APIs and always
    use a simple in-memory substring search. You can extend this later
    to plug in a local embedding model if desired.
    """

    def __init__(
        self,
        persist_directory: str = "./memory_data",
        embedding_model: str = "text-embedding-3-small",
    ):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        # We keep the Chroma plumbing available but do not depend on OpenAI
        # embeddings or any external API keys.
        self.use_chroma = False
        if CHROMADB_AVAILABLE:
            try:
                self._init_chroma()
            except Exception:
                self._init_fallback()
        else:
            self._init_fallback()

        self.documents: List[MemoryDocument] = []

    def _init_chroma(self) -> None:
        """Initialize ChromaDB (metadata only, no external embeddings)."""
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="agent_memory",
            metadata={"description": "AI Company Agent Memory"},
        )
        # We still don't store vectors to avoid embedding dependencies.
        self.use_chroma = False

    def _init_fallback(self) -> None:
        """Initialize fallback in-memory store."""
        self.use_chroma = False

    def add(
        self,
        content: str,
        memory_type: str,
        metadata: Dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        """Add a document to memory."""
        doc_id = doc_id or str(uuid.uuid4())

        document = MemoryDocument(
            id=doc_id,
            content=content,
            metadata=metadata or {},
            memory_type=memory_type,
        )

        if self.use_chroma and self.embeddings:
            try:
                embedding = self.embeddings.embed_query(content)
                self.collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[{**(metadata or {}), "memory_type": memory_type}],
                )
            except Exception:
                # Fall back silently if Chroma interaction fails
                pass

        self.documents.append(document)
        return doc_id

    def search(
        self,
        query: str,
        memory_type: str | None = None,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> List[MemoryDocument]:
        """Search memory by semantic similarity (fallback: substring)."""
        if not self.documents:
            return []

        query_lower = query.lower()
        results: List[MemoryDocument] = []

        for doc in reversed(self.documents):
            if query_lower in doc.content.lower():
                if memory_type is None or doc.memory_type == memory_type:
                    results.append(doc)
                    if len(results) >= limit:
                        break

        return results

    def add_code(
        self, code: str, language: str = "python", metadata: Dict[str, Any] | None = None
    ) -> str:
        """Add code to memory."""
        return self.add(
            content=code,
            memory_type="code",
            metadata={**(metadata or {}), "language": language},
        )

    def add_task_result(
        self,
        task: str,
        result: str,
        status: str,
        artifacts: Dict[str, Any] | None = None,
    ) -> str:
        """Store task result in memory."""
        return self.add(
            content=f"Task: {task}\n\nResult: {result}\nStatus: {status}",
            memory_type="task",
            metadata={"task": task, "status": status},
        )

    def get_context_for_task(self, task: str) -> str:
        """Get relevant context for a new task."""
        related = self.search(task, memory_type="task", limit=3)

        if not related:
            return ""

        context_parts = ["## Related Past Tasks"]
        for doc in related:
            context_parts.append(f"- {doc.content[:200]}...")

        return "\n".join(context_parts)

