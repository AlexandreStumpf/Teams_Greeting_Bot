import uuid
from typing import Dict, List, Optional, Set
from datetime import datetime

from botbuilder.core import TurnContext, ActivityHandler, MessageFactory
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount, ConversationReference
from azure.identity import ClientSecretCredential
from aws_lambda_powertools import Logger

from config.settings import settings
from models.schemas import (
    ParticipantInfo, MeetingInfo, GreetingRequest, 
    AudioResponse, BotActivity, ParticipantRole
)
from services.openai_service import openai_service

logger = Logger()


class TeamsService:
    """Service for handling Microsoft Teams meeting operations."""
    
    def __init__(self):
        self.active_meetings: Dict[str, MeetingInfo] = {}
        self.participant_cache: Dict[str, Set[str]] = {}  # meeting_id -> participant_ids
        self.conversation_references: Dict[str, ConversationReference] = {}
    
    async def handle_meeting_join(self, meeting_id: str, participant: ParticipantInfo) -> None:
        """Handle when a participant joins a meeting."""
        
        try:
            logger.info("Participant joined meeting", 
                       meeting_id=meeting_id, 
                       participant=participant.display_name)
            
            # Initialize meeting if not exists
            if meeting_id not in self.active_meetings:
                self.active_meetings[meeting_id] = MeetingInfo(
                    meeting_id=meeting_id,
                    organizer_id="unknown",  # Will be updated when available
                    started_at=datetime.utcnow()
                )
                self.participant_cache[meeting_id] = set()
            
            meeting = self.active_meetings[meeting_id]
            
            # Check if this is a new participant (not rejoining)
            is_new_participant = participant.id not in self.participant_cache[meeting_id]
            
            if is_new_participant:
                # Add to participant cache
                self.participant_cache[meeting_id].add(participant.id)
                meeting.participants.append(participant)
                
                # Generate and play greeting audio
                await self._generate_and_play_greeting(meeting_id, participant)
                
                # Log activity
                await self._log_bot_activity(
                    meeting_id=meeting_id,
                    activity_type="participant_joined",
                    participant_id=participant.id,
                    metadata={"participant_name": participant.display_name}
                )
            
        except Exception as e:
            logger.error("Failed to handle meeting join", 
                        meeting_id=meeting_id,
                        participant=participant.display_name,
                        error=str(e))
    
    async def handle_meeting_leave(self, meeting_id: str, participant_id: str) -> None:
        """Handle when a participant leaves a meeting."""
        
        try:
            logger.info("Participant left meeting", 
                       meeting_id=meeting_id, 
                       participant_id=participant_id)
            
            if meeting_id in self.active_meetings:
                meeting = self.active_meetings[meeting_id]
                
                # Remove from participant cache
                if meeting_id in self.participant_cache:
                    self.participant_cache[meeting_id].discard(participant_id)
                
                # Remove from participants list
                meeting.participants = [
                    p for p in meeting.participants if p.id != participant_id
                ]
                
                # Log activity
                await self._log_bot_activity(
                    meeting_id=meeting_id,
                    activity_type="participant_left",
                    participant_id=participant_id
                )
                
                # Clean up meeting if empty
                if not meeting.participants:
                    await self._cleanup_meeting(meeting_id)
            
        except Exception as e:
            logger.error("Failed to handle meeting leave", 
                        meeting_id=meeting_id,
                        participant_id=participant_id,
                        error=str(e))
    
    async def _generate_and_play_greeting(self, meeting_id: str, participant: ParticipantInfo) -> None:
        """Generate greeting audio and play it in the meeting."""
        
        try:
            # Create greeting request
            greeting_request = GreetingRequest(
                participant_name=participant.display_name,
                language=settings.default_greeting_language
            )
            
            # Generate audio using OpenAI
            audio_response = await openai_service.generate_greeting_audio(greeting_request)
            
            # Play audio in meeting (this would require real-time media capabilities)
            await self._play_audio_in_meeting(meeting_id, audio_response)
            
            logger.info("Greeting played successfully", 
                       meeting_id=meeting_id,
                       participant=participant.display_name,
                       audio_duration=audio_response.duration_seconds)
            
        except Exception as e:
            logger.error("Failed to generate and play greeting", 
                        meeting_id=meeting_id,
                        participant=participant.display_name,
                        error=str(e))
    
    async def _play_audio_in_meeting(self, meeting_id: str, audio_response: AudioResponse) -> None:
        """Play audio in Teams meeting. This is a placeholder for actual audio streaming."""
        
        # NOTE: Playing audio in Teams meetings requires:
        # 1. Real-time media capabilities registration in Bot Framework
        # 2. Establishing media streams with Teams service
        # 3. Using Teams Real-time Media Platform
        
        logger.info("Playing audio in meeting", 
                   meeting_id=meeting_id,
                   audio_url=audio_response.audio_url,
                   text=audio_response.text_content)
        
        # For now, this is a placeholder. In a real implementation, you would:
        # 1. Convert the audio file to appropriate format for Teams
        # 2. Stream the audio using Teams Real-time Media APIs
        # 3. Handle audio mixing with existing meeting audio
        
        # Placeholder implementation - send text message instead
        if meeting_id in self.conversation_references:
            conversation_ref = self.conversation_references[meeting_id]
            message = MessageFactory.text(f"🎵 {audio_response.text_content}")
            # await self._send_proactive_message(conversation_ref, message)
    
    async def _send_proactive_message(self, conversation_ref: ConversationReference, message: Activity) -> None:
        """Send proactive message to Teams conversation."""
        
        # This would require the bot adapter to send proactive messages
        # Implementation depends on the specific bot framework setup
        pass
    
    async def _log_bot_activity(self, meeting_id: str, activity_type: str, 
                               participant_id: Optional[str] = None, 
                               metadata: Optional[Dict] = None) -> None:
        """Log bot activity for monitoring and debugging."""
        
        activity = BotActivity(
            activity_id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            activity_type=activity_type,
            participant_id=participant_id,
            metadata=metadata or {}
        )
        
        logger.info("Bot activity logged", 
                   activity_type=activity_type,
                   meeting_id=meeting_id,
                   participant_id=participant_id,
                   metadata=metadata)
    
    async def _cleanup_meeting(self, meeting_id: str) -> None:
        """Clean up meeting data when meeting ends."""
        
        try:
            if meeting_id in self.active_meetings:
                del self.active_meetings[meeting_id]
            
            if meeting_id in self.participant_cache:
                del self.participant_cache[meeting_id]
                
            if meeting_id in self.conversation_references:
                del self.conversation_references[meeting_id]
            
            logger.info("Meeting cleaned up", meeting_id=meeting_id)
            
        except Exception as e:
            logger.error("Failed to cleanup meeting", meeting_id=meeting_id, error=str(e))
    
    async def get_meeting_info(self, meeting_id: str) -> Optional[MeetingInfo]:
        """Get meeting information by ID."""
        return self.active_meetings.get(meeting_id)
    
    async def get_active_meetings(self) -> List[MeetingInfo]:
        """Get list of all active meetings."""
        return list(self.active_meetings.values())
    
    def add_conversation_reference(self, meeting_id: str, conversation_ref: ConversationReference) -> None:
        """Add conversation reference for proactive messaging."""
        self.conversation_references[meeting_id] = conversation_ref


# Global service instance
teams_service = TeamsService() 