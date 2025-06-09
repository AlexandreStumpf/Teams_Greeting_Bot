from typing import List, Dict, Any

from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import (
    Activity, ActivityTypes, ChannelAccount, ConversationReference,
    TeamsChannelAccount, TeamsMeetingParticipant
)
from aws_lambda_powertools import Logger

from models.schemas import ParticipantInfo, ParticipantRole
from services.teams_service import teams_service
from services.openai_service import openai_service

logger = Logger()


class TeamsGreetingBot(ActivityHandler):
    """Main Teams bot class for handling meeting events and greetings."""
    
    def __init__(self):
        super().__init__()
        self.conversation_references: Dict[str, ConversationReference] = {}
    
    async def on_message_activity(self, turn_context: TurnContext) -> None:
        """Handle incoming messages."""
        
        try:
            message_text = turn_context.activity.text.strip().lower() if turn_context.activity.text else ""
            
            # Handle bot commands
            if message_text.startswith("/"):
                await self._handle_bot_command(turn_context, message_text)
            else:
                # Echo the message for testing
                response_text = f"Olá! Recebi sua mensagem: {turn_context.activity.text}"
                await turn_context.send_activity(MessageFactory.text(response_text))
            
        except Exception as e:
            logger.error("Error handling message activity", error=str(e))
            await turn_context.send_activity(
                MessageFactory.text("Desculpe, ocorreu um erro ao processar sua mensagem.")
            )
    
    async def _handle_bot_command(self, turn_context: TurnContext, command: str) -> None:
        """Handle bot commands."""
        
        try:
            if command == "/help":
                help_text = """
**Comandos disponíveis:**
- `/help` - Mostrar esta ajuda
- `/status` - Status do bot e reuniões ativas
- `/test <nome>` - Testar geração de áudio para um nome
                """
                await turn_context.send_activity(MessageFactory.text(help_text))
                
            elif command == "/status":
                active_meetings = await teams_service.get_active_meetings()
                status_text = f"🤖 Bot ativo\n📊 Reuniões ativas: {len(active_meetings)}"
                
                for meeting in active_meetings:
                    status_text += f"\n- Reunião {meeting.meeting_id}: {len(meeting.participants)} participantes"
                
                await turn_context.send_activity(MessageFactory.text(status_text))
                
            elif command.startswith("/test "):
                name = command[6:].strip()
                if name:
                    await self._test_greeting_generation(turn_context, name)
                else:
                    await turn_context.send_activity(
                        MessageFactory.text("Por favor, forneça um nome: `/test João`")
                    )
            
        except Exception as e:
            logger.error("Error handling bot command", command=command, error=str(e))
            await turn_context.send_activity(
                MessageFactory.text("Erro ao executar comando.")
            )
    
    async def _test_greeting_generation(self, turn_context: TurnContext, name: str) -> None:
        """Test greeting audio generation."""
        
        try:
            from models.schemas import GreetingRequest
            
            await turn_context.send_activity(
                MessageFactory.text(f"🎵 Gerando áudio de saudação para {name}...")
            )
            
            greeting_request = GreetingRequest(participant_name=name)
            audio_response = await openai_service.generate_greeting_audio(greeting_request)
            
            await turn_context.send_activity(
                MessageFactory.text(
                    f"✅ Áudio gerado com sucesso!\n"
                    f"📝 Texto: {audio_response.text_content}\n"
                    f"⏱️ Duração: {audio_response.duration_seconds:.1f}s"
                )
            )
            
        except Exception as e:
            logger.error("Error testing greeting generation", name=name, error=str(e))
            await turn_context.send_activity(
                MessageFactory.text("❌ Erro ao gerar áudio de teste.")
            )
    
    async def on_teams_meeting_participants_join(
        self, 
        meeting_participants_joined: List[TeamsMeetingParticipant],
        meeting_info: Any,  # TeamsMeetingInfo type
        turn_context: TurnContext
    ) -> None:
        """Handle when participants join a Teams meeting."""
        
        try:
            meeting_id = getattr(meeting_info, 'id', 'unknown')
            
            logger.info("Teams meeting participants joined", 
                       meeting_id=meeting_id,
                       participants_count=len(meeting_participants_joined))
            
            for participant in meeting_participants_joined:
                # Convert to our ParticipantInfo model
                participant_info = self._convert_teams_participant(participant)
                
                # Skip bot itself
                if self._is_bot_participant(participant_info):
                    continue
                
                # Handle the join event
                await teams_service.handle_meeting_join(meeting_id, participant_info)
            
        except Exception as e:
            logger.error("Error handling meeting participants join", error=str(e))
    
    async def on_teams_meeting_participants_leave(
        self,
        meeting_participants_left: List[TeamsMeetingParticipant],
        meeting_info: Any,  # TeamsMeetingInfo type
        turn_context: TurnContext
    ) -> None:
        """Handle when participants leave a Teams meeting."""
        
        try:
            meeting_id = getattr(meeting_info, 'id', 'unknown')
            
            logger.info("Teams meeting participants left", 
                       meeting_id=meeting_id,
                       participants_count=len(meeting_participants_left))
            
            for participant in meeting_participants_left:
                participant_id = getattr(participant.user, 'id', 'unknown')
                await teams_service.handle_meeting_leave(meeting_id, participant_id)
            
        except Exception as e:
            logger.error("Error handling meeting participants leave", error=str(e))
    
    def _convert_teams_participant(self, teams_participant: TeamsMeetingParticipant) -> ParticipantInfo:
        """Convert Teams participant to our ParticipantInfo model."""
        
        user = teams_participant.user
        meeting = teams_participant.meeting
        
        # Extract participant information
        participant_id = getattr(user, 'id', 'unknown')
        display_name = getattr(user, 'name', 'Unknown User')
        email = getattr(user, 'user_principal_name', None) or getattr(user, 'email', None)
        
        # Determine role
        role = ParticipantRole.ATTENDEE
        if hasattr(meeting, 'role'):
            role_str = getattr(meeting, 'role', '').lower()
            if role_str in ['organizer', 'coorganizer']:
                role = ParticipantRole.ORGANIZER if role_str == 'organizer' else ParticipantRole.COORGANIZER
            elif role_str == 'presenter':
                role = ParticipantRole.PRESENTER
        
        return ParticipantInfo(
            id=participant_id,
            display_name=display_name,
            email=email,
            role=role,
            is_muted=False  # This would need to be determined from Teams API
        )
    
    def _is_bot_participant(self, participant: ParticipantInfo) -> bool:
        """Check if participant is the bot itself."""
        
        # Bot detection logic - adjust based on your bot's characteristics
        bot_identifiers = [
            'teamsgreetingbot',
            'greeting bot',
            'bot',
            '@bot'
        ]
        
        display_name_lower = participant.display_name.lower()
        return any(identifier in display_name_lower for identifier in bot_identifiers)
    
    async def on_members_added_activity(
        self, 
        members_added: List[ChannelAccount], 
        turn_context: TurnContext
    ) -> None:
        """Handle when the bot is added to a Teams conversation."""
        
        try:
            for member in members_added:
                if member.id != turn_context.activity.recipient.id:
                    # Bot was added by someone else
                    welcome_text = (
                        "👋 Olá! Sou o Bot de Saudações do Teams.\n\n"
                        "Quando adicionado a uma reunião, eu automaticamente:\n"
                        "• Identifico quando novos participantes entram\n"
                        "• Gero uma saudação personalizada com o nome da pessoa\n"
                        "• Reproduzo o áudio para todos ouvirem\n\n"
                        "Digite `/help` para ver comandos disponíveis."
                    )
                    await turn_context.send_activity(MessageFactory.text(welcome_text))
            
        except Exception as e:
            logger.error("Error handling members added", error=str(e))
    
    async def on_turn(self, turn_context: TurnContext) -> None:
        """Process incoming activity."""
        
        # Store conversation reference for proactive messaging
        self._add_conversation_reference(turn_context.activity)
        
        # Call parent implementation
        await super().on_turn(turn_context)
    
    def _add_conversation_reference(self, activity: Activity) -> None:
        """Store conversation reference for proactive messaging."""
        
        conversation_reference = TurnContext.get_conversation_reference(activity)
        conversation_id = conversation_reference.conversation.id
        
        self.conversation_references[conversation_id] = conversation_reference
        
        # Also add to teams service if it's a meeting
        if hasattr(activity, 'channel_data') and activity.channel_data:
            meeting_id = activity.channel_data.get('meeting', {}).get('id')
            if meeting_id:
                teams_service.add_conversation_reference(meeting_id, conversation_reference) 