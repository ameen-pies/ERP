from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class POLineInput(BaseModel):
    item_name: str = Field(
        default="Test Item", description="Item description for the PO line."
    )
    qty_ordered: int = Field(
        default=10, ge=1, description="Quantity requested for this item."
    )
    unit_price: float = Field(
        default=5.0, ge=0.01, description="Unit price for the ordered item."
    )


class CreatePORequest(BaseModel):
    supplier: str = Field(
        default="ACME Supplier", description="Supplier providing the PO."
    )
    lines: List[POLineInput] = Field(
        default_factory=list, description="List of PO line items."
    )


class AddPOLineRequest(BaseModel):
    item_name: str = Field(default="Additional Item", description="Item name.")
    qty_ordered: int = Field(
        default=5, ge=1, description="Additional quantity to order."
    )
    unit_price: float = Field(default=4.5, ge=0.01, description="Unit price.")


class POLineUpdate(BaseModel):
    line_id: str | None = Field(default=None, description="Line identifier.")
    item_name: str = Field(default="Test Item", description="Item name.")
    qty_ordered: int = Field(default=10, ge=0, description="Requested qty.")
    unit_price: float = Field(default=5.0, ge=0.01, description="Unit price.")


class UpdatePORequest(BaseModel):
    supplier: str | None = Field(default=None, description="Supplier name.")
    lines: Optional[List[POLineUpdate]] = Field(
        default=None, description="Lines to replace current PO lines."
    )

