import os
import tempfile
import torch
import whisper
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


forced_temp_root = "C:\\temp"
os.makedirs(forced_temp_root, exist_ok=True)
temp_dir_manager = tempfile.TemporaryDirectory(dir=forced_temp_root)
temp_dir = temp_dir_manager.name


device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")


model = whisper.load_model("turbo").to(device)


thread_pool_executor = ThreadPoolExecutor(max_workers=os.cpu_count() * 2)

@asynccontextmanager
async def lifespan(app):
    logger.info("App started")
    yield
    logger.info("App ended")
    temp_dir_manager.cleanup()
    thread_pool_executor.shutdown()
