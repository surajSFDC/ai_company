# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Virtual Office dashboard (default)
python main.py

# Run the main orchestrator (CLI mode)
python main.py --cli  # or modify main.py to call main() directly

# Run tests
python dev/test_agents.py

# Debug/test individual agents
python dev/debug_tools.py

# Virtual Office options
python main.py --port 8080    # Custom port
python main.py --host 0.0.0.0 # Bind to all interfaces
```

## Architecture Overview

This is a multi-agent AI system where specialized agents collaborate to complete software development tasks. The architecture follows a pipeline pattern with a central orchestrator.

### Core Components

**Orchestrator** (`orchestrator/manager.py`) - The "CEO" that:
- Routes tasks to appropriate agents based on task type (research, architecture, devops, documentation, full-stack)
- Manages a 6-step pipeline for full-stack tasks: Code → Review → Test → QA → DevOps → Docs
- Handles parallel task execution via `TaskQueue` (thread pool with configurable workers)
- Manages approval workflows and persistent memory

**Virtual Office** (`office/server.py`) - Real-time dashboard:
- FastAPI server with WebSocket for live updates
- Visual office view showing each agent's status, current task, and messages
- Activity feed showing inter-agent communication and handoffs
- Task submission form for assigning new work

**Agents** (`agents/`) - Specialized agents built on `BaseAgent`:
- `CoderAgent` - Writes production code
- `ReviewerAgent` - Reviews code quality
- `TesterAgent` - Generates tests
- `QAAgent` - Quality assurance
- `DevOpsAgent` - Creates deployment configs
- `DocsAgent` - Writes documentation
- `ArchitectAgent` - System design
- `ResearchAgent` - Web research capabilities

**Tools** (`tools/`):
- `FileOperations` - Safe file I/O in workspace
- `CodeExecutor` - Execute Python code/tests
- `WebBrowser` - Web scraping for research

**Memory** (`memory/`):
- `MemoryStore` - In-memory session storage
- `VectorMemoryStore` - Persistent vector store (ChromaDB) with fallback to substring search

### Data Flow

1. `ManagerAgent.process_task()` receives a task
2. Task type detection routes to appropriate handler
3. Handler creates `AgentState` and passes through agent pipeline
4. Each agent processes and updates `state.artifacts`
5. Results saved to `workspace/outputs/` and indexed in vector memory

### Key Patterns

- **AgentState**: Pydantic model carrying task, context, messages, artifacts, status
- **BaseAgent**: LangChain-based with Ollama backend (`llama3.2:3b` default)
- **LangGraph**: Used for agent orchestration
- **Parallel execution**: ThreadPoolExecutor in TaskQueue
- **Human-in-the-loop**: ApprovalQueue for code generation checkpoints

### Configuration

Environment variables:
- `AGENT_MODEL_NAME` - Override default Ollama model
- `OPENAI_API_KEY` - Required for OpenAI-based features
