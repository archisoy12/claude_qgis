from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Tenant
from schemas import TenantCreate, TenantUpdate, TenantResponse
from auth import require_admin, require_any

router = APIRouter()


@router.get("", response_model=list[TenantResponse])
async def list_tenants(db: AsyncSession = Depends(get_db), _=Depends(require_any)):
    result = await db.execute(select(Tenant).order_by(Tenant.company_name))
    return result.scalars().all()


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_any)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="임차사를 찾을 수 없습니다.")
    return tenant


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(body: TenantCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    tenant = Tenant(**body.model_dump())
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, body: TenantUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="임차사를 찾을 수 없습니다.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(tenant_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="임차사를 찾을 수 없습니다.")
    await db.delete(tenant)
    await db.commit()
