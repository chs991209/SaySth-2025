import asyncio
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.teams import RoundRobinGroupChat, MagenticOneGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.ui import Console
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

from autogen_core import CancellationToken
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams

from dotenv import load_dotenv
import os
import requests
from fastapi import FastAPI, Request

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

#stt데이터 주소 (태훈이 집컴)
stt_url = 'https://e169-39-122-179-149.ngrok-free.app/stt'

app = FastAPI()

#텍스트를 통해 에이전트 사용
@app.post("/receive-text")
async def receive_text(request: Request):
    command= (await request.json())['text']
    print(command)
    await main(command)
    return {"message": "successfully get text"," text:":command}

#음성을 통해 에이전트 사용
@app.post("/receive-voice")
async def receive_voice() -> None:
    # 업로드할 음성파일 경로
    file_path = 'audio.wav'

    # 파일 열기
    with open(file_path, 'rb') as f:
        files = {'file': ('audio.wav', f, 'audio/wav')}
        response = requests.post(stt_url, files=files)

    # 응답 처리
    if response.status_code == 200:
        data = response.json()
        command = data.get('text')
        print("받은 텍스트:", command)
    else:
        print("요청 실패:", response.status_code)
        print("응답 내용:", response.text)
    await main(command)

#에이전트 실행 코드
async def main(command) -> None:
    #mcp 서버 연결
    server_params = SseServerParams(
        #mcp 서버에서 만든 로컬 url
        url="http://127.0.0.1:8000/sse",
        headers={"Content-Type":"application/json"},
        timeout=30,
    )

    #mcp 서버의 도구
    adapter_weather= await SseMcpToolAdapter.from_server_params(server_params,"get_weather")
    adapter_blog= await SseMcpToolAdapter.from_server_params(server_params,"search_blog")
    adapter_news= await SseMcpToolAdapter.from_server_params(server_params,"search_news")
    adapter_book= await SseMcpToolAdapter.from_server_params(server_params,"search_book")
    adapter_book_adv= await SseMcpToolAdapter.from_server_params(server_params,"get_book_adv")
    adapter_encyc= await SseMcpToolAdapter.from_server_params(server_params,"search_encyc")
    adapter_cafe= await SseMcpToolAdapter.from_server_params(server_params,"search_cafe_article")
    adapter_kin= await SseMcpToolAdapter.from_server_params(server_params,"search_kin")
    adapter_local= await SseMcpToolAdapter.from_server_params(server_params,"search_local")
    adapter_spelling= await SseMcpToolAdapter.from_server_params(server_params,"fix_spelling")
    adapter_webkr= await SseMcpToolAdapter.from_server_params(server_params,"search_webkr")
    adapter_image= await SseMcpToolAdapter.from_server_params(server_params,"search_image")
    adapter_shop= await SseMcpToolAdapter.from_server_params(server_params,"search_shop")
    adapter_doc= await SseMcpToolAdapter.from_server_params(server_params,"search_doc")

    #ai 모델 연결
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key = API_KEY)
    # The web surfer will open a Chromium browser window to perform web browsing tasks.
    web_surfer = MultimodalWebSurfer("web_surfer", model_client, description="""A helpful assistant with access to a web browser.
    Ask them to perform web searches, open pages, and interact with content (e.g., clicking links, scrolling the viewport, filling in form fields, etc.).
    It can also be asked to sleep and wait for pages to load, in cases where the page seems not yet fully loaded.""", headless=False,start_page="https://www.naver.com/",
        browser_channel="chrome", to_save_screenshots=False)
    # The user proxy agent is used to get user input after each step of the web surfer.
    # NOTE: you can skip input by pressing Enter.
    user_proxy = UserProxyAgent("user_proxy")

    #mcp api(adapter_ㅁㅁ)와 ai 에이전트 연결
    agent = AssistantAgent(
        name="naver_mcp",
        model_client=model_client,
        tools=[
            adapter_weather, 
            adapter_blog,
            adapter_news, 
            adapter_book,
            adapter_book_adv,
            adapter_encyc,
            adapter_cafe,
            adapter_kin,
            adapter_local,
            adapter_spelling,
            adapter_webkr,
            adapter_image,
            adapter_shop,
            adapter_doc
            ],
        system_message="You are a helpful naver api tools, like search, image, information.",
    )

    # The termination condition is set to end the conversation when the user types 'exit'.
    termination = TextMentionTermination("exit", sources=["user_proxy"])
    # Web surfer and user proxy take turns in a round-robin fashion.
    team = MagenticOneGroupChat([agent], termination_condition=termination, model_client=model_client)
    # Start the team and wait for it to terminate.
    await Console(team.run_stream(task=command))
    await web_surfer.close()

