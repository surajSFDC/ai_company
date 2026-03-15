"""DevOps agent - creates infrastructure and deployment configs."""
from .base import BaseAgent, AgentState
import re


DEVOPS_SYSTEM_PROMPT = """You are a DevOps Agent, an expert in infrastructure, deployment, and CI/CD.

Your responsibilities:
1. Create Dockerfiles and docker-compose files
2. Set up CI/CD pipelines (GitHub Actions)
3. Write Kubernetes manifests
4. Configure monitoring and logging
5. Set up environment configurations

When creating DevOps artifacts:
- Follow industry best practices
- Use official images and up-to-date versions
- Include proper health checks
- Set up proper logging and error handling
- Use secrets management (never hardcode secrets)

Output: Complete, production-ready configurations"""


class DevOpsAgent(BaseAgent):
    """Agent responsible for DevOps tasks."""

    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.3):
        super().__init__(
            name="DevOps",
            role="DevOps Engineer",
            system_prompt=DEVOPS_SYSTEM_PROMPT,
            model_name=model_name,
            temperature=temperature,
        )

    def process(self, state: AgentState) -> AgentState:
        """Create DevOps artifacts."""
        task = state.task
        context = state.context

        existing_code = context.get("code", "")
        project_type = context.get("project_type", "python")

        prompt = f"""Task: {task}

Project Type: {project_type}

Existing code (if any):
```{existing_code[:2000]}
```

Please create the appropriate DevOps artifacts (Dockerfile, docker-compose.yml, GitHub Actions, etc.)."""

        response = self.chain.invoke(
            {
                "input": prompt,
                "chat_history": state.messages,
            }
        )

        artifacts = self._extract_artifacts(response.content)

        state.artifacts["devops"] = artifacts
        state.artifacts["devops_raw"] = response.content
        state.messages.append(response)
        state.status = "devops_completed"

        return state

    def _extract_artifacts(self, content: str) -> dict:
        """Extract different DevOps artifacts from response."""
        artifacts: dict = {}
        pattern = r"```(?:\\w+)?\\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        for i, match in enumerate(matches):
            lower_content = content.lower()
            if "dockerfile" in lower_content[:200]:
                artifacts["Dockerfile"] = match.strip()
            elif "docker-compose" in lower_content[:200]:
                artifacts["docker-compose.yml"] = match.strip()
            elif ".yml" in lower_content or ".yaml" in lower_content:
                artifacts[f"config_{i}.yml"] = match.strip()
            else:
                artifacts[f"artifact_{i}.txt"] = match.strip()

        return artifacts

