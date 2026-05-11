from __future__ import annotations
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str

class TokenResponse(BaseModel):
    access_token: str
    role: str  # "admin" | "viewer"


# ── LogisticsCenter ───────────────────────────────────────────────────────────

class CenterBase(BaseModel):
    name: str
    status: str = "운영중"
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    region: Optional[str] = None
    total_area: Optional[float] = None
    net_leasable_area: Optional[float] = None
    floors_above: Optional[int] = None
    floors_below: Optional[int] = None
    dock_count: Optional[int] = None
    ceiling_height: Optional[float] = None
    completion_date: Optional[date] = None
    developer: Optional[str] = None
    note: Optional[str] = None

class CenterCreate(CenterBase):
    pass

class CenterUpdate(CenterBase):
    name: Optional[str] = None
    status: Optional[str] = None
    address: Optional[str] = None

class CenterResponse(CenterBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class CenterGeoJSON(BaseModel):
    type: str = "FeatureCollection"
    features: List[dict]


# ── Tenant ────────────────────────────────────────────────────────────────────

class TenantBase(BaseModel):
    company_name: str
    industry: Optional[str] = None
    business_type: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    credit_grade: Optional[str] = None
    note: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(TenantBase):
    company_name: Optional[str] = None

class TenantResponse(TenantBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── LeaseContract ─────────────────────────────────────────────────────────────

class LeaseBase(BaseModel):
    center_id: str
    tenant_id: Optional[str] = None
    floor: Optional[str] = None
    unit_name: Optional[str] = None
    lease_area: Optional[float] = None
    lease_start: Optional[date] = None
    lease_end: Optional[date] = None
    monthly_rent: Optional[int] = None
    rent_per_sqm: Optional[float] = None
    deposit: Optional[int] = None
    rent_free_months: int = 0
    contract_status: str = "계약중"
    note: Optional[str] = None

class LeaseCreate(LeaseBase):
    pass

class LeaseUpdate(LeaseBase):
    center_id: Optional[str] = None

class LeaseResponse(LeaseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── VacancyRecord ─────────────────────────────────────────────────────────────

class VacancyBase(BaseModel):
    center_id: str
    record_year: int
    record_month: int
    total_area: Optional[float] = None
    occupied_area: Optional[float] = None
    vacant_area: Optional[float] = None
    vacancy_rate: Optional[float] = None
    note: Optional[str] = None

class VacancyCreate(VacancyBase):
    pass

class VacancyResponse(VacancyBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionBase(BaseModel):
    center_id: str
    deal_date: Optional[date] = None
    deal_type: str = "매매"
    price: Optional[int] = None
    price_per_sqm: Optional[float] = None
    buyer: Optional[str] = None
    seller: Optional[str] = None
    cap_rate: Optional[float] = None
    noi: Optional[int] = None
    note: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    center_id: Optional[str] = None

class TransactionResponse(TransactionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResult(BaseModel):
    success: int
    failed: int
    errors: List[str]
