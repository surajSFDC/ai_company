"""Approval queue for human-in-the-loop."""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class ApprovalType(Enum):
    CODE_REVIEW = "code_review"
    TESTS_READY = "tests_ready"
    DEPLOYMENT = "deployment"
    FINAL_OUTPUT = "final_output"
    CUSTOM = "custom"


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """A request for human approval"""

    id: str
    approval_type: ApprovalType
    title: str
    description: str
    content: str
    task_id: str
    requested_at: datetime = field(default_factory=datetime.now)
    responded_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_notes: str = ""
    response: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


class ApprovalQueue:
    """Queue for managing human approvals"""

    def __init__(
        self,
        auto_approve: bool = False,
        timeout_seconds: int = 3600,
        on_approval_callback: Optional[Callable] = None,
    ):
        self.auto_approve = auto_approve
        self.timeout_seconds = timeout_seconds
        self.on_approval_callback = on_approval_callback

        self.requests: Dict[str, ApprovalRequest] = {}
        self.pending_queue: List[str] = []
        self.history: List[ApprovalRequest] = []

    def create_request(
        self,
        approval_type: ApprovalType,
        title: str,
        description: str,
        content: str,
        task_id: str,
        context: Dict[str, Any] = None,
    ) -> str:
        """Create a new approval request"""
        request_id = str(uuid.uuid4())[:8]

        request = ApprovalRequest(
            id=request_id,
            approval_type=approval_type,
            title=title,
            description=description,
            content=content,
            task_id=task_id,
            context=context or {},
        )

        self.requests[request_id] = request
        self.pending_queue.append(request_id)

        if self.auto_approve:
            self.approve(request_id, skip=True)

        return request_id

    def get_pending(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return [self.requests[rid] for rid in self.pending_queue]

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific approval request"""
        return self.requests.get(request_id)

    def approve(self, request_id: str, skip: bool = False, notes: str = "") -> bool:
        """Approve a request"""
        request = self.requests.get(request_id)
        if not request:
            return False

        if skip:
            request.status = ApprovalStatus.SKIPPED
            request.response = "skipped"
        else:
            request.status = ApprovalStatus.APPROVED
            request.response = "approved"

        request.responded_at = datetime.now()
        request.reviewer_notes = notes

        if request_id in self.pending_queue:
            self.pending_queue.remove(request_id)

        self.history.append(request)

        if self.on_approval_callback:
            self.on_approval_callback(request)

        return True

    def reject(self, request_id: str, reason: str = "") -> bool:
        """Reject a request"""
        request = self.requests.get(request_id)
        if not request:
            return False

        request.status = ApprovalStatus.REJECTED
        request.response = "rejected"
        request.responded_at = datetime.now()
        request.reviewer_notes = reason

        if request_id in self.pending_queue:
            self.pending_queue.remove(request_id)

        self.history.append(request)

        if self.on_approval_callback:
            self.on_approval_callback(request)

        return True

    def get_pending_count(self) -> int:
        """Get count of pending approvals"""
        return len(self.pending_queue)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of approval queue"""
        return {
            "pending": len(self.pending_queue),
            "total_requests": len(self.requests),
            "approved": len(
                [r for r in self.history if r.status == ApprovalStatus.APPROVED]
            ),
            "rejected": len(
                [r for r in self.history if r.status == ApprovalStatus.REJECTED]
            ),
            "skipped": len(
                [r for r in self.history if r.status == ApprovalStatus.SKIPPED]
            ),
        }

