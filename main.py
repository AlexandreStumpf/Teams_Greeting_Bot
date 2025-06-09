import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from aws_lambda_powertools import Logger

from config.settings import settings
from routers.bot_routes import router as bot_router

# Initialize logger for Lambda
logger = Logger()

# Create FastAPI application optimized for Lambda
app = FastAPI(
    title="Teams Greeting Bot",
    description="Microsoft Teams bot for AWS Lambda",
    version="1.0.0",
    docs_url=None,  # Disabled for Lambda
    redoc_url=None  # Disabled for Lambda
)

# Minimal CORS for Teams
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://teams.microsoft.com", "https://*.teams.microsoft.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for Lambda."""
    
    logger.error("Unhandled exception", 
                error=str(exc),
                path=request.url.path,
                method=request.method)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Lambda execution failed"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    
    return {
        "status": "healthy",
        "service": "Teams Greeting Bot Lambda",
        "version": "1.0.0",
        "environment": "AWS Lambda"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    
    return {
        "service": "Microsoft Teams Greeting Bot",
        "description": "Bot serverless para saudações no Teams",
        "version": "1.0.0",
        "platform": "AWS Lambda"
    }

# Include bot routes
app.include_router(bot_router) 