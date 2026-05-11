import io
import re
import asyncio
from datetime import date, datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import LogisticsCenter, Tenant, LeaseContract, VacancyRecord, Transaction
from schemas import UploadResult
from auth import require_admin
from geocoding import geocode_address

router = APIRouter()


@router.post("/preview-columns")
async def preview_columns(file: UploadFile = File(...), _=Depends(require_admin)):
    """엑셀 파일의 헤더 컬럼명 목록 반환 (매핑 UI용)."""
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content), nrows=0)
    return list(df.columns.str.strip())


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _parse_date(val) -> Optional[date]:
    if pd.isna(val):
        return None
    if isinstance(val, (date, datetime)):
        return val if isinstance(val, date) else val.date()
    s = re.sub(r"[.\-/년월일\s]", "-", str(val)).strip("-")
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(s[:len(fmt)], fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(val) -> Optional[float]:
    if pd.isna(val):
        return None
    return float(re.sub(r"[,\s%㎡]", "", str(val)))


def _parse_int(val) -> Optional[int]:
    v = _parse_float(val)
    return int(v) if v is not None else None


async def _get_center_map(db: AsyncSession) -> dict[str, str]:
    """address → id 매핑 테이블 반환."""
    result = await db.execute(select(LogisticsCenter.address, LogisticsCenter.id))
    return {row.address: row.id for row in result}


# ── 물류센터 (공급 / 공급예정) ─────────────────────────────────────────────────

@router.post("/centers", response_model=UploadResult)
async def upload_centers(
    file: UploadFile = File(...),
    status: str = Form("운영중"),
    col_address: str = Form("대지위치"),
    col_name: str = Form("센터명"),
    col_region: str = Form("지역"),
    col_total_area: str = Form("연면적"),
    col_net_area: str = Form("임대가능면적"),
    col_floors: str = Form("지상층수"),
    col_dock: str = Form("도크수"),
    col_ceiling: str = Form("층고"),
    col_completion: str = Form("준공일"),
    col_developer: str = Form("개발사"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    df = pd.read_excel(await file.read())
    df.columns = df.columns.str.strip()

    success, failed, errors = 0, 0, []

    for i, row in df.iterrows():
        try:
            address = str(row[col_address]).strip()
            if not address or address == "nan":
                raise ValueError("대지위치 없음")

            existing = await db.execute(
                select(LogisticsCenter).where(LogisticsCenter.address == address)
            )
            center = existing.scalar_one_or_none()

            lat = lng = None
            coords = await geocode_address(address)
            if coords:
                lat, lng = coords
            await asyncio.sleep(0.1)

            data = dict(
                name=str(row.get(col_name, address)).strip(),
                status=status,
                address=address,
                lat=lat,
                lng=lng,
                region=row.get(col_region) if col_region in df.columns else None,
                total_area=_parse_float(row.get(col_total_area)) if col_total_area in df.columns else None,
                net_leasable_area=_parse_float(row.get(col_net_area)) if col_net_area in df.columns else None,
                floors_above=_parse_int(row.get(col_floors)) if col_floors in df.columns else None,
                dock_count=_parse_int(row.get(col_dock)) if col_dock in df.columns else None,
                ceiling_height=_parse_float(row.get(col_ceiling)) if col_ceiling in df.columns else None,
                completion_date=_parse_date(row.get(col_completion)) if col_completion in df.columns else None,
                developer=str(row.get(col_developer, "")).strip() or None,
            )

            if center:
                for k, v in data.items():
                    if v is not None:
                        setattr(center, k, v)
            else:
                center = LogisticsCenter(**data)
                db.add(center)

            await db.commit()
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"행 {i+2}: {e}")

    return UploadResult(success=success, failed=failed, errors=errors)


# ── 임차사 ────────────────────────────────────────────────────────────────────

@router.post("/tenants", response_model=UploadResult)
async def upload_tenants(
    file: UploadFile = File(...),
    col_company: str = Form("임차사명"),
    col_industry: str = Form("업종"),
    col_business: str = Form("사업유형"),
    col_contact: str = Form("담당자"),
    col_phone: str = Form("연락처"),
    col_email: str = Form("이메일"),
    col_grade: str = Form("신용등급"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    df = pd.read_excel(await file.read())
    df.columns = df.columns.str.strip()
    success, failed, errors = 0, 0, []

    for i, row in df.iterrows():
        try:
            company = str(row[col_company]).strip()
            existing = await db.execute(select(Tenant).where(Tenant.company_name == company))
            tenant = existing.scalar_one_or_none()

            data = dict(
                company_name=company,
                industry=row.get(col_industry) if col_industry in df.columns else None,
                business_type=row.get(col_business) if col_business in df.columns else None,
                contact_name=row.get(col_contact) if col_contact in df.columns else None,
                contact_phone=row.get(col_phone) if col_phone in df.columns else None,
                contact_email=row.get(col_email) if col_email in df.columns else None,
                credit_grade=row.get(col_grade) if col_grade in df.columns else None,
            )

            if tenant:
                for k, v in data.items():
                    if v is not None:
                        setattr(tenant, k, v)
            else:
                db.add(Tenant(**data))

            await db.commit()
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"행 {i+2}: {e}")

    return UploadResult(success=success, failed=failed, errors=errors)


# ── 임대료 ────────────────────────────────────────────────────────────────────

@router.post("/leases", response_model=UploadResult)
async def upload_leases(
    file: UploadFile = File(...),
    col_address: str = Form("대지위치"),
    col_tenant: str = Form("임차사명"),
    col_floor: str = Form("층"),
    col_unit: str = Form("호실"),
    col_area: str = Form("임대면적"),
    col_start: str = Form("임대시작일"),
    col_end: str = Form("임대종료일"),
    col_rent: str = Form("월임대료"),
    col_rent_sqm: str = Form("임대료/㎡"),
    col_deposit: str = Form("보증금"),
    col_status: str = Form("계약상태"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    df = pd.read_excel(await file.read())
    df.columns = df.columns.str.strip()
    center_map = await _get_center_map(db)
    success, failed, errors = 0, 0, []

    for i, row in df.iterrows():
        try:
            address = str(row[col_address]).strip()
            center_id = center_map.get(address)
            if not center_id:
                raise ValueError(f"센터 미등록: {address}")

            tenant_id = None
            if col_tenant in df.columns:
                t = await db.execute(select(Tenant).where(Tenant.company_name == str(row[col_tenant]).strip()))
                t_obj = t.scalar_one_or_none()
                tenant_id = t_obj.id if t_obj else None

            db.add(LeaseContract(
                center_id=center_id,
                tenant_id=tenant_id,
                floor=str(row.get(col_floor, "")).strip() or None,
                unit_name=str(row.get(col_unit, "")).strip() or None,
                lease_area=_parse_float(row.get(col_area)) if col_area in df.columns else None,
                lease_start=_parse_date(row.get(col_start)) if col_start in df.columns else None,
                lease_end=_parse_date(row.get(col_end)) if col_end in df.columns else None,
                monthly_rent=_parse_int(row.get(col_rent)) if col_rent in df.columns else None,
                rent_per_sqm=_parse_float(row.get(col_rent_sqm)) if col_rent_sqm in df.columns else None,
                deposit=_parse_int(row.get(col_deposit)) if col_deposit in df.columns else None,
                contract_status=str(row.get(col_status, "계약중")).strip(),
            ))
            await db.commit()
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"행 {i+2}: {e}")

    return UploadResult(success=success, failed=failed, errors=errors)


# ── 공실률 ────────────────────────────────────────────────────────────────────

@router.post("/vacancy", response_model=UploadResult)
async def upload_vacancy(
    file: UploadFile = File(...),
    col_address: str = Form("대지위치"),
    col_year: str = Form("연도"),
    col_month: str = Form("월"),
    col_total: str = Form("전체면적"),
    col_occupied: str = Form("임대면적"),
    col_vacant: str = Form("공실면적"),
    col_rate: str = Form("공실률"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    df = pd.read_excel(await file.read())
    df.columns = df.columns.str.strip()
    center_map = await _get_center_map(db)
    success, failed, errors = 0, 0, []

    for i, row in df.iterrows():
        try:
            address = str(row[col_address]).strip()
            center_id = center_map.get(address)
            if not center_id:
                raise ValueError(f"센터 미등록: {address}")

            total    = _parse_float(row.get(col_total)) if col_total in df.columns else None
            occupied = _parse_float(row.get(col_occupied)) if col_occupied in df.columns else None
            vacant   = _parse_float(row.get(col_vacant)) if col_vacant in df.columns else None
            rate     = _parse_float(row.get(col_rate)) if col_rate in df.columns else None

            if total and occupied and vacant is None:
                vacant = total - occupied
            if total and vacant and rate is None:
                rate = round(vacant / total * 100, 2)

            db.add(VacancyRecord(
                center_id=center_id,
                record_year=int(row[col_year]),
                record_month=int(row[col_month]),
                total_area=total,
                occupied_area=occupied,
                vacant_area=vacant,
                vacancy_rate=rate,
            ))
            await db.commit()
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"행 {i+2}: {e}")

    return UploadResult(success=success, failed=failed, errors=errors)


# ── 거래 정보 ─────────────────────────────────────────────────────────────────

@router.post("/transactions", response_model=UploadResult)
async def upload_transactions(
    file: UploadFile = File(...),
    col_address: str = Form("대지위치"),
    col_date: str = Form("거래일"),
    col_type: str = Form("거래유형"),
    col_price: str = Form("거래금액"),
    col_price_sqm: str = Form("단가/㎡"),
    col_buyer: str = Form("매수인"),
    col_seller: str = Form("매도인"),
    col_cap: str = Form("Cap Rate"),
    col_noi: str = Form("NOI"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    df = pd.read_excel(await file.read())
    df.columns = df.columns.str.strip()
    center_map = await _get_center_map(db)
    success, failed, errors = 0, 0, []

    for i, row in df.iterrows():
        try:
            address = str(row[col_address]).strip()
            center_id = center_map.get(address)
            if not center_id:
                raise ValueError(f"센터 미등록: {address}")

            db.add(Transaction(
                center_id=center_id,
                deal_date=_parse_date(row.get(col_date)) if col_date in df.columns else None,
                deal_type=str(row.get(col_type, "매매")).strip(),
                price=_parse_int(row.get(col_price)) if col_price in df.columns else None,
                price_per_sqm=_parse_float(row.get(col_price_sqm)) if col_price_sqm in df.columns else None,
                buyer=str(row.get(col_buyer, "")).strip() or None,
                seller=str(row.get(col_seller, "")).strip() or None,
                cap_rate=_parse_float(row.get(col_cap)) if col_cap in df.columns else None,
                noi=_parse_int(row.get(col_noi)) if col_noi in df.columns else None,
            ))
            await db.commit()
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"행 {i+2}: {e}")

    return UploadResult(success=success, failed=failed, errors=errors)


# ── 원본 데이터 다운로드 (admin only) ─────────────────────────────────────────

@router.get("/export/{table}")
async def export_table(
    table: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    allowed = {"centers", "tenants", "leases", "vacancy", "transactions"}
    if table not in allowed:
        raise HTTPException(status_code=400, detail="잘못된 테이블명입니다.")

    model_map = {
        "centers": LogisticsCenter,
        "tenants": Tenant,
        "leases": LeaseContract,
        "vacancy": VacancyRecord,
        "transactions": Transaction,
    }

    result = await db.execute(select(model_map[table]))
    rows = result.scalars().all()

    records = [
        {c.name: getattr(row, c.name) for c in row.__table__.columns if c.name != "geom"}
        for row in rows
    ]
    df = pd.DataFrame(records)

    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={table}.xlsx"},
    )
