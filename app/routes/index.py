from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/")
async def read_index():
    static_file_path = os.path.join("static", "index.html")
    return FileResponse(static_file_path)
