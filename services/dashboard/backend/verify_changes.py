from models import Task
from schemas import TaskBase

# Check if fields exist in Model
assert hasattr(Task, 'announcement_audio_url')
assert hasattr(Task, 'announcement_text')
assert hasattr(Task, 'completion_audio_url')
assert hasattr(Task, 'completion_text')

# Check if fields exist in Schema
# Pydantic models use .__fields__ 
assert 'announcement_audio_url' in TaskBase.model_fields
assert 'announcement_text' in TaskBase.model_fields
assert 'completion_audio_url' in TaskBase.model_fields
assert 'completion_text' in TaskBase.model_fields

print("Verification Successful: Voice fields are present in Model and Schema.")
