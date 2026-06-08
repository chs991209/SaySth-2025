import aiohttp
import os
import urllib.parse
import ssl
import certifi
from autogen_core.tools import FunctionTool

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


async def search_youtube_videos(query: str, max_results: int = 1) -> dict:
    search_url = (
        "https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&type=video&maxResults={max_results}&q={urllib.parse.quote(query)}&key={YOUTUBE_API_KEY}"
    )
    # SSL 컨텍스트 생성 (certifi 인증서 사용)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(search_url) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Failed to search YouTube: {resp.status} {text}")
            return await resp.json()


search_youtube_tool = FunctionTool(
    search_youtube_videos,
    name="search_youtube_videos",
    description="Searches for videos on YouTube.",
)