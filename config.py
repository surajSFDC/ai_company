"""Configuration for AI Company agents."""
from dataclasses import dataclass
import os


@dataclass
class AgentConfig:
    """Configuration for AI agents."""

    # Default to a local Ollama model; override via env if needed
    model_name: str = os.getenv("AGENT_MODEL_NAME", "llama3.2:3b")
    temperature: float = 0.7
    max_tokens: int = 4000
    workspace_dir: str = "./workspace"


config = AgentConfig()

# Make sure OPENAI_API_KEY is available at runtime
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
