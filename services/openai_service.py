import os
import tempfile
import uuid
from pathlib import Path

from openai import AsyncOpenAI
from aws_lambda_powertools import Logger

from config.settings import settings
from models.schemas import GreetingRequest, AudioResponse

logger = Logger()


class OpenAIService:
    """Service for OpenAI text-to-speech operations."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Always use /tmp for Lambda environment
        self.temp_dir = Path("/tmp") / "teams_bot_audio"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def generate_greeting_text(self, greeting_request: GreetingRequest) -> str:
        """Generate greeting text based on participant name and language."""
        
        if greeting_request.custom_message:
            return greeting_request.custom_message.format(name=greeting_request.participant_name)
        
        # Default greeting messages by language
        greetings = {
            "pt-BR": f"Bom dia, {greeting_request.participant_name}",
            "en-US": f"Good morning, {greeting_request.participant_name}",
            "es-ES": f"Buenos días, {greeting_request.participant_name}",
            "fr-FR": f"Bonjour, {greeting_request.participant_name}",
        }
        
        return greetings.get(greeting_request.language, greetings["pt-BR"])
    
    async def generate_speech_audio(self, text: str, voice: str = "alloy") -> AudioResponse:
        """Generate speech audio from text using OpenAI TTS."""
        
        try:
            logger.info("Generating speech audio", text=text, voice=voice)
            
            # Generate unique filename
            audio_id = str(uuid.uuid4())
            audio_file_path = self.temp_dir / f"{audio_id}.mp3"
            
            # Create speech using OpenAI TTS
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            
            # Save audio to file
            audio_file_path.write_bytes(response.content)
            
            # Calculate approximate duration (rough estimate: ~150 words per minute)
            word_count = len(text.split())
            duration_seconds = max(1.0, (word_count / 150) * 60)
            
            logger.info("Speech audio generated successfully", 
                       audio_file=str(audio_file_path), 
                       duration=duration_seconds)
            
            return AudioResponse(
                audio_url=f"file://{audio_file_path}",
                duration_seconds=duration_seconds,
                text_content=text
            )
            
        except Exception as e:
            logger.error("Failed to generate speech audio", error=str(e), text=text)
            raise
    
    async def generate_greeting_audio(self, greeting_request: GreetingRequest) -> AudioResponse:
        """Generate complete greeting audio from request."""
        
        try:
            # Generate greeting text
            greeting_text = await self.generate_greeting_text(greeting_request)
            
            # Select appropriate voice based on language
            voice_mapping = {
                "pt-BR": "alloy",  # Good for Portuguese
                "en-US": "echo",   # Good for English
                "es-ES": "fable",  # Good for Spanish
                "fr-FR": "onyx",   # Good for French
            }
            
            selected_voice = voice_mapping.get(greeting_request.language, "alloy")
            
            # Generate audio
            audio_response = await self.generate_speech_audio(greeting_text, selected_voice)
            
            logger.info("Greeting audio generated", 
                       participant=greeting_request.participant_name,
                       language=greeting_request.language,
                       text=greeting_text)
            
            return audio_response
            
        except Exception as e:
            logger.error("Failed to generate greeting audio", 
                        participant=greeting_request.participant_name,
                        error=str(e))
            raise
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> None:
        """Clean up temporary audio files older than specified hours."""
        
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for audio_file in self.temp_dir.glob("*.mp3"):
                file_age = current_time - audio_file.stat().st_mtime
                if file_age > max_age_seconds:
                    audio_file.unlink()
                    logger.debug("Cleaned up old audio file", file=str(audio_file))
                    
        except Exception as e:
            logger.error("Failed to cleanup temp files", error=str(e))


# Global service instance
openai_service = OpenAIService() 