"""Coder agent - writes production code."""
from .base import BaseAgent, AgentState
from langchain_core.messages import HumanMessage
import re


CODER_SYSTEM_PROMPT = """You are a Senior Code Agent, an expert programmer who writes clean, efficient, and maintainable code.

Your responsibilities:
1. Write high-quality code based on specifications
2. Follow best practices and coding standards
3. Add appropriate comments and documentation
4. Handle edge cases and error handling
5. Write modular, reusable code

When writing code:
- Use proper naming conventions
- Keep functions small and focused
- Add type hints where applicable
- Include docstrings
- Handle errors gracefully

Output format:
- Always provide the full code file
- Use markdown code blocks with the appropriate language
- Explain your approach briefly"""


class CoderAgent(BaseAgent):
    """Agent responsible for writing code."""

    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.4):
        super().__init__(
            name="Coder",
            role="Senior Software Engineer",
            system_prompt=CODER_SYSTEM_PROMPT,
            model_name=model_name,
            temperature=temperature,
        )

    def process(self, state: AgentState) -> AgentState:
        """Write code based on the task specification."""
        task = state.task
        context = state.context

        # Include memory context if available
        memory_context = context.get("memory_context", "")

        prompt = f"""Task: {task}

Context:
{memory_context}

Please write the code for this task. Include:
1. The complete implementation
2. Any necessary imports
3. Documentation
4. Error handling

Output your code in a structured format."""

        response = self.chain.invoke(
            {
                "input": prompt,
                "chat_history": state.messages,
            }
        )

        code = self._extract_code(response.content)

        state.artifacts["code"] = code
        state.artifacts["code_raw_response"] = response.content
        state.messages.append(HumanMessage(content=prompt))
        state.messages.append(response)
        state.status = "code_generated"

        return state

    def _extract_code(self, response: str) -> str:
        """Extract code from markdown code blocks."""
        pattern = r"```(?:\\w+)?\\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return max(matches, key=len).strip()

        return response.strip()

