"""Main orchestrator - the CEO of your AI company."""
from typing import Dict, Any, List
from datetime import datetime
import json
import os

from agents.base import AgentState
from agents.coder import CoderAgent
from agents.reviewer import ReviewerAgent
from agents.tester import TesterAgent
from agents.researcher import ResearchAgent
from agents.devops import DevOpsAgent
from agents.docs_writer import DocsAgent
from agents.architect import ArchitectAgent
from agents.qa import QAAgent
from tools.file_ops import FileOperations
from tools.executor import CodeExecutor
from tools.web_browser import WebBrowserSync
from memory.store import MemoryStore
from memory.vector_store import VectorMemoryStore
from orchestrator.task_queue import TaskQueue, Task, TaskPriority, TaskStatus
from orchestrator.approval_queue import (
    ApprovalQueue,
    ApprovalType,
    ApprovalStatus,
)


class ManagerAgent:
    """Full-featured orchestrator with all features."""

    def __init__(
        self,
        model_name: str = "llama3.2",
        workspace_dir: str = "./workspace",
        auto_execute: bool = False,
        enable_web_research: bool = True,
        auto_approve: bool = False,
        enable_persistent_memory: bool = True,
        max_parallel_tasks: int = 5,
    ):
        # Initialize all agents
        self.coder = CoderAgent(model_name=model_name)
        self.reviewer = ReviewerAgent(model_name=model_name)
        self.tester = TesterAgent(model_name=model_name)
        self.devops = DevOpsAgent(model_name=model_name)
        self.docs = DocsAgent(model_name=model_name)
        self.architect = ArchitectAgent(model_name=model_name)
        self.qa = QAAgent(model_name=model_name)

        # Research agent
        self.researcher = ResearchAgent(model_name=model_name)
        if enable_web_research:
            self.web_browser = WebBrowserSync()
            self.researcher.set_browser(self.web_browser)
        else:
            self.web_browser = None

        # Tools
        self.file_ops = FileOperations(workspace_dir)
        self.executor = CodeExecutor()

        # Memory
        self.memory = MemoryStore()
        if enable_persistent_memory:
            self.vector_memory = VectorMemoryStore(
                persist_directory=f"{workspace_dir}/vector_store"
            )
        else:
            self.vector_memory = None

        # Task queue
        self.task_queue = TaskQueue(max_workers=max_parallel_tasks)

        # Approval queue
        self.approval_queue = ApprovalQueue(
            auto_approve=auto_approve,
            on_approval_callback=self._on_approval_callback,
        )

        self.auto_approve = auto_approve
        self.auto_execute = auto_execute
        self.workspace_dir = workspace_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_task(self, task: str, context: Dict[str, Any] | None = None) -> AgentState:
        """Process a single task."""

        memory_context = ""
        if self.vector_memory:
            memory_context = self.vector_memory.get_context_for_task(task)

        full_context: Dict[str, Any] = context or {}
        full_context["memory_context"] = memory_context

        print(f"\n{'='*60}")
        print(f"[START] Starting task: {task}")
        print(f"{'='*60}\n")

        state = self._route_task(task, full_context)

        if self.vector_memory and state.status == "completed":
            self.vector_memory.add_task_result(task, state.status, "completed", state.artifacts)

        return state

    def process_tasks_parallel(
        self,
        tasks: List[str],
        contexts: List[Dict[str, Any]] | None = None,
        approval_required: bool = False,
    ) -> List[AgentState]:
        """Process multiple tasks in parallel."""

        print(f"\n{'='*60}")
        print(f"[START] Starting {len(tasks)} tasks in parallel")
        print(f"{'='*60}\n")

        task_ids: List[str] = []

        for i, task in enumerate(tasks):
            context = contexts[i] if contexts and i < len(contexts) else {}
            task_id = self.task_queue.add_task(
                name=f"Task {i+1}",
                description=task,
                task_type="full_stack",
                priority=TaskPriority.NORMAL,
                context=context,
                approval_required=approval_required,
            )
            task_ids.append(task_id)

        results: List[AgentState] = []
        while True:
            next_task: Task | None = self.task_queue.get_next_task()

            if not next_task:
                status = self.task_queue.get_status_summary()
                if status["running"] == 0 and status["pending"] == 0:
                    break
                continue

            def execute_fn(task_obj: Task) -> AgentState:
                return self._route_task(task_obj.description, task_obj.context)

            future = self.task_queue.start_task(next_task.id, execute_fn)

            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Task failed: {e}")
                # Represent failure as a minimal AgentState
                fail_state = AgentState(
                    task=next_task.description,
                    context=next_task.context,
                    status="failed",
                    errors=[str(e)],
                )
                results.append(fail_state)

        return results

    def search_memory(self, query: str) -> List[Any]:
        """Search vector memory for related items."""
        if not self.vector_memory:
            return []
        return self.vector_memory.search(query)

    def get_status(self) -> Dict[str, Any]:
        """Get system status summary."""
        return {
            "task_queue": self.task_queue.get_status_summary(),
            "approvals": self.approval_queue.get_summary(),
            "memory": self._get_memory_stats(),
        }

    def get_pending_approvals(self):
        """Return pending approval requests."""
        return self.approval_queue.get_pending()

    def approve(self, request_id: str, notes: str = "") -> bool:
        """Approve a specific approval request."""
        return self.approval_queue.approve(request_id, skip=False, notes=notes)

    def reject(self, request_id: str, reason: str = "") -> bool:
        """Reject a specific approval request."""
        return self.approval_queue.reject(request_id, reason=reason)

    def shutdown(self) -> None:
        """Shutdown any background workers."""
        self.task_queue.shutdown()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _route_task(self, task: str, context: Dict[str, Any]) -> AgentState:
        """Route task to appropriate handler."""
        task_type = self._determine_task_type(task)

        if task_type == "research":
            return self._handle_research(task, context)
        if task_type == "architecture":
            return self._handle_architecture(task, context)
        if task_type == "devops":
            return self._handle_devops(task, context)
        if task_type == "documentation":
            return self._handle_documentation(task, context)

        return self._handle_full_stack(task, context)

    def _determine_task_type(self, task: str) -> str:
        """Determine task type."""
        task_lower = task.lower()

        if "research" in task_lower or "compare" in task_lower:
            return "research"
        if "architecture" in task_lower or "design" in task_lower:
            return "architecture"
        if any(x in task_lower for x in ["deploy", "docker", "ci/cd", "k8s"]):
            return "devops"
        if any(x in task_lower for x in ["document", "readme"]):
            return "documentation"

        return "full_stack"

    # -- Handlers ------------------------------------------------------

    def _handle_full_stack(
        self,
        task: str,
        context: Dict[str, Any],
        require_approval: bool = True,
    ) -> AgentState:
        """Handle full-stack development."""

        state = AgentState(task=task, context=context, status="started")

        # Generate code
        print("[STEP 1] Generating code...")
        state = self.coder.process(state)

        if state.status == "failed":
            return state

        # Code review
        print("\n[STEP 2] Reviewing code...")
        state = self.reviewer.process(state)

        if state.status == "needs_revision":
            print("\n[REVISION] Handling revisions...")
            state = self._handle_revision(state)

        if state.status == "approved":
            # Generate tests
            print("\n[STEP 3] Generating tests...")
            state = self.tester.process(state)

            # QA
            print("\n[STEP 4] Running QA...")
            state.context["code"] = state.artifacts.get("code", "")
            state.context["tests"] = state.artifacts.get("tests", "")
            state = self.qa.process(state)

            # DevOps
            print("\n[STEP 5] Creating DevOps artifacts...")
            state.context["project_type"] = self._detect_project_type(
                state.artifacts.get("code", "")
            )
            state = self.devops.process(state)

            # Documentation
            print("\n[STEP 6] Writing documentation...")
            state = self.docs.process(state)

            # Execute tests
            if self.auto_execute:
                print("\n[STEP 7] Running tests...")
                state = self._execute_tests(state)

        state.status = "completed"
        self._save_artifacts(state, "full_stack")

        if self.vector_memory:
            code = state.artifacts.get("code", "")
            if code:
                self.vector_memory.add_code(code, metadata={"task": task})

        return state

    def _handle_research(self, task: str, context: Dict[str, Any]) -> AgentState:
        """Handle research task."""
        state = AgentState(task=task, context=context, status="started")
        print("[RESEARCH] Running research agent...")
        state = self.researcher.process(state)
        state.status = "completed"
        self._save_artifacts(state, "research")
        return state

    def _handle_architecture(self, task: str, context: Dict[str, Any]) -> AgentState:
        """Handle architecture task."""
        state = AgentState(task=task, context=context, status="started")
        print("[ARCHITECTURE] Running architecture agent...")
        state = self.architect.process(state)
        state.status = "completed"
        self._save_artifacts(state, "architecture")
        return state

    def _handle_devops(self, task: str, context: Dict[str, Any]) -> AgentState:
        """Handle DevOps task."""
        state = AgentState(task=task, context=context, status="started")
        print("[DEVOPS] Running DevOps agent...")
        state = self.devops.process(state)
        state.status = "completed"
        self._save_artifacts(state, "devops")
        return state

    def _handle_documentation(self, task: str, context: Dict[str, Any]) -> AgentState:
        """Handle documentation task."""
        state = AgentState(task=task, context=context, status="started")
        print("[DOCS] Running documentation agent...")
        state = self.docs.process(state)
        state.status = "completed"
        self._save_artifacts(state, "docs")
        return state

    def _handle_revision(self, state: AgentState) -> AgentState:
        """Handle revision cycle after review."""
        # Simple strategy: send task back to coder and then reviewer once more
        print("🔁 Re-running coder and reviewer for revisions...")
        state = self.coder.process(state)
        state = self.reviewer.process(state)
        return state

    # -- Utilities -----------------------------------------------------

    def _detect_project_type(self, code: str) -> str:
        """Very small heuristic to guess project type."""
        if "FastAPI" in code or "flask" in code.lower():
            return "python_web"
        if "React" in code or "Next.js" in code or "next/router" in code:
            return "react"
        return "python"

    def _execute_tests(self, state: AgentState) -> AgentState:
        """Execute generated tests."""
        code = state.artifacts.get("code", "")
        tests = state.artifacts.get("tests", "")
        if not code or not tests:
            return state

        result = self.executor.execute_tests(tests, code)
        state.artifacts["test_run"] = result
        return state

    def _save_artifacts(self, state: AgentState, task_type: str) -> None:
        """Persist artifacts from a completed state to workspace."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.join(self.workspace_dir, "outputs", task_type, timestamp)
        os.makedirs(base_dir, exist_ok=True)

        payload = {
            "task": state.task,
            "status": state.status,
            "errors": state.errors,
            "artifacts": list(state.artifacts.keys()),
        }

        meta_path = os.path.join(base_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        for key, value in state.artifacts.items():
            if isinstance(value, (str, bytes)):
                filename = f"{key}.txt"
                if key == "code":
                    filename = "main.py"
                elif key == "tests":
                    filename = "test_main.py"
                path = os.path.join(base_dir, filename)
                mode = "wb" if isinstance(value, bytes) else "w"
                with open(path, mode) as f:
                    f.write(value)

    def _on_approval_callback(self, request) -> None:
        """Called when an approval request is resolved."""
        # For now we just log; you can extend this to trigger follow‑up work.
        print(f"[APPROVAL] Resolved: {request.id} -> {request.status}")

    def _get_memory_stats(self) -> Dict[str, Any]:
        """Return basic memory statistics."""
        stats = {
            "vector_store_enabled": bool(self.vector_memory),
            "documents": 0,
        }
        if self.vector_memory:
            stats["documents"] = len(self.vector_memory.documents)
        return stats

