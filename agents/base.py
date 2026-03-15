"""Base agent class for all AI agents, backed by a local model (Ollama)."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel


class AgentState(BaseModel):
    """Shared state between agents."""

    task: str
    context: Dict[str, Any] = {}
    messages: List[Any] = []
    artifacts: Dict[str, Any] = {}
    status: str = "pending"
    errors: List[str] = []


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model_name: str = "llama3.2:3b",
        temperature: float = 0.7,
    ) -> None:
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

        # Local model via Ollama (ollama.com)
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                HumanMessage(content="{input}"),
            ]
        )

        self.chain = self.prompt | self.llm

    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Process the current task and return updated state."""
        raise NotImplementedError

    def invoke(self, input: str, chat_history: List | None = None) -> str:
        """Simple invoke method for quick testing."""
        return self.chain.invoke(
            {
                "input": input,
                "chat_history": chat_history or [],
            }
        ).content

    def __repr__(self) -> str:
        return f"{self.name}(role={self.role})"

