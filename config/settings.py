from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Lambda-optimized settings for Teams Greeting Bot."""
    
    # Microsoft Bot Framework Configuration
    microsoft_app_id: str = Field(..., env="MICROSOFT_APP_ID")
    microsoft_app_password: str = Field(..., env="MICROSOFT_APP_PASSWORD") 
    microsoft_app_tenant_id: str = Field(..., env="MICROSOFT_APP_TENANT_ID")
    
    # Microsoft Graph API Configuration
    graph_client_id: str = Field(..., env="GRAPH_CLIENT_ID")
    graph_client_secret: str = Field(..., env="GRAPH_CLIENT_SECRET")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Bot Configuration
    bot_name: str = Field(default="TeamsGreetingBot", env="BOT_NAME")
    default_greeting_language: str = Field(default="pt-BR", env="DEFAULT_GREETING_LANGUAGE")
    
    class Config:
        case_sensitive = False


# Global settings instance
settings = Settings() 