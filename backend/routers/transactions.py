from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Transaction
from schemas import TransactionCreate, TransactionUpdate, TransactionResponse
from auth import require_admin, require_any

router = APIRouter()


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    center_id: str = Query(None),
    deal_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_any),
):
    q = select(Transaction).order_by(Transaction.deal_date.desc())
    if center_id:
        q = q.where(Transaction.center_id == center_id)
    if deal_type:
        q = q.where(Transaction.deal_type == deal_type)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{tx_id}", response_model=TransactionResponse)
async def get_transaction(tx_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_any)):
    tx = await db.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="거래 정보를 찾을 수 없습니다.")
    return tx


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(body: TransactionCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    tx = Transaction(**body.model_dump())
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


@router.put("/{tx_id}", response_model=TransactionResponse)
async def update_transaction(tx_id: str, body: TransactionUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    tx = await db.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="거래 정보를 찾을 수 없습니다.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    await db.commit()
    await db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=204)
async def delete_transaction(tx_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    tx = await db.get(Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="거래 정보를 찾을 수 없습니다.")
    await db.delete(tx)
    await db.commit()
