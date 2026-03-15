"""Architect agent - designs system architecture."""
from .base import BaseAgent, AgentState


ARCHITECT_SYSTEM_PROMPT = """You are a System Architect Agent, an expert at designing scalable, maintainable systems.

Your responsibilities:
1. Design system architecture
2. Create technical specifications
3. Choose appropriate technologies and patterns
4. Define data models and APIs
5. Plan for scalability and security

Architecture principles:
- Keep it simple (YAGNI, KISS)
- Design for failure
- Use appropriate abstractions
- Plan for scaling
- Security by default

Output: Architecture diagrams (Mermaid), component descriptions, recommendations"""


class ArchitectAgent(BaseAgent):
    """Agent responsible for system architecture."""

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.4):
        super().__init__(
            name="Architect",
            role="System Architect",
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            model_name=model_name,
            temperature=temperature,
        )

    def process(self, state: AgentState) -> AgentState:
        """Design system architecture."""
        task = state.task

        prompt = f"""Design the system architecture for:

{task}

Please provide:
1. High-level architecture overview
2. Component diagram (use Mermaid syntax)
3. Technology stack recommendation
4. API design (if applicable)
5. Data model design
6. Scalability and security considerations"""

        response = self.chain.invoke(
            {
                "input": prompt,
                "chat_history": state.messages,
            }
        )

        state.artifacts["architecture"] = response.content
        state.messages.append(response)
        state.status = "architecture_completed"

        return state

