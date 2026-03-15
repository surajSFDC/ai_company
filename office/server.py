"""Virtual Office Server - Real-time agent dashboard with WebSocket."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict, List, Any
import asyncio
import json
from datetime import datetime
import threading

from agents.base import AgentState
from orchestrator.manager import ManagerAgent


class OfficeEvent:
    """Event broadcasted to all connected clients."""

    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class OfficeHub:
    """Central hub managing office state and WebSocket connections."""

    def __init__(self, manager: ManagerAgent):
        self.manager = manager
        self.clients: List[WebSocket] = []
        self.agent_status: Dict[str, Dict[str, Any]] = self._init_agent_status()
        self.events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def _init_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Initialize status for all agents."""
        agents = [
            ("manager", "Manager", "CEO - Orchestrating tasks"),
            ("architect", "Architect", "System Design & Architecture"),
            ("coder", "Coder", "Writing production code"),
            ("reviewer", "Reviewer", "Code review & quality"),
            ("tester", "Tester", "Generating test cases"),
            ("qa", "QA", "Quality assurance"),
            ("devops", "DevOps", "Deployment & CI/CD"),
            ("docs", "Docs", "Documentation"),
            ("researcher", "Researcher", "Web research"),
        ]
        return {
            name: {
                "display_name": display,
                "role": role,
                "status": "idle",
                "current_task": None,
                "message": "Waiting for tasks...",
                "avatar": self._get_avatar(name),
            }
            for name, display, role in agents
        }

    def _get_avatar(self, agent_name: str) -> str:
        """Get emoji avatar for agent."""
        avatars = {
            "manager": "👔",
            "architect": "🏗️",
            "coder": "💻",
            "reviewer": "🔍",
            "tester": "🧪",
            "qa": "✅",
            "devops": "🚀",
            "docs": "📝",
            "researcher": "🌐",
        }
        return avatars.get(agent_name, "🤖")

    def update_agent_status(
        self, agent_name: str, status: str, task: str = None, message: str = None
    ):
        """Update agent status and broadcast to clients."""
        with self._lock:
            if agent_name in self.agent_status:
                self.agent_status[agent_name]["status"] = status
                if task:
                    self.agent_status[agent_name]["current_task"] = task
                if message:
                    self.agent_status[agent_name]["message"] = message

            event = OfficeEvent(
                "agent_update",
                {
                    "agent": agent_name,
                    "status": status,
                    "task": task,
                    "message": message,
                },
            )
            self.events.append(event.to_dict())
            self._broadcast(event)

    def log_message(self, agent_name: str, message: str, msg_type: str = "info"):
        """Log a message from an agent."""
        event = OfficeEvent(
            "agent_message",
            {"agent": agent_name, "message": message, "type": msg_type},
        )
        self.events.append(event.to_dict())
        self._broadcast(event)

    def _broadcast(self, event: OfficeEvent):
        """Broadcast event to all connected clients."""
        asyncio.create_task(self._send_to_clients(event))

    async def _send_to_clients(self, event: OfficeEvent):
        """Send event to all WebSocket clients."""
        for client in self.clients:
            try:
                await client.send_json(event.to_dict())
            except Exception:
                pass

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.clients.append(websocket)
        # Send initial state
        await websocket.send_json(
            {
                "type": "init",
                "data": {
                    "agents": self.agent_status,
                    "events": self.events[-50:],  # Last 50 events
                },
            }
        )

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected client."""
        if websocket in self.clients:
            self.clients.remove(websocket)

    def get_office_state(self) -> Dict[str, Any]:
        """Get current office state."""
        return {"agents": self.agent_status, "events": self.events}


# Global hub instance
hub: OfficeHub = None


def create_app(manager: ManagerAgent = None) -> FastAPI:
    """Create FastAPI application for virtual office."""
    global hub

    if manager is None:
        manager = ManagerAgent()

    hub = OfficeHub(manager)

    app = FastAPI(title="AI Company Virtual Office")

    @app.get("/")
    async def get_office():
        """Serve the office dashboard."""
        return HTMLResponse(get_office_html())

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await hub.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Handle commands from client if needed
        except WebSocketDisconnect:
            hub.disconnect(websocket)

    @app.get("/api/office")
    async def get_office_state():
        """Get current office state."""
        return hub.get_office_state()

    @app.post("/api/task")
    async def submit_task(task: dict):
        """Submit a new task to the office."""
        task_description = task.get("description", "")
        task_type = task.get("type", "full_stack")

        hub.update_agent_status("manager", "active", task_description, "Received new task")
        hub.log_message("manager", f"Starting task: {task_description}", "system")

        # Run task in background
        asyncio.create_task(run_task_with_updates(task_description, task_type))

        return {"status": "started", "task": task_description}

    async def run_task_with_updates(task: str, task_type: str = "full_stack"):
        """Run task and broadcast updates through the office."""
        try:
            # Determine task flow based on type
            if task_type == "research":
                await run_research_flow(task)
            elif task_type == "architecture":
                await run_architecture_flow(task)
            elif task_type == "devops":
                await run_devops_flow(task)
            elif task_type == "documentation":
                await run_docs_flow(task)
            else:
                await run_full_stack_flow(task)
        except Exception as e:
            hub.log_message("manager", f"Task error: {str(e)}", "error")
            hub.update_agent_status("manager", "error", message=str(e))

    async def run_research_flow(task: str):
        """Run research task flow."""
        hub.update_agent_status("researcher", "working", task, "Starting research...")
        hub.log_message("researcher", "Searching the web for information...", "action")
        await asyncio.sleep(2)  # Simulate research time
        hub.update_agent_status("researcher", "completed", task, "Research complete")
        hub.log_message("researcher", "Found relevant information", "success")
        hub.update_agent_status("manager", "completed", task, "Research task done")

    async def run_architecture_flow(task: str):
        """Run architecture task flow."""
        hub.update_agent_status("architect", "working", task, "Designing system...")
        hub.log_message("architect", "Creating architecture design...", "action")
        await asyncio.sleep(2)
        hub.update_agent_status("architect", "completed", task, "Architecture complete")
        hub.log_message("architect", "Design ready for review", "success")
        hub.update_agent_status("manager", "completed", task, "Architecture task done")

    async def run_devops_flow(task: str):
        """Run DevOps task flow."""
        hub.update_agent_status("devops", "working", task, "Creating deployment config...")
        hub.log_message("devops", "Setting up CI/CD pipeline...", "action")
        await asyncio.sleep(2)
        hub.update_agent_status("devops", "completed", task, "DevOps artifacts ready")
        hub.log_message("devops", "Dockerfile and workflow created", "success")
        hub.update_agent_status("manager", "completed", task, "DevOps task done")

    async def run_docs_flow(task: str):
        """Run documentation task flow."""
        hub.update_agent_status("docs", "working", task, "Writing documentation...")
        hub.log_message("docs", "Creating README and docs...", "action")
        await asyncio.sleep(2)
        hub.update_agent_status("docs", "completed", task, "Documentation complete")
        hub.log_message("docs", "Docs written successfully", "success")
        hub.update_agent_status("manager", "completed", task, "Documentation task done")

    async def run_full_stack_flow(task: str):
        """Run full development pipeline with all agents."""
        agents_flow = [
            ("architect", "Designing architecture...", "Architecture planned"),
            ("coder", "Writing code...", "Code implementation complete"),
            ("reviewer", "Reviewing code...", "Code review passed"),
            ("tester", "Creating tests...", "Test suite generated"),
            ("qa", "Running QA checks...", "QA passed"),
            ("devops", "Setting up deployment...", "DevOps artifacts ready"),
            ("docs", "Writing documentation...", "Documentation complete"),
        ]

        for agent_name, start_msg, complete_msg in agents_flow:
            hub.update_agent_status(agent_name, "working", task, start_msg)
            hub.log_message(agent_name, start_msg.split(".")[0], "action")
            await asyncio.sleep(1.5)  # Simulate work time
            hub.update_agent_status(agent_name, "completed", task, complete_msg)
            hub.log_message(agent_name, complete_msg, "success")

            # Show inter-agent communication
            if agent_name == "coder":
                hub.log_message(
                    "coder", "Passing code to reviewer for feedback", "handoff"
                )
            elif agent_name == "reviewer":
                hub.log_message("reviewer", "Code looks good, sending to tester", "handoff")
            elif agent_name == "tester":
                hub.log_message("tester", "Tests ready, QA team can verify", "handoff")
            elif agent_name == "devops":
                hub.log_message("devops", "Deployment ready, docs team can document", "handoff")

        hub.update_agent_status("manager", "completed", task, "All tasks complete!")
        hub.log_message("manager", "🎉 Project delivered successfully!", "success")

    return app


def get_office_html() -> str:
    """Return the office dashboard HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Company Virtual Office</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .office-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        header h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        header p { opacity: 0.7; margin-top: 10px; }

        /* Task Input Section */
        .task-input-section {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .task-input-section h2 { margin-bottom: 15px; font-size: 1.3em; }
        .task-form { display: flex; gap: 15px; flex-wrap: wrap; }
        .task-form input[type="text"] {
            flex: 1;
            min-width: 300px;
            padding: 15px 20px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1em;
        }
        .task-form input[type="text"]:focus {
            outline: 2px solid #00d9ff;
        }
        .task-form select {
            padding: 15px 20px;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 1em;
            cursor: pointer;
        }
        .task-form button {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            color: #1a1a2e;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .task-form button:hover { transform: scale(1.05); }
        .task-form button:disabled { opacity: 0.5; cursor: not-allowed; }

        /* Office Grid */
        .office-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .agent-desk {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .agent-desk::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: transparent;
            transition: background 0.3s;
        }
        .agent-desk.working::before { background: #ffaa00; }
        .agent-desk.completed::before { background: #00ff88; }
        .agent-desk.error::before { background: #ff4444; }
        .agent-desk.idle::before { background: #00d9ff; }

        .agent-desk:hover {
            transform: translateY(-5px);
            background: rgba(255,255,255,0.08);
        }
        .agent-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        .agent-avatar {
            font-size: 2.5em;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }
        .agent-info h3 { font-size: 1.2em; margin-bottom: 5px; }
        .agent-info p { opacity: 0.6; font-size: 0.9em; }
        .agent-status {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin-top: 10px;
        }
        .status-idle { background: rgba(0,217,255,0.2); color: #00d9ff; }
        .status-working { background: rgba(255,170,0,0.2); color: #ffaa00; }
        .status-completed { background: rgba(0,255,136,0.2); color: #00ff88; }
        .status-error { background: rgba(255,68,68,0.2); color: #ff4444; }

        .agent-task {
            margin-top: 15px;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            font-size: 0.9em;
        }
        .agent-task-label { opacity: 0.5; font-size: 0.8em; margin-bottom: 5px; }
        .agent-task-text { color: #00d9ff; }

        .agent-message {
            margin-top: 10px;
            padding: 10px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            font-size: 0.85em;
            border-left: 3px solid #00d9ff;
        }

        /* Activity Feed */
        .activity-section {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .activity-section h2 { margin-bottom: 20px; font-size: 1.3em; }
        .activity-feed {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 10px;
        }
        .activity-feed::-webkit-scrollbar { width: 8px; }
        .activity-feed::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 4px; }
        .activity-feed::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 4px; }

        .feed-item {
            padding: 12px 15px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .feed-avatar { font-size: 1.5em; }
        .feed-content { flex: 1; }
        .feed-message { color: #fff; }
        .feed-time { opacity: 0.4; font-size: 0.8em; }
        .feed-item.type-action { border-left: 3px solid #ffaa00; }
        .feed-item.type-success { border-left: 3px solid #00ff88; }
        .feed-item.type-handoff { border-left: 3px solid #00d9ff; }
        .feed-item.type-system { border-left: 3px solid #fff; }
        .feed-item.type-error { border-left: 3px solid #ff4444; }

        /* Pulse animation for working agents */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .agent-desk.working .agent-avatar {
            animation: pulse 1.5s infinite;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .task-form { flex-direction: column; }
            .task-form input[type="text"], .task-form select, .task-form button {
                width: 100%;
            }
            .office-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="office-container">
        <header>
            <h1>🏢 AI Company Virtual Office</h1>
            <p>Watch your AI team collaborate in real-time</p>
        </header>

        <div class="task-input-section">
            <h2>📋 Assign New Task</h2>
            <form class="task-form" id="taskForm">
                <input type="text" id="taskInput" placeholder="Describe the task..." required>
                <select id="taskType">
                    <option value="full_stack">Full Stack</option>
                    <option value="research">Research</option>
                    <option value="architecture">Architecture</option>
                    <option value="devops">DevOps</option>
                    <option value="documentation">Documentation</option>
                </select>
                <button type="submit" id="submitBtn">🚀 Start</button>
            </form>
        </div>

        <div class="office-grid" id="officeGrid">
            <!-- Agent desks will be rendered here -->
        </div>

        <div class="activity-section">
            <h2>📢 Activity Feed</h2>
            <div class="activity-feed" id="activityFeed">
                <!-- Activity items will be rendered here -->
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://' + window.location.host + '/ws');
        let agents = {};

        ws.onopen = () => {
            console.log('Connected to office hub');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'init') {
                agents = data.data.agents;
                renderOffice();
                renderActivity(data.data.events);
            } else if (data.type === 'agent_update') {
                updateAgent(data.data);
            } else if (data.type === 'agent_message') {
                addActivity(data.data);
            }
        };

        function renderOffice() {
            const grid = document.getElementById('officeGrid');
            grid.innerHTML = '';

            for (const [key, agent] of Object.entries(agents)) {
                const desk = document.createElement('div');
                desk.className = `agent-desk ${agent.status}`;
                desk.id = `desk-${key}`;
                desk.innerHTML = `
                    <div class="agent-header">
                        <div class="agent-avatar">${agent.avatar}</div>
                        <div class="agent-info">
                            <h3>${agent.display_name}</h3>
                            <p>${agent.role}</p>
                        </div>
                    </div>
                    <div class="agent-status status-${agent.status}">${agent.status.toUpperCase()}</div>
                    <div class="agent-task" style="${agent.current_task ? '' : 'display:none'}">
                        <div class="agent-task-label">Current Task:</div>
                        <div class="agent-task-text">${agent.current_task || ''}</div>
                    </div>
                    <div class="agent-message" style="${agent.message && agent.status !== 'idle' ? '' : 'display:none'}">
                        ${agent.message}
                    </div>
                `;
                grid.appendChild(desk);
            }
        }

        function updateAgent(data) {
            const { agent, status, task, message } = data;
            if (agents[agent]) {
                agents[agent].status = status;
                if (task) agents[agent].current_task = task;
                if (message) agents[agent].message = message;
            }
            renderOffice();
        }

        function renderActivity(events) {
            const feed = document.getElementById('activityFeed');
            feed.innerHTML = '';
            events.forEach(event => {
                if (event.type === 'agent_message') {
                    addFeedItem(event.data);
                }
            });
        }

        function addActivity(data) {
            addFeedItem(data);
        }

        function addFeedItem(data) {
            const feed = document.getElementById('activityFeed');
            const item = document.createElement('div');
            item.className = `feed-item type-${data.type}`;
            const time = new Date().toLocaleTimeString();
            item.innerHTML = `
                <div class="feed-avatar">${agents[data.agent]?.avatar || '🤖'}</div>
                <div class="feed-content">
                    <div class="feed-message"><strong>${agents[data.agent]?.display_name || data.agent}</strong>: ${data.message}</div>
                    <div class="feed-time">${time}</div>
                </div>
            `;
            feed.insertBefore(item, feed.firstChild);
        }

        // Task form submission
        document.getElementById('taskForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const taskInput = document.getElementById('taskInput');
            const taskType = document.getElementById('taskType');
            const submitBtn = document.getElementById('submitBtn');

            const task = {
                description: taskInput.value,
                type: taskType.value
            };

            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Starting...';

            try {
                const response = await fetch('/api/task', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(task)
                });
                const result = await response.json();
                if (result.status === 'started') {
                    taskInput.value = '';
                }
            } catch (err) {
                console.error('Error submitting task:', err);
            }

            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Start';
        });
    </script>
</body>
</html>"""
