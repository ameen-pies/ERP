
from typing import List, Dict, Any, Optional
from workflow_models import *

class WorkflowConfiguration:
    def __init__(self):
        self.department_configs = self._load_default_configs()
    
    def _load_default_configs(self) -> List[WorkflowConfig]:
        return [
            WorkflowConfig(
                department="IT",
                document_type=DocumentType.PURCHASE_REQUISITION,
                amount_ranges=[
                    {"min": 0, "max": 1000, "approvers": [
                        ApprovalRole.DEPARTMENT_MANAGER
                    ]},
                    {"min": 1000, "max": 5000, "approvers": [
                        ApprovalRole.DEPARTMENT_MANAGER,
                        ApprovalRole.FINANCIAL_APPROVER
                    ]},
                    {"min": 5000, "max": 20000, "approvers": [
                        ApprovalRole.DEPARTMENT_MANAGER,
                        ApprovalRole.FINANCIAL_APPROVER,
                        ApprovalRole.PURCHASING_MANAGER
                    ]},
                    {"min": 20000, "max": float('inf'), "approvers": [
                        ApprovalRole.DEPARTMENT_MANAGER,
                        ApprovalRole.FINANCIAL_APPROVER,
                        ApprovalRole.PURCHASING_MANAGER,
                        ApprovalRole.GENERAL_MANAGER
                    ]}
                ],
                required_approvers=[],
                auto_assign_rules={
                    "technical_reviewer": {"department": "IT", "role": "Technical Lead"},
                    "financial_approver": {"department": "Finance", "role": "Financial Controller"}
                }
            ),
            WorkflowConfig(
                department="HR",
                document_type=DocumentType.PURCHASE_REQUISITION,
                amount_ranges=[
                    {"min": 0, "max": 2000, "approvers": [
                        ApprovalRole.DEPARTMENT_MANAGER
                    ]},
                    {"min": 2000, "max": 10000, "approvers": [
                        ApprovalRole.DEPARTMENT_MANAGER,
                        ApprovalRole.FINANCIAL_APPROVER
                    ]},
                    {"min": 10000, "max": float('inf'), "approvers": [
                        ApprovalRole.DEPARTMENT_MANAGER,
                        ApprovalRole.FINANCIAL_APPROVER,
                        ApprovalRole.GENERAL_MANAGER
                    ]}
                ],
                required_approvers=[],
                auto_assign_rules={
                    "financial_approver": {"department": "Finance", "role": "Financial Controller"}
                }
            )
        ]
    
    def get_workflow_config(self, department: str, doc_type: DocumentType, amount: float = 0) -> Optional[WorkflowConfig]:
        for config in self.department_configs:
            if config.department == department and config.document_type == doc_type:
                return config
        return None
    
    def get_required_approvers(self, department: str, doc_type: DocumentType, amount: float) -> List[ApprovalRole]:
        config = self.get_workflow_config(department, doc_type, amount)
        if not config:
            return []
        
        for range_config in config.amount_ranges:
            if range_config["min"] <= amount < range_config["max"]:
                return range_config["approvers"]
        
        return []

# Mock user database - in real implementation, this would come from your user management system
MOCK_USERS = {
    "IT": [
        {"user_id": "tech_lead_1", "name": "Alice Tech", "email": "alice@company.com", "role": "Technical Lead", "approval_role": ApprovalRole.TECHNICAL_REVIEWER},
        {"user_id": "it_manager_1", "name": "Bob IT Manager", "email": "bob@company.com", "role": "IT Manager", "approval_role": ApprovalRole.DEPARTMENT_MANAGER}
    ],
    "Finance": [
        {"user_id": "finance_1", "name": "Charlie Finance", "email": "charlie@company.com", "role": "Financial Controller", "approval_role": ApprovalRole.FINANCIAL_APPROVER}
    ],
    "Purchasing": [
        {"user_id": "purchasing_1", "name": "Diana Purchasing", "email": "diana@company.com", "role": "Purchasing Manager", "approval_role": ApprovalRole.PURCHASING_MANAGER}
    ],
    "Management": [
        {"user_id": "gm_1", "name": "Eve General Manager", "email": "eve@company.com", "role": "General Manager", "approval_role": ApprovalRole.GENERAL_MANAGER}
    ]
}

def find_approver_user(department: str, approval_role: ApprovalRole) -> Optional[Dict[str, Any]]:
    for dept, users in MOCK_USERS.items():
        for user in users:
            if user.get("approval_role") == approval_role:
                return user
    return None
