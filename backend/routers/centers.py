from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import LogisticsCenter
from schemas import CenterCreate, CenterUpdate, CenterResponse, CenterGeoJSON
from auth import require_admin, require_any
from geocoding import geocode_address

router = APIRouter()


@router.get("/geojson", response_model=CenterGeoJSON)
async def get_centers_geojson(
    status: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_any),
):
    """지도용 GeoJSON 반환."""
    q = select(LogisticsCenter)
    if status:
        q = q.where(LogisticsCenter.status == status)
    if region:
        q = q.where(LogisticsCenter.region == region)

    result = await db.execute(q)
    centers = result.scalars().all()

    features = []
    for c in centers:
        if c.lat is None or c.lng is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [c.lng, c.lat]},
            "properties": {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "address": c.address,
                "region": c.region,
                "total_area": c.total_area,
                "completion_date": str(c.completion_date) if c.completion_date else None,
            },
        })

    return CenterGeoJSON(features=features)


@router.get("", response_model=list[CenterResponse])
async def list_centers(
    status: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_any),
):
    q = select(LogisticsCenter).order_by(LogisticsCenter.name)
    if status:
        q = q.where(LogisticsCenter.status == status)
    if region:
        q = q.where(LogisticsCenter.region == region)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{center_id}", response_model=CenterResponse)
async def get_center(
    center_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_any),
):
    center = await db.get(LogisticsCenter, center_id)
    if not center:
        raise HTTPException(status_code=404, detail="센터를 찾을 수 없습니다.")
    return center


@router.post("", response_model=CenterResponse, status_code=201)
async def create_center(
    body: CenterCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    lat, lng = body.lat, body.lng
    if lat is None or lng is None:
        coords = await geocode_address(body.address)
        if coords:
            lat, lng = coords

    center = LogisticsCenter(**body.model_dump(exclude={"lat", "lng"}), lat=lat, lng=lng)
    if lat and lng:
        center.geom = text(f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)")
    db.add(center)
    await db.commit()
    await db.refresh(center)
    return center


@router.put("/{center_id}", response_model=CenterResponse)
async def update_center(
    center_id: str,
    body: CenterUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    center = await db.get(LogisticsCenter, center_id)
    if not center:
        raise HTTPException(status_code=404, detail="센터를 찾을 수 없습니다.")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(center, field, value)

    if center.lat and center.lng:
        await db.execute(
            text("UPDATE logistics_centers SET geom = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326) WHERE id = :id"),
            {"lng": center.lng, "lat": center.lat, "id": center_id},
        )

    await db.commit()
    await db.refresh(center)
    return center


@router.delete("/{center_id}", status_code=204)
async def delete_center(
    center_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_admin),
):
    center = await db.get(LogisticsCenter, center_id)
    if not center:
        raise HTTPException(status_code=404, detail="센터를 찾을 수 없습니다.")
    await db.delete(center)
    await db.commit()
