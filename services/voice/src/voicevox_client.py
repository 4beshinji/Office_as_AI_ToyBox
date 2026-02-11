import aiohttp
from pathlib import Path
from loguru import logger

class VoicevoxClient:
    """Client for VOICEVOX speech synthesis API."""
    
    # Speaker ID: 47 (ナースロボ＿タイプＴ - ノーマル)
    SPEAKER_ID = 47
    
    def __init__(self, base_url: str = "http://voicevox:50021"):
        self.base_url = base_url
        logger.info(f"VoicevoxClient initialized with base_url: {base_url}")
    
    async def synthesize(
        self, 
        text: str, 
        speaker_id: int = None
    ) -> bytes:
        """
        Synthesize speech using VOICEVOX API.
        
        Args:
            text: Text to synthesize
            speaker_id: Voice character ID (default: ナースロボ＿タイプＴ)
        
        Returns:
            WAV audio data as bytes
        """
        if speaker_id is None:
            speaker_id = self.SPEAKER_ID
            
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Generate audio query
                query_url = f"{self.base_url}/audio_query"
                params = {"text": text, "speaker": speaker_id}
                
                logger.debug(f"Generating audio query for text: {text[:50]}...")
                async with session.post(query_url, params=params) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Audio query failed: {error_text}")
                    query = await resp.json()
                
                # Step 2: Synthesize audio
                synthesis_url = f"{self.base_url}/synthesis"
                params = {"speaker": speaker_id}
                
                logger.debug("Synthesizing audio...")
                async with session.post(
                    synthesis_url, 
                    json=query, 
                    params=params
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Synthesis failed: {error_text}")
                    audio_data = await resp.read()
                
                logger.info(f"Successfully synthesized {len(audio_data)} bytes of audio")
                return audio_data
                
        except Exception as e:
            logger.error(f"VOICEVOX synthesis error: {e}")
            raise
    
    async def save_audio(self, audio_data: bytes, filepath: Path):
        """Save audio data to WAV file."""
        try:
            with open(filepath, "wb") as f:
                f.write(audio_data)
            logger.info(f"Saved audio to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise
