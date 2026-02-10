from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import tasks, users
import models # Make sure models are registered

app = FastAPI(title="SOMS Dashboard API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

# Include Routers
app.include_router(tasks.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "SOMS Dashboard API Running"}
