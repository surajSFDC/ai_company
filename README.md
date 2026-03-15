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
