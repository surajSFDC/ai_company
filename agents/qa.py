"""QA agent - performs quality assurance."""
from .base import BaseAgent, AgentState


QA_SYSTEM_PROMPT = """You are a QA Agent, an expert at ensuring software quality through comprehensive testing.

Your responsibilities:
1. Write comprehensive test plans
2. Create integration and e2e tests
3. Perform risk analysis
4. Identify edge cases and corner cases
5. Verify security and performance

Testing approach:
- Test behavior, not implementation
- Cover happy path AND edge cases
- Test error conditions
- Consider security implications

Output:
- Detailed test plan
- Test cases with expected results
- Risk assessment"""


class QAAgent(BaseAgent):
    """Agent responsible for quality assurance."""

    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.4):
        super().__init__(
            name="QA",
            role="QA Engineer",
            system_prompt=QA_SYSTEM_PROMPT,
            model_name=model_name,
            temperature=temperature,
        )

    def process(self, state: AgentState) -> AgentState:
        """Perform quality assurance."""
        task = state.task
        context = state.context

        code = context.get("code", "")
        unit_tests = context.get("tests", "")

        prompt = f"""Perform quality assurance for:

Task: {task}

Code:
```{code[:2000]}
```

Unit Tests:
```{unit_tests[:1500]}
```

Please provide:
1. Test Plan with test objectives and scope
2. Additional Test Cases (edge cases not covered)
3. Risk Assessment (potential issues, security concerns)
4. Recommendations for improvement"""

        response = self.chain.invoke(
            {
                "input": prompt,
                "chat_history": state.messages,
            }
        )

        state.artifacts["qa_report"] = response.content
        state.messages.append(response)
        state.status = "qa_completed"

        return state

