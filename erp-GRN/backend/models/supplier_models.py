from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SupplierRequest(BaseModel):
    name: str = Field(..., description="Supplier name.")
    code: Optional[str] = Field(default=None, description="Supplier code.")

