import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Integer, BigInteger,
    Float, Date, DateTime, UniqueConstraint, CheckConstraint, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class LogisticsCenter(Base):
    __tablename__ = "logistics_centers"

    id                  = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name                = Column(Text, nullable=False)
    status              = Column(Text, nullable=False, default="운영중")
    address             = Column(Text, nullable=False, unique=True)
    lat                 = Column(Float)
    lng                 = Column(Float)
    geom                = Column(Geometry("POINT", srid=4326))
    region              = Column(Text)
    total_area          = Column(Float)
    net_leasable_area   = Column(Float)
    floors_above        = Column(Integer)
    floors_below        = Column(Integer)
    dock_count          = Column(Integer)
    ceiling_height      = Column(Float)
    completion_date     = Column(Date)
    developer           = Column(Text)
    note                = Column(Text)
    created_at          = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at          = Column(DateTime(timezone=True), default=datetime.utcnow)

    leases              = relationship("LeaseContract", back_populates="center", cascade="all, delete-orphan")
    vacancy_records     = relationship("VacancyRecord", back_populates="center", cascade="all, delete-orphan")
    transactions        = relationship("Transaction", back_populates="center", cascade="all, delete-orphan")


class Tenant(Base):
    __tablename__ = "tenants"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_name    = Column(Text, nullable=False)
    industry        = Column(Text)
    business_type   = Column(Text)
    contact_name    = Column(Text)
    contact_phone   = Column(Text)
    contact_email   = Column(Text)
    credit_grade    = Column(Text)
    note            = Column(Text)
    created_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at      = Column(DateTime(timezone=True), default=datetime.utcnow)

    leases          = relationship("LeaseContract", back_populates="tenant")


class LeaseContract(Base):
    __tablename__ = "lease_contracts"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    center_id       = Column(UUID(as_uuid=False), ForeignKey("logistics_centers.id", ondelete="CASCADE"), nullable=False)
    tenant_id       = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="SET NULL"))
    floor           = Column(Text)
    unit_name       = Column(Text)
    lease_area      = Column(Float)
    lease_start     = Column(Date)
    lease_end       = Column(Date)
    monthly_rent    = Column(BigInteger)
    rent_per_sqm    = Column(Float)
    deposit         = Column(BigInteger)
    rent_free_months = Column(Integer, default=0)
    contract_status = Column(Text, default="계약중")
    note            = Column(Text)
    created_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at      = Column(DateTime(timezone=True), default=datetime.utcnow)

    center          = relationship("LogisticsCenter", back_populates="leases")
    tenant          = relationship("Tenant", back_populates="leases")


class VacancyRecord(Base):
    __tablename__ = "vacancy_records"
    __table_args__ = (UniqueConstraint("center_id", "record_year", "record_month"),)

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    center_id       = Column(UUID(as_uuid=False), ForeignKey("logistics_centers.id", ondelete="CASCADE"), nullable=False)
    record_year     = Column(Integer, nullable=False)
    record_month    = Column(Integer, nullable=False)
    total_area      = Column(Float)
    occupied_area   = Column(Float)
    vacant_area     = Column(Float)
    vacancy_rate    = Column(Float)
    note            = Column(Text)
    created_at      = Column(DateTime(timezone=True), default=datetime.utcnow)

    center          = relationship("LogisticsCenter", back_populates="vacancy_records")


class Transaction(Base):
    __tablename__ = "transactions"

    id              = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    center_id       = Column(UUID(as_uuid=False), ForeignKey("logistics_centers.id", ondelete="CASCADE"), nullable=False)
    deal_date       = Column(Date)
    deal_type       = Column(Text, default="매매")
    price           = Column(BigInteger)
    price_per_sqm   = Column(Float)
    buyer           = Column(Text)
    seller          = Column(Text)
    cap_rate        = Column(Float)
    noi             = Column(BigInteger)
    note            = Column(Text)
    created_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at      = Column(DateTime(timezone=True), default=datetime.utcnow)

    center          = relationship("LogisticsCenter", back_populates="transactions")
