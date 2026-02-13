from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models import Device
from schemas import DeviceCreate, DeviceUpdate, DeviceResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/", response_model=DeviceResponse)
async def register_device(body: DeviceCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Device).filter(Device.device_id == body.device_id)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Device already registered")

    device = Device(
        device_id=body.device_id,
        owner_id=body.owner_id,
        device_type=body.device_type,
        display_name=body.display_name,
        topic_prefix=body.topic_prefix,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device).order_by(Device.registered_at.desc()))
    return result.scalars().all()


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    body: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).filter(Device.device_id == device_id)
    )
    device = result.scalars().first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if body.display_name is not None:
        device.display_name = body.display_name
    if body.is_active is not None:
        device.is_active = body.is_active
    if body.topic_prefix is not None:
        device.topic_prefix = body.topic_prefix

    await db.commit()
    await db.refresh(device)
    return device
