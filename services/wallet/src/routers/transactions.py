from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from database import get_db
from models import LedgerEntry
from schemas import (
    TaskRewardRequest,
    P2PTransferRequest,
    TransactionResponse,
    LedgerEntryResponse,
)
from services.ledger import transfer, SYSTEM_USER_ID

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/task-reward", response_model=TransactionResponse)
async def task_reward(body: TaskRewardRequest, db: AsyncSession = Depends(get_db)):
    """Pay task bounty from system wallet to user wallet."""
    reference = f"task:{body.task_id}"
    description = body.description or f"Task #{body.task_id} reward"

    try:
        txn_id = await transfer(
            db,
            from_user_id=SYSTEM_USER_ID,
            to_user_id=body.user_id,
            amount=body.amount,
            transaction_type="TASK_REWARD",
            description=description,
            reference_id=reference,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return await _get_transaction(db, txn_id)


@router.post("/p2p-transfer", response_model=TransactionResponse)
async def p2p_transfer(body: P2PTransferRequest, db: AsyncSession = Depends(get_db)):
    """Transfer funds between two user wallets."""
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    try:
        txn_id = await transfer(
            db,
            from_user_id=body.from_user_id,
            to_user_id=body.to_user_id,
            amount=body.amount,
            transaction_type="P2P_TRANSFER",
            description=body.description,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return await _get_transaction(db, txn_id)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: UUID, db: AsyncSession = Depends(get_db)):
    return await _get_transaction(db, transaction_id)


async def _get_transaction(db: AsyncSession, txn_id: UUID) -> TransactionResponse:
    result = await db.execute(
        select(LedgerEntry)
        .filter(LedgerEntry.transaction_id == txn_id)
        .order_by(LedgerEntry.id)
    )
    entries = result.scalars().all()
    if not entries:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse(transaction_id=txn_id, entries=entries)
