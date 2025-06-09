from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List

from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from aws_lambda_powertools import Logger

from config.settings import settings
from bot.teams_bot import TeamsGreetingBot
from services.teams_service import teams_service
from services.openai_service import openai_service
from models.schemas import (
    GreetingRequest, AudioResponse, MeetingInfo, 
    ParticipantInfo, ErrorResponse
)

logger = Logger()

# Initialize bot and adapter
bot_settings = BotFrameworkAdapterSettings(
    app_id=settings.microsoft_app_id,
    app_password=settings.microsoft_app_password
)
adapter = BotFrameworkAdapter(bot_settings)
bot = TeamsGreetingBot()

# Create router
router = APIRouter(prefix="/api/bot", tags=["bot"])


async def handle_bot_error(context, error):
    """Handle bot framework errors."""
    logger.error("Bot framework error", error=str(error))
    await context.send_activity("Desculpe, ocorreu um erro interno.")


# Set error handler
adapter.on_turn_error = handle_bot_error


@router.post("/messages")
async def bot_messages(request: Request) -> JSONResponse:
    """Main webhook endpoint for Teams bot messages."""
    
    try:
        # Get the raw body and headers
        body = await request.body()
        auth_header = request.headers.get("Authorization", "")
        
        # Create activity from request
        activity = Activity().deserialize(await request.json())
        
        # Process the activity
        await adapter.process_activity(activity, auth_header, bot.on_turn)
        
        return JSONResponse(content={"status": "ok"})
        
    except Exception as e:
        logger.error("Error processing bot message", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_bot_status() -> Dict[str, Any]:
    """Get bot status and active meetings."""
    
    try:
        active_meetings = await teams_service.get_active_meetings()
        
        return {
            "status": "active",
            "bot_name": settings.bot_name,
            "active_meetings_count": len(active_meetings),
            "active_meetings": [
                {
                    "meeting_id": meeting.meeting_id,
                    "participants_count": len(meeting.participants),
                    "started_at": meeting.started_at.isoformat() if meeting.started_at else None
                }
                for meeting in active_meetings
            ]
        }
        
    except Exception as e:
        logger.error("Error getting bot status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get bot status")


@router.get("/meetings")
async def get_active_meetings() -> List[MeetingInfo]:
    """Get list of active meetings."""
    
    try:
        meetings = await teams_service.get_active_meetings()
        return meetings
        
    except Exception as e:
        logger.error("Error getting active meetings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get active meetings")


@router.get("/meetings/{meeting_id}")
async def get_meeting_info(meeting_id: str) -> MeetingInfo:
    """Get information about a specific meeting."""
    
    try:
        meeting = await teams_service.get_meeting_info(meeting_id)
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
            
        return meeting
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting meeting info", meeting_id=meeting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get meeting info")


@router.post("/test/greeting")
async def test_greeting_generation(greeting_request: GreetingRequest) -> AudioResponse:
    """Test endpoint to generate greeting audio."""
    
    try:
        logger.info("Testing greeting generation", participant=greeting_request.participant_name)
        
        audio_response = await openai_service.generate_greeting_audio(greeting_request)
        
        logger.info("Greeting generation test completed", 
                   participant=greeting_request.participant_name,
                   duration=audio_response.duration_seconds)
        
        return audio_response
        
    except Exception as e:
        logger.error("Error testing greeting generation", 
                    participant=greeting_request.participant_name,
                    error=str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate greeting: {str(e)}"
        )


# Cleanup endpoint removed - Lambda handles temp file cleanup automatically


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    
    return {
        "status": "healthy",
        "service": "Teams Greeting Bot",
        "version": "1.0.0"
    } 