#!/usr/bin/env python3
"""
Setup script to (re)create the AI Company project structure and core files.

This is inspired by the `agnent_chat.md` design:
- Creates the canonical folder layout (agents, tools, memory, orchestrator, workspace)
- Ensures package __init__ files exist
- Bootstraps config, requirements, env example, README, and main entry point

You can run this script in a fresh folder to scaffold the project, or re-run
it here to repair a partially-created setup. Existing files are not overwritten
unless you pass --force.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from textwrap import dedent


PROJECT_DIR = Path(".").resolve()


def write_file(path: Path, content: str, force: bool = False) -> None:
    """Write text content to a file, optionally skipping if it already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not force:
        return

    path.write_text(content, encoding="utf-8")


def ensure_packages(base: Path) -> None:
    """Create core package directories and empty __init__.py files."""
    package_dirs = [
        base / "agents",
        base / "tools",
        base / "memory",
        base / "orchestrator",
        base / "workspace",
    ]

    for d in package_dirs:
        d.mkdir(parents=True, exist_ok=True)
        init_file = d / "__init__.py"
        if d.name == "agents":
            # Minimal exports; you can later replace with the full multi-agent code
            content = '"""AI Company agents package."""\n'
        elif d.name == "tools":
            content = '"""Tools package for AI Company (file ops, executor, etc.)."""\n'
        elif d.name == "memory":
            content = '"""Memory systems for AI Company (in-memory, vector)."""\n'
        elif d.name == "orchestrator":
            content = '"""Orchestrator package for AI Company (manager, queues)."""\n'
        else:
            content = ""

        if not init_file.exists():
            init_file.write_text(content, encoding="utf-8")


def bootstrap_config(base: Path, force: bool = False) -> None:
    """Create a minimal config.py similar to the one in agnent_chat.md."""
    config_py = dedent(
        '''\
        """Configuration for AI Company agents."""
        from dataclasses import dataclass
        import os


        @dataclass
        class AgentConfig:
            """Configuration for AI agents."""

            model_name: str = "gpt-4o"
            temperature: float = 0.7
            max_tokens: int = 4000
            workspace_dir: str = "./workspace"


        config = AgentConfig()

        # Make sure OPENAI_API_KEY is available at runtime
        os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        '''
    )

    write_file(base / "config.py", config_py, force=force)


def bootstrap_requirements(base: Path, force: bool = False) -> None:
    """Create requirements.txt as defined in the reference chat."""
    requirements_txt = dedent(
        """\
        langchain>=0.1.0
        langchain-openai>=0.0.5
        langgraph>=0.0.20
        pydantic>=2.0.0
        chromadb>=0.4.0
        playwright>=1.40.0
        python-dotenv>=1.0.0
        """
    )

    write_file(base / "requirements.txt", requirements_txt, force=force)


def bootstrap_env_example(base: Path, force: bool = False) -> None:
    """Create .env.example file."""
    env_example = dedent(
        """\
        # Copy this to .env and fill in your API key
        OPENAI_API_KEY=your-api-key-here
        """
    )

    write_file(base / ".env.example", env_example, force=force)


def bootstrap_readme(base: Path, force: bool = False) -> None:
    """Create README.md based on the agent design in agnent_chat.md."""
    readme_md = dedent(
        """\
        # 🤖 AI Company - Your AI-Powered Development Team

        Welcome to your AI company! This is a system where you (the CEO) manage a team of AI agents
        to build software, research topics, and handle various development tasks.

        ## 🌟 Features

        - **Specialized Agents**: Coder, Reviewer, Tester, Researcher, DevOps, Docs, Architect, QA
        - **Parallel Execution**: Run multiple tasks simultaneously
        - **Human-in-the-Loop**: Approve/reject at key checkpoints
        - **Persistent Memory**: Vector-based memory for learning from past tasks
        - **Web Research**: Agents can search the web for information

        ## 🚀 Quick Start

        ```bash
        # Install dependencies
        pip install -r requirements.txt

        # Copy and configure environment
        cp .env.example .env
        # Edit .env and add your OPENAI_API_KEY

        # Run the demo
        python main.py
        ```

        ## 📁 Project Structure

        ```text
        ai_company/
        ├── agents/          # All AI agents
        ├── tools/           # Tools (file ops, executor, browser)
        ├── memory/          # Memory systems
        ├── orchestrator/    # Task queue, approval queue, manager
        ├── workspace/       # Generated outputs
        ├── config.py        # Agent configuration
        ├── main.py          # Entry point
        ├── requirements.txt
        └── .env.example
        ```
        """
    )

    write_file(base / "README.md", readme_md, force=force)


def bootstrap_main(base: Path, force: bool = False) -> None:
    """Create a minimal main.py that wires up the ManagerAgent placeholder."""
    main_py = dedent(
        '''\
        """Main entry point for AI Company."""
        import os

        try:
            from orchestrator.manager import ManagerAgent  # type: ignore
        except ImportError:
            ManagerAgent = None  # Placeholder; implement full manager later


        def main() -> None:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key or "your-api-key-here" in api_key.lower():
                print("\\nSet your API key first:")
                print("  set OPENAI_API_KEY=sk-your-key")
                return

            if ManagerAgent is None:
                print(
                    "ManagerAgent is not implemented yet. "
                    "Add orchestrator/manager.py from your agnent_chat.md reference."
                )
                return

            manager = ManagerAgent()
            task = "Create a Python function that implements an LRU cache"
            result = manager.process_task(task)
            print(f"\\nStatus: {result.status}")


        if __name__ == "__main__":
            main()
        '''
    )

    write_file(base / "main.py", main_py, force=force)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Setup AI Company project structure and core files.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files (by default, existing files are left untouched).",
    )
    return parser.parse_args()


def main_cli() -> None:
    args = parse_args()
    force = args.force

    print(f"📁 Project directory: {PROJECT_DIR}")

    ensure_packages(PROJECT_DIR)
    bootstrap_config(PROJECT_DIR, force=force)
    bootstrap_requirements(PROJECT_DIR, force=force)
    bootstrap_env_example(PROJECT_DIR, force=force)
    bootstrap_readme(PROJECT_DIR, force=force)
    bootstrap_main(PROJECT_DIR, force=force)

    print("\n✅ AI Company project files ensured.")
    print("Next steps:")
    print("  pip install -r requirements.txt")
    print("  copy .env.example to .env and set OPENAI_API_KEY")
    print("  python main.py")


if __name__ == "__main__":
    main_cli()

