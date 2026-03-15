"""Documentation agent - writes README and docs."""
from .base import BaseAgent, AgentState


DOCS_SYSTEM_PROMPT = """You are a Documentation Agent, an expert at writing clear, comprehensive documentation.

Your responsibilities:
1. Write README files with getting started guides
2. Create API documentation
3. Write user guides and tutorials
4. Maintain code documentation and docstrings

Documentation principles:
- Write for your audience
- Use clear, concise language
- Include code examples where appropriate
- Use proper Markdown formatting"""


class DocsAgent(BaseAgent):
    """Agent responsible for writing documentation."""

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.4):
        super().__init__(
            name="Docs",
            role="Technical Writer",
            system_prompt=DOCS_SYSTEM_PROMPT,
            model_name=model_name,
            temperature=temperature,
        )

    def process(self, state: AgentState) -> AgentState:
        """Write documentation."""
        task = state.task
        context = state.context

        code = context.get("code", "")

        prompt = f"""Task: {task}

Code to document:
```{code[:3000]}
```

Please create comprehensive documentation:
1. README.md with project overview, installation, usage
2. Any other relevant documentation"""

        response = self.chain.invoke(
            {
                "input": prompt,
                "chat_history": state.messages,
            }
        )

        docs = {"README.md": response.content}

        state.artifacts["documentation"] = docs
        state.artifacts["docs_raw"] = response.content
        state.messages.append(response)
        state.status = "docs_completed"

        return state

