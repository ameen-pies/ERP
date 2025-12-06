from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GRNLineInput(BaseModel):
    po_line_id: str = Field(..., description="Identifier of the PO line.")
    received_qty: int = Field(default=10, ge=0, description="Quantity received.")
    quality_status: str = Field(
        default="pass", description="Quality status: pass or fail."
    )
    comments: str | None = Field(default=None, description="Optional notes.")


class CreateGRNRequest(BaseModel):
    po_id: str = Field(..., description="Target purchase order.")
    lines: List[GRNLineInput] = Field(
        default_factory=list, description="Lines describing received goods."
    )


class GRNLineUpdate(BaseModel):
    po_line_id: str = Field(..., description="Linked PO line.")
    quality_status: Optional[str] = Field(
        default=None, description="Updated quality status (pass/fail)."
    )
    comments: Optional[str] = Field(default=None, description="Updated comments.")


class UpdateGRNRequest(BaseModel):
    status: Optional[str] = Field(default=None, description="New GRN status.")
    lines: Optional[List[GRNLineUpdate]] = Field(
        default=None, description="Lines with updated metadata."
    )

