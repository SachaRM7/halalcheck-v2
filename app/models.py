from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

HalalStatus = Literal["halal", "haram", "dubious", "unknown"]


class ProductCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    barcode: str = Field(..., min_length=8, max_length=32)
    name: str
    brand: Optional[str] = None
    ingredients: str = ""
    halal_status: HalalStatus = "unknown"
    certification_body: Optional[str] = None
    cert_number: Optional[str] = None
    source_url: Optional[HttpUrl] = None


class RestaurantCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    name: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    cuisine_type: Optional[str] = None
    halal_status: HalalStatus = "unknown"


class ReviewCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    photo_url: Optional[HttpUrl] = None


class TrackerCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    product_barcode: str
    consumed_at: Optional[datetime] = None


class AlertCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    product_barcode: str


class PendingContributionOut(BaseModel):
    id: int
    type: str
    payload: dict
    user_id: int
    submitted_at: str
    approvals: int
    rejected: bool
