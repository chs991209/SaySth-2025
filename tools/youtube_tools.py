import aiohttp
import os
import urllib.parse
from autogen_core.tools import FunctionTool

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


async def search_youtube_videos(query: str, max_results: int = 1) -> dict:
    search_url = (
        "https://www.googleapis.com/youtube/v3/search?"
        f"part=snippet&type=video&maxResults={max_results}&q={urllib.parse.quote(query)}&key={YOUTUBE_API_KEY}"
    )
    async with aiohttp.ClientSession() as session:
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


# from typing_extensions import Annotated
# import base64
# import json
# import mcp
# from mcp.client.streamable_http import streamablehttp_client
# from dotenv import load_dotenv
# import os
# import urllib.parse
# import traceback
#
# load_dotenv()
#
# YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY")
#
#
# async def search_youtube_videos(
#         query: Annotated[str, "Search query for YouTube videos"],
# ) -> dict:
#     config = {
#         "youtubeApiKey": YOUTUBE_API_KEY,
#         "youtubeTranscriptLang": "ko"
#     }
#
#     config_b64 = base64.urlsafe_b64encode(json.dumps(config).encode()).decode()
#     url = f"https://server.smithery.ai/@jikime/py-mcp-youtube-toolbox/mcp?config={urllib.parse.quote(config_b64)}&api_key={urllib.parse.quote(SMITHERY_API_KEY)}"
#
#     async with streamablehttp_client(url) as (read_stream, write_stream, _):
#         async with mcp.ClientSession(read_stream, write_stream) as session:
#             await session.initialize()
#             print(query)
#             print("Available tools:")
#             for tool in await session.list_tools():
#                 print("o")
#                 # print(f"- {tool}", flush=False)  # should list 'searchVideos'
#
#             try:
#                 result = await session.call_tool(name="search_videos", arguments= dict({"query": query, "max_results": 1}))
#                 # print("MCP result:", result)
#                 return result
#             except Exception as e:
#                 traceback.print_exc()
#                 print(f"Error calling MCP tool: {e}")
#                 raise
#
#
