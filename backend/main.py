"""
Vocalis Backend Server

FastAPI application entry point.
"""

import logging
import uvicorn
from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import configuration
from . import config

# Import services
from .services.transcription import WhisperTranscriber
from .services.llm import LLMClient
from .services.tts import TTSClient
from .services.vision import vision_service
from . import dependencies as deps

# Import routes
from .routes.websocket import websocket_endpoint
from .routes.twilio import router as twilio_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Vision service is a singleton already initialized in its module

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the FastAPI application.
    """
    # Load configuration
    cfg = config.get_config()
    
    # Initialize services on startup
    logger.info("Initializing services...")
    
    # Initialize transcription service
    deps.transcription_service = WhisperTranscriber(
        model_size=cfg["whisper_model"],
        sample_rate=cfg["audio_sample_rate"]
    )
    
    # Initialize LLM service
    deps.llm_service = LLMClient(
        api_endpoint=cfg["llm_api_endpoint"]
    )
    
    # Initialize TTS service
    deps.tts_service = TTSClient(
        api_endpoint=cfg["tts_api_endpoint"],
        model=cfg["tts_model"],
        voice=cfg["tts_voice"],
        output_format=cfg["tts_format"]
    )
    
    # Initialize vision service (will download model if not cached)
    logger.info("Initializing vision service...")
    vision_service.initialize()
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down services...")
    
    # No specific cleanup needed for these services,
    # but we could add resource release code here if needed (maybe in a future release lex 31/03/25)
    
    logger.info("Shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Vocalis Backend",
    description="Speech-to-Speech AI Assistant Backend",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Twilio webhook routes
app.include_router(twilio_router)


# API routes
@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "Vocalis backend is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "services": {
            "transcription": deps.transcription_service is not None,
            "llm": deps.llm_service is not None,
            "tts": deps.tts_service is not None,
            "vision": vision_service.is_ready()
        },
        "config": {
            "whisper_model": config.WHISPER_MODEL,
            "tts_voice": config.TTS_VOICE,
            "websocket_port": config.WEBSOCKET_PORT
        }
    }

@app.get("/config")
async def get_full_config():
    """Get full configuration."""
    if not all([deps.transcription_service, deps.llm_service, deps.tts_service]) or not vision_service.is_ready():
        raise HTTPException(status_code=503, detail="Services not initialized")

    return {
        "transcription": deps.transcription_service.get_config(),
        "llm": deps.llm_service.get_config(),
        "tts": deps.tts_service.get_config(),
        "system": config.get_config()
    }

# WebSocket route
@app.websocket("/ws")
async def websocket_route(
    websocket: WebSocket,
    transcriber: WhisperTranscriber = Depends(deps.get_transcription_service),
    llm_client: LLMClient = Depends(deps.get_llm_service),
    tts_client: TTSClient = Depends(deps.get_tts_service),
):
    """WebSocket endpoint for bidirectional audio streaming."""
    await websocket_endpoint(
        websocket,
        transcriber,
        llm_client,
        tts_client,
    )

# Run server directly if executed as script
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=config.WEBSOCKET_HOST,
        port=config.WEBSOCKET_PORT,
        reload=True
    )
