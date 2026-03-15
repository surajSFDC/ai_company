"""Researcher agent - researches topics and web searches."""
from .base import BaseAgent, AgentState


RESEARCHER_SYSTEM_PROMPT = """You are a Research Agent, an expert at researching topics thoroughly and presenting findings clearly.

Your responsibilities:
1. Search the web for relevant information
2. Analyze and synthesize findings
3. Compare different approaches/technologies
4. Provide recommendations with pros and cons

Research methodology:
- Start with broad search to understand the topic
- Dig deeper into specific aspects
- Look for official documentation and best practices
- Compare multiple sources and approaches

Output format:
- Executive summary at the top
- Key findings organized by topic
- Pros and cons of different approaches
- Recommendations with reasoning"""


class ResearchAgent(BaseAgent):
    """Agent responsible for researching topics."""

    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.5):
        super().__init__(
            name="Researcher",
            role="Research Analyst",
            system_prompt=RESEARCHER_SYSTEM_PROMPT,
            model_name=model_name,
            temperature=temperature,
        )
        self.web_browser = None

    def set_browser(self, browser) -> None:
        """Set the web browser tool."""
        self.web_browser = browser

    def process(self, state: AgentState) -> AgentState:
        """Research the given topic."""
        task = state.task

        if self.web_browser:
            print("[RESEARCH] Conducting web research...")
            web_results = self.web_browser.research(task)
            state.context["web_research"] = web_results

            prompt = f"""Based on the following web research, provide a comprehensive summary:

Research Query: {task}

Web Research Results:
{web_results}

Please provide:
1. Executive Summary (2-3 sentences)
2. Key Findings (bulleted list)
3. Recommendations"""

            response = self.chain.invoke(
                {
                    "input": prompt,
                    "chat_history": state.messages,
                }
            )

            state.artifacts["research_report"] = response.content
            state.messages.append(response)
            state.status = "research_completed"
        else:
            prompt = f"""Research the following topic thoroughly:

{task}

Please provide:
1. Executive Summary
2. Key concepts and background
3. Best practices
4. Popular tools/frameworks
5. Recommendations with pros and cons"""

            response = self.chain.invoke(
                {
                    "input": prompt,
                    "chat_history": state.messages,
                }
            )

            state.artifacts["research_report"] = response.content
            state.messages.append(response)
            state.status = "research_completed"

        return state

