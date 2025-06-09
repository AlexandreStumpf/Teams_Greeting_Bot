from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ParticipantRole(str, Enum):
    """Enum for participant roles in Teams meetings."""
    ORGANIZER = "organizer"
    PRESENTER = "presenter"
    ATTENDEE = "attendee"
    PRODUCER = "producer"
    COORGANIZER = "coorganizer"


class ParticipantInfo(BaseModel):
    """Model representing a meeting participant."""
    id: str = Field(..., description="Unique identifier for the participant")
    display_name: str = Field(..., description="Display name of the participant")
    email: Optional[str] = Field(None, description="Email address of the participant")
    role: ParticipantRole = Field(default=ParticipantRole.ATTENDEE, description="Role in the meeting")
    is_muted: bool = Field(default=False, description="Whether participant is muted")
    joined_at: datetime = Field(default_factory=datetime.utcnow, description="When participant joined")


class MeetingInfo(BaseModel):
    """Model representing Teams meeting information."""
    meeting_id: str = Field(..., description="Unique meeting identifier")
    organizer_id: str = Field(..., description="Meeting organizer ID")
    subject: Optional[str] = Field(None, description="Meeting subject/title")
    participants: List[ParticipantInfo] = Field(default_factory=list, description="Current participants")
    started_at: Optional[datetime] = Field(None, description="Meeting start time")


class GreetingRequest(BaseModel):
    """Model for greeting generation requests."""
    participant_name: str = Field(..., description="Name of the participant to greet")
    language: str = Field(default="pt-BR", description="Language for the greeting")
    custom_message: Optional[str] = Field(None, description="Custom greeting message template")


class AudioResponse(BaseModel):
    """Model for audio generation responses."""
    audio_url: str = Field(..., description="URL to the generated audio file")
    duration_seconds: float = Field(..., description="Duration of the audio in seconds")
    text_content: str = Field(..., description="Original text used for audio generation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When audio was generated")


class BotActivity(BaseModel):
    """Model for tracking bot activities and events."""
    activity_id: str = Field(..., description="Unique activity identifier")
    meeting_id: str = Field(..., description="Associated meeting ID")
    activity_type: str = Field(..., description="Type of activity (greeting, join, leave)")
    participant_id: Optional[str] = Field(None, description="Participant associated with activity")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Activity timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional activity metadata")


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error_code: str = Field(..., description="Error code identifier")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp") 