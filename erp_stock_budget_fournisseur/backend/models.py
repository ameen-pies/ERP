"""
Modèles Pydantic pour validation MongoDB
"""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

# ==================== ENUMS ====================

class SupplierStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"

class BudgetStatus(str, Enum):
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"

class MovementType(str, Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"

# ==================== PYDANTIC MODELS (Validation) ====================

class SupplierBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    tax_id: str = Field(..., min_length=5, max_length=50)
    category: str = Field(..., min_length=2)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: str
    status: str
    compliance_checked: bool
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BudgetBase(BaseModel):
    department: str = Field(..., min_length=2)
    allocated: float = Field(..., gt=0)
    used: float = Field(default=0.0, ge=0)

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: str
    available: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BudgetCheckRequest(BaseModel):
    department: str
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=5)
    reference: Optional[str] = None

class BudgetCheckResponse(BaseModel):
    status: BudgetStatus
    reason: Optional[str] = None
    details: Optional[str] = None
    new_available: Optional[float] = None
    transaction_id: Optional[str] = None

class StockItemBase(BaseModel):
    item_id: str = Field(..., min_length=2)
    item_name: str = Field(..., min_length=2)
    quantity: float = Field(default=0.0, ge=0)
    unit: str = Field(default="pcs")
    min_threshold: float = Field(default=10.0, ge=0)
    unit_price: float = Field(default=0.0, ge=0)

class StockItemCreate(StockItemBase):
    pass

class StockItemResponse(StockItemBase):
    id: str
    created_at: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True

class StockMovementBase(BaseModel):
    item_id: str
    quantity: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    movement_type: MovementType = MovementType.IN
    project_id: Optional[str] = None
    reference: Optional[str] = None
    description: Optional[str] = None

class StockMovementCreate(StockMovementBase):
    pass

class StockMovementResponse(BaseModel):
    message: str
    stock_level: float
    accounting_entry: dict
    project_status: str
    movement: dict

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# ==================== HELPER FUNCTIONS ====================

def convert_objectid_to_str(doc: dict) -> dict:
    """Convert MongoDB ObjectId to string in document"""
    if doc and "_id" in doc:
        # Only set id from _id if custom id doesn't exist
        # Otherwise, just remove _id to avoid overwriting the custom id field
        if "id" not in doc:
            doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

def prepare_document_for_insert(data: dict, exclude_id: bool = False) -> dict:
    """Prepare document for MongoDB insert"""
    doc = data.copy()
    if exclude_id and "id" in doc:
        del doc["id"]
    return doc
