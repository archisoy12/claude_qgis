from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import VacancyRecord
from schemas import VacancyCreate, VacancyResponse
from auth import require_admin, require_any

router = APIRouter()


@router.get("", response_model=list[VacancyResponse])
async def list_vacancy(
    center_id: str = Query(None),
    year: int = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_any),
):
    q = select(VacancyRecord).order_by(VacancyRecord.record_year, VacancyRecord.record_month)
    if center_id:
        q = q.where(VacancyRecord.center_id == center_id)
    if year:
        q = q.where(VacancyRecord.record_year == year)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=VacancyResponse, status_code=201)
async def create_vacancy(body: VacancyCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    # 공실면적 없으면 자동 계산
    data = body.model_dump()
    if data.get("total_area") and data.get("occupied_area") and data.get("vacant_area") is None:
        data["vacant_area"] = data["total_area"] - data["occupied_area"]
    if data.get("total_area") and data.get("vacant_area") and data.get("vacancy_rate") is None:
        data["vacancy_rate"] = round(data["vacant_area"] / data["total_area"] * 100, 2)

    record = VacancyRecord(**data)
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
async def delete_vacancy(record_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    record = await db.get(VacancyRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="공실률 기록을 찾을 수 없습니다.")
    await db.delete(record)
    await db.commit()
