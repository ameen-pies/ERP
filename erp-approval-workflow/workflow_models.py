from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ApprovalRole(str, Enum):
    INITIATOR = "initiator"
    TECHNICAL_REVIEWER = "technical_reviewer"
    FINANCIAL_APPROVER = "financial_approver"
    DEPARTMENT_MANAGER = "department_manager"
    PURCHASING_MANAGER = "purchasing_manager"
    GENERAL_MANAGER = "general_manager"

class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    DELEGATE = "delegate"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    COMPLETED = "completed"

class DocumentType(str, Enum):
    PURCHASE_REQUISITION = "purchase_requisition"
    PURCHASE_ORDER = "purchase_order"
    CONTRACT = "contract"
    EXPENSE_REPORT = "expense_report"

class ApprovalStep(BaseModel):
    step_id: str
    role: ApprovalRole
    assigned_to: str
    assigned_name: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    action: Optional[ApprovalAction] = None
    comments: str = ""
    action_date: Optional[str] = None
    deadline: str
    order: int

class ApprovalWorkflow(BaseModel):
    workflow_id: str
    document_type: DocumentType
    document_id: str
    document_title: str
    initiator: str
    initiator_name: str
    department: str
    total_amount: Optional[float] = None
    current_step: int = 0
    overall_status: ApprovalStatus = ApprovalStatus.PENDING
    steps: List[ApprovalStep] = []
    created_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_date: str = Field(default_factory=lambda: datetime.now().isoformat())

class ApprovalActionRequest(BaseModel):
    workflow_id: str
    step_id: str
    action: ApprovalAction
    comments: str = ""
    delegate_to: Optional[str] = None

class Comment(BaseModel):
    comment_id: str = ""
    workflow_id: str
    author: str
    author_name: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class WorkflowCreate(BaseModel):
    document_type: DocumentType
    document_id: str
    document_title: str
    initiator: str
    initiator_name: str
    department: str
    total_amount: Optional[float] = None