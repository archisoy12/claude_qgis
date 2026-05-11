from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import LeaseContract
from schemas import LeaseCreate, LeaseUpdate, LeaseResponse
from auth import require_admin, require_any

router = APIRouter()


@router.get("", response_model=list[LeaseResponse])
async def list_leases(
    center_id: str = Query(None),
    tenant_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_any),
):
    q = select(LeaseContract)
    if center_id:
        q = q.where(LeaseContract.center_id == center_id)
    if tenant_id:
        q = q.where(LeaseContract.tenant_id == tenant_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{lease_id}", response_model=LeaseResponse)
async def get_lease(lease_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_any)):
    lease = await db.get(LeaseContract, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="임대차 계약을 찾을 수 없습니다.")
    return lease


@router.post("", response_model=LeaseResponse, status_code=201)
async def create_lease(body: LeaseCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    lease = LeaseContract(**body.model_dump())
    db.add(lease)
    await db.commit()
    await db.refresh(lease)
    return lease


@router.put("/{lease_id}", response_model=LeaseResponse)
async def update_lease(lease_id: str, body: LeaseUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    lease = await db.get(LeaseContract, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="임대차 계약을 찾을 수 없습니다.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(lease, field, value)
    await db.commit()
    await db.refresh(lease)
    return lease


@router.delete("/{lease_id}", status_code=204)
async def delete_lease(lease_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    lease = await db.get(LeaseContract, lease_id)
    if not lease:
        raise HTTPException(status_code=404, detail="임대차 계약을 찾을 수 없습니다.")
    await db.delete(lease)
    await db.commit()
