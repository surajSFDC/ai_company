"""Main entry point for AI Company (local model)."""
from orchestrator.manager import ManagerAgent


def main() -> None:
    manager = ManagerAgent()
    task = "Create a Python function that implements an LRU cache"
    result = manager.process_task(task)
    print(f"\nStatus: {result.status}")


if __name__ == "__main__":
    main()
