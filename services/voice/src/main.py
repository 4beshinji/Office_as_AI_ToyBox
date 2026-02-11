from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from loguru import logger

from models import TaskAnnounceRequest, VoiceResponse, DualVoiceResponse
from voicevox_client import VoicevoxClient
from speech_generator import SpeechGenerator

# Initialize FastAPI app
app = FastAPI(
    title="SOMS Voice Service",
    description="Voice notification service using VOICEVOX and LLM"
)

# Initialize clients
voice_client = VoicevoxClient()
speech_gen = SpeechGenerator()

# Audio storage directory
AUDIO_DIR = Path("/app/audio")
AUDIO_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"service": "SOMS Voice Service", "status": "running"}

@app.post("/api/voice/announce", response_model=VoiceResponse)
async def announce_task(request: TaskAnnounceRequest):
    """
    Generate voice announcement for a task.
    
    Flow:
    1. Generate natural speech text using LLM
    2. Synthesize using VOICEVOX (ナースロボ＿タイプＴ)
    3. Save audio file
    4. Return audio URL and metadata
    """
    try:
        logger.info(f"Announcing task: {request.task.title}")
        
        # 1. Generate natural speech text using LLM
        speech_text = await speech_gen.generate_speech_text(request.task)
        
        # 2. Synthesize using VOICEVOX
        audio_data = await voice_client.synthesize(speech_text)
        
        # 3. Save audio file
        audio_id = str(uuid.uuid4())
        audio_filename = f"task_{audio_id}.mp3"
        audio_path = AUDIO_DIR / audio_filename
        await voice_client.save_audio(audio_data, audio_path)
        
        # 4. Calculate duration (rough estimate based on sample rate)
        # VOICEVOX typically outputs 24kHz, 16-bit mono
        duration_seconds = len(audio_data) / (24000 * 2)  # bytes / (sample_rate * bytes_per_sample)
        
        return VoiceResponse(
            audio_url=f"/audio/{audio_filename}",
            text_generated=speech_text,
            duration_seconds=round(duration_seconds, 2)
        )
        
    except Exception as e:
        logger.error(f"Failed to announce task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/feedback/{feedback_type}")
async def generate_feedback(feedback_type: str):
    """
    Generate feedback message (e.g., task completion acknowledgment).
    
    Args:
        feedback_type: Type of feedback ('task_completed', 'task_accepted')
    """
    try:
        logger.info(f"Generating feedback: {feedback_type}")
        
        # 1. Generate feedback text using LLM
        feedback_text = await speech_gen.generate_feedback(feedback_type)
        
        # 2. Synthesize
        audio_data = await voice_client.synthesize(feedback_text)
        
        # 3. Save
        audio_id = str(uuid.uuid4())
        audio_filename = f"feedback_{audio_id}.mp3"
        audio_path = AUDIO_DIR / audio_filename
        await voice_client.save_audio(audio_data, audio_path)
        
        # 4. Calculate duration
        duration_seconds = len(audio_data) / (24000 * 2)
        
        return VoiceResponse(
            audio_url=f"/audio/{audio_filename}",
            text_generated=feedback_text,
            duration_seconds=round(duration_seconds, 2)
        )
        
    except Exception as e:
        logger.error(f"Failed to generate feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/announce_with_completion", response_model=DualVoiceResponse)
async def announce_task_with_completion(request: TaskAnnounceRequest):
    """
    Generate both announcement and completion voices for a task.
    The completion voice is contextually linked to the task content.
    
    Flow:
    1. Generate announcement text using LLM
    2. Generate contextual completion text using LLM
    3. Synthesize both using VOICEVOX
    4. Save both audio files
    5. Return both audio URLs and metadata
    """
    try:
        logger.info(f"Generating dual voice for task: {request.task.title}")
        
        # 1. Generate announcement text using LLM
        announcement_text = await speech_gen.generate_speech_text(request.task)
        
        # 2. Generate contextual completion text using LLM
        completion_text = await speech_gen.generate_completion_text(request.task)
        
        # 3. Synthesize announcement
        announcement_audio = await voice_client.synthesize(announcement_text)
        
        # 4. Synthesize completion
        completion_audio = await voice_client.synthesize(completion_text)
        
        # 5. Save announcement audio
        announcement_id = str(uuid.uuid4())
        announcement_filename = f"task_announce_{announcement_id}.mp3"
        announcement_path = AUDIO_DIR / announcement_filename
        await voice_client.save_audio(announcement_audio, announcement_path)
        
        # 6. Save completion audio
        completion_id = str(uuid.uuid4())
        completion_filename = f"task_complete_{completion_id}.mp3"
        completion_path = AUDIO_DIR / completion_filename
        await voice_client.save_audio(completion_audio, completion_path)
        
        # 7. Calculate durations
        announcement_duration = len(announcement_audio) / (24000 * 2)
        completion_duration = len(completion_audio) / (24000 * 2)
        
        logger.info(f"Announcement: {announcement_text}")
        logger.info(f"Completion: {completion_text}")
        
        return DualVoiceResponse(
            announcement_audio_url=f"/audio/{announcement_filename}",
            announcement_text=announcement_text,
            announcement_duration=round(announcement_duration, 2),
            completion_audio_url=f"/audio/{completion_filename}",
            completion_text=completion_text,
            completion_duration=round(completion_duration, 2)
        )
        
    except Exception as e:
        logger.error(f"Failed to generate dual voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files."""
    audio_path = AUDIO_DIR / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    
    # We omit the filename argument to default to inline disposition,
    # which is better for web playback in <audio> or Audio objects.
    return FileResponse(
        audio_path, 
        media_type="audio/mpeg"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
