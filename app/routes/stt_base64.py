from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import base64
import asyncio
import os

from ..config import model, thread_pool_executor, temp_dir
from ..utils.temp_file import save_audio_tempfile
from ..services.whisper_service import transcribe_audio

router = APIRouter()

@router.post("/stt_base64")
async def transcript_base64(request: Request):
    try:
        data = await request.json()
        audio_base64 = data.get("audio") or data.get("data")
        if not audio_base64:
            raise HTTPException(status_code=400, detail="No audio data provided")

        audio_data = base64.b64decode(audio_base64)
        audio_path = save_audio_tempfile(audio_data, temp_dir)

        try:
            stt_result = await asyncio.get_event_loop().run_in_executor(
                thread_pool_executor, transcribe_audio, model, audio_path
            )
        finally:
            os.remove(audio_path)

        return JSONResponse(content={"text": stt_result["text"]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
