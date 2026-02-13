from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Wallet
class WalletCreate(BaseModel):
    user_id: int

class WalletResponse(BaseModel):
    id: int
    user_id: int
    balance: int  # milli-units
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Ledger
class LedgerEntryResponse(BaseModel):
    id: int
    transaction_id: UUID
    wallet_id: int
    amount: int
    balance_after: int
    entry_type: str
    transaction_type: str
    description: Optional[str] = None
    reference_id: Optional[str] = None
    counterparty_wallet_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    transaction_id: UUID
    entries: List[LedgerEntryResponse]


# Task Reward
class TaskRewardRequest(BaseModel):
    user_id: int
    amount: int  # milli-units
    task_id: int
    description: Optional[str] = None


# P2P Transfer
class P2PTransferRequest(BaseModel):
    from_user_id: int
    to_user_id: int
    amount: int  # milli-units (must be > 0)
    description: Optional[str] = None


# Device
class DeviceCreate(BaseModel):
    device_id: str
    owner_id: int
    device_type: str  # llm_node / sensor_node / hub
    display_name: Optional[str] = None
    topic_prefix: Optional[str] = None

class DeviceUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    topic_prefix: Optional[str] = None

class DeviceResponse(BaseModel):
    id: int
    device_id: str
    owner_id: int
    device_type: str
    display_name: Optional[str] = None
    topic_prefix: Optional[str] = None
    registered_at: datetime
    is_active: bool
    last_heartbeat_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Reward Rate
class RewardRateResponse(BaseModel):
    id: int
    device_type: str
    rate_per_hour: int
    min_uptime_for_reward: int

    class Config:
        from_attributes = True

class RewardRateUpdate(BaseModel):
    rate_per_hour: int
    min_uptime_for_reward: Optional[int] = None


# Supply
class SupplyResponse(BaseModel):
    total_issued: int
    total_burned: int
    circulating: int

    class Config:
        from_attributes = True


# History pagination
class HistoryParams(BaseModel):
    limit: int = 50
    offset: int = 0
