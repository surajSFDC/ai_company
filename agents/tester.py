"""Tester agent - writes comprehensive tests."""
from .base import BaseAgent, AgentState
from langchain_core.messages import HumanMessage
import re


TESTER_SYSTEM_PROMPT = """You are a Testing Agent, an expert at writing comprehensive tests for code.

Your responsibilities:
1. Write unit tests that cover edge cases
2. Write integration tests where appropriate
3. Use appropriate testing frameworks
4. Follow testing best practices
5. Mock external dependencies
6. Ensure high test coverage

Output:
- Provide complete, runnable test code
- Use proper assertions
- Include both positive and negative test cases"""


class TesterAgent(BaseAgent):
    """Agent responsible for writing tests."""

    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.4):
        super().__init__(
            name="Tester",
            role="QA Engineer",
            system_prompt=TESTER_SYSTEM_PROMPT,
            model_name=model_name,
            temperature=temperature,
        )

    def process(self, state: AgentState) -> AgentState:
        """Write tests for the generated code."""
        code = state.artifacts.get("code", "")

        if not code:
            state.errors.append("No code to test")
            state.status = "failed"
            return state

        prompt = f"""Write comprehensive tests for the following code:

```{code}
```

Please write tests using pytest. Cover:
- Happy path scenarios
- Edge cases
- Error conditions
- Boundary values"""

        response = self.chain.invoke(
            {
                "input": prompt,
                "chat_history": state.messages,
            }
        )

        tests = self._extract_code(response.content)

        state.artifacts["tests"] = tests
        state.artifacts["tests_raw_response"] = response.content
        state.messages.append(response)
        state.status = "tests_generated"

        return state

    def _extract_code(self, response: str) -> str:
        """Extract code from markdown code blocks."""
        pattern = r"```(?:\\w+)?\\n(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return max(matches, key=len).strip()

        return response.strip()

