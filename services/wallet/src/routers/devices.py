from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func as sa_func
from typing import List

from database import get_db
from models import Device
from schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse,
    DeviceXpGrantRequest, DeviceXpResponse, DeviceXpStatsResponse,
)
from services.xp_scorer import grant_xp_to_zone, compute_reward_multiplier, find_zone_devices

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


@router.post("/xp-grant", response_model=DeviceXpResponse)
async def xp_grant(body: DeviceXpGrantRequest, db: AsyncSession = Depends(get_db)):
    """Grant XP to all active devices in a zone."""
    devices_awarded, total_xp, device_ids = await grant_xp_to_zone(
        db,
        zone=body.zone,
        task_id=body.task_id,
        xp_amount=body.xp_amount,
        event_type=body.event_type,
    )
    await db.commit()
    return DeviceXpResponse(
        devices_awarded=devices_awarded,
        total_xp_granted=total_xp,
        device_ids=device_ids,
    )


@router.get("/zone-multiplier/{zone}")
async def get_zone_multiplier(zone: str, db: AsyncSession = Depends(get_db)):
    """Get the average reward multiplier for devices in a zone."""
    devices = await find_zone_devices(db, zone)
    if not devices:
        return {"zone": zone, "multiplier": 1.0, "device_count": 0, "avg_xp": 0}

    avg_xp = sum(d.xp for d in devices) / len(devices)
    multiplier = compute_reward_multiplier(int(avg_xp))
    return {
        "zone": zone,
        "multiplier": multiplier,
        "device_count": len(devices),
        "avg_xp": int(avg_xp),
    }
