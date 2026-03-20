"""Main entry point for AI Company (local model)."""
import argparse
from orchestrator.manager import ManagerAgent
from office.server import create_app
import uvicorn


def run_office() -> None:
    """Launch the Virtual Office dashboard."""
    parser = argparse.ArgumentParser(description="AI Company - Virtual Office")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--model", default=None, help="Override the agent model name"
    )
    args = parser.parse_args()

    manager = ManagerAgent()
    if args.model:
        manager.coder.llm = type(manager.coder.llm)(model=args.model)

    app = create_app(manager)
    print(f"\n{'='*60}")
    print("AI Company Virtual Office")
    print(f"{'='*60}")
    print(f"Opening at: http://{args.host}:{args.port}")
    print(f"\nWatch your AI agents collaborate in real-time!")
    print(f"Press Ctrl+C to stop.\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


def main() -> None:
    """Run a single task via CLI (original behavior)."""
    manager = ManagerAgent()
    task = "Create a Python function that implements an LRU cache"
    result = manager.process_task(task)
    print(f"\nStatus: {result.status}")


if __name__ == "__main__":
    run_office()
