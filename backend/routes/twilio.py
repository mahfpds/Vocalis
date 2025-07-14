from fastapi import APIRouter, Request, WebSocket, Depends
from fastapi.responses import Response
from ..services.transcription import WhisperTranscriber
from ..services.llm import LLMClient
from ..services.tts import TTSClient
from ..dependencies import (
    get_transcription_service,
    get_llm_service,
    get_tts_service,
)
from .. import config
import base64
import json
import numpy as np
import audioop
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TwilioStreamManager:
    """Handle Twilio media stream over WebSocket."""

    def __init__(self, transcriber: WhisperTranscriber, llm: LLMClient, tts: TTSClient):
        self.transcriber = transcriber
        self.llm_client = llm
        self.tts_client = tts
        self.buffer = bytearray()
        self.stream_sid = ""

    async def process_buffer(self, websocket: WebSocket):
        if not self.buffer:
            return
        try:
            pcm = bytes(self.buffer)
            # Twilio streams at 8kHz mu-law. Convert to 16-bit linear PCM.
            pcm_linear = audioop.ulaw2lin(pcm, 2)
            if self.transcriber.sample_rate != 8000:
                pcm_linear, _ = audioop.ratecv(pcm_linear, 2, 1, 8000, self.transcriber.sample_rate, None)
            audio_np = np.frombuffer(pcm_linear, dtype=np.int16)
            text, _ = self.transcriber.transcribe(audio_np)
            if not text.strip():
                self.buffer.clear()
                return
            llm_resp = self.llm_client.get_response(text)
            tts_audio = await self.tts_client.async_text_to_speech(llm_resp["text"])
            if self.transcriber.sample_rate != 8000:
                tts_audio, _ = audioop.ratecv(tts_audio, 2, 1, self.transcriber.sample_rate, 8000, None)
            ulaw = audioop.lin2ulaw(tts_audio, 2)
            payload = base64.b64encode(ulaw).decode("utf-8")
            await websocket.send_text(json.dumps({
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {"payload": payload}
            }))
        except Exception as e:
            logger.error(f"Twilio stream processing error: {e}")
        finally:
            self.buffer.clear()

    async def handle(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                msg = await websocket.receive_text()
                data = json.loads(msg)
                event = data.get("event")
                if event in ("connected", "start"):
                    self.stream_sid = data.get("streamSid", self.stream_sid)
                    greeting = "Hello, welcome to Vocalis. How can I help you?"
                    tts_audio = await self.tts_client.async_text_to_speech(greeting)
                    if self.transcriber.sample_rate != 8000:
                        tts_audio, _ = audioop.ratecv(tts_audio, 2, 1, self.transcriber.sample_rate, 8000, None)
                    ulaw = audioop.lin2ulaw(tts_audio, 2)
                    payload = base64.b64encode(ulaw).decode("utf-8")
                    await websocket.send_text(json.dumps({
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {"payload": payload}
                    }))
                elif event == "media":
                    payload = data.get("media", {}).get("payload")
                    if payload:
                        self.buffer.extend(base64.b64decode(payload))
                        if len(self.buffer) > 8000 * 2:  # ~1s of audio
                            await self.process_buffer(websocket)
                elif event == "stop":
                    await self.process_buffer(websocket)
                    break
        except Exception as e:
            logger.error(f"Twilio websocket error: {e}")
        finally:
            await websocket.close()

@router.post("/twilio/voice")
async def twilio_voice(request: Request):
    """Webhook for Twilio voice calls returning TwiML."""
    ws_url = config.TWILIO_WS_URL
    if not ws_url:
        host = request.headers.get("host")
        ws_url = f"wss://{host}/twilio/ws"
    twiml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<Response><Connect><Stream url=\"" + ws_url + "\"/></Connect></Response>"
    )
    return Response(content=twiml, media_type="text/xml")

@router.websocket("/twilio/ws")
async def twilio_ws(
    websocket: WebSocket,
    transcriber: WhisperTranscriber = Depends(get_transcription_service),
    llm_client: LLMClient = Depends(get_llm_service),
    tts_client: TTSClient = Depends(get_tts_service),
):
    manager = TwilioStreamManager(transcriber, llm_client, tts_client)
    await manager.handle(websocket)
