import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.future import select
from database import engine, AsyncSessionLocal, Base
from routers import tasks, users, voice_events
import models # Make sure models are registered

logger = logging.getLogger(__name__)

app = FastAPI(title="SOMS Dashboard API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _migrate_add_columns(conn):
    """Add missing columns to existing tables (stopgap until Alembic)."""
    inspector = inspect(conn)
    existing = {col["name"] for col in inspector.get_columns("tasks")}

    migrations = [
        ("assigned_to", "INTEGER"),
        ("accepted_at", "TIMESTAMP WITH TIME ZONE"),
    ]
    for col_name, col_type in migrations:
        if col_name not in existing:
            conn.execute(text(
                f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"
            ))
            logger.info("Migrated: added column tasks.%s", col_name)


# Startup Event
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        # Add columns that create_all cannot add to existing tables
        await conn.run_sync(_migrate_add_columns)

    # Seed default user if none exist
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(models.User))
        if not result.scalars().first():
            session.add(models.User(username="guest", display_name="ゲスト"))
            await session.commit()

# Include Routers
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(voice_events.router)

@app.get("/")
async def root():
    return {"message": "SOMS Dashboard API Running"}
