from pydantic import BaseModel
from typing import Optional, List

class Task(BaseModel):
    """Task model for voice announcement."""
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    bounty_gold: int = 10
    urgency: int = 2  # 0-4
    zone: Optional[str] = None

class SynthesizeRequest(BaseModel):
    """Request model for direct text-to-speech synthesis."""
    text: str

class TaskAnnounceRequest(BaseModel):
    """Request model for task announcement."""
    task: Task

class VoiceResponse(BaseModel):
    """Response model for voice generation."""
    audio_url: str
    text_generated: str
    duration_seconds: float

class DualVoiceResponse(BaseModel):
    """Response model for dual voice generation (announcement + completion)."""
    announcement_audio_url: str
    announcement_text: str
    announcement_duration: float
    completion_audio_url: str
    completion_text: str
    completion_duration: float
