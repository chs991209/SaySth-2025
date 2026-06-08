from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from autogen_agentchat.ui import Console
from agents.intent import classify_intents_with_keywords
from agents.groupchat import build_agent_teams
from agent_utils.groupchat.groupchat_manager import (
    extract_final_answer,
    format_team_prompt,
)

import time


app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to actual frontend domain(s) if in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/execute")
async def execute_prompt(request: Request):
    """
    프롬프트 실행기
    HTTPS Request로 온 요청을 수행하는 function입니다.
    :param request:
    :return:
    """
    body = await request.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return JSONResponse(content={"error": "Empty prompt"}, status_code=400)

    intent_dicts = await classify_intents_with_keywords(
        prompt
    )  # 의도 및 키워드 분류기 호출부, coroutine 타입의 객체를 반환합니다.
    if len(
        intent_dicts
    ):  # 의도 및 keyword가 인식되지 않으면 다음 step으로 넘어가지 않습니다.
        team_configs = build_agent_teams(
            intent_dicts
        )  # 의도별 액션 생성 team 생성부(SelectorGroupChat 타입의 객체)

        start_time = time.time()  # timer start point timestamp

        actions_list: list[dict[str, str]] = []  # None은 받지 않습니다.
        for config in team_configs:
            intent = config["intent"]
            keywords = config["keywords"]
            team = config["team"]
            await team.reset()  # 순차적 team별 초기화 부분
            team_prompt = format_team_prompt(
                intent, keywords
            )  # 팀 별로 프롬프트를 새로 배치하는 부분
            print(f"[RUNNING TEAM '{intent}'] Prompt: {team_prompt}")
            
            # 각 team이 완료될 때까지 기다림
            try:
                task_result = await Console(
                    team.run_stream(task=team_prompt)
                )  # 액션 생성팀이 작업을 실행하는 부분
                
                # #ACTIONSGENERATIONDONE이 있는지 확인
                messages = getattr(task_result, "messages", [])
                has_actions_done = any(
                    "#ACTIONSGENERATIONDONE" in (
                        msg.content() if callable(getattr(msg, "content", None))
                        else getattr(msg, "content", "")
                    )
                    for msg in messages
                )
                
                if not has_actions_done:
                    print(f"[WARNING] Team '{intent}' did not complete properly - no #ACTIONSGENERATIONDONE found")
                
                action = extract_final_answer(task_result)  # 액션 추출기 호출부
                if action is not None:  # 유의미한 action만 수집합니다.
                    actions_list.append(action)
                else:
                    print(f"[WARNING] Team '{intent}' did not produce a valid action")
            except Exception as e:
                print(f"[ERROR] Team '{intent}' encountered an error: {e}")
                # 에러가 발생해도 다음 team 계속 실행

        end_time = time.time()  # timer end point timestamp
        print(f"[GroupChat session duration] {end_time - start_time:.2f} seconds")

        if len(actions_list):  # 유의미한 action이 생성돼야 응답합니다(액션이 없을 시
            return JSONResponse(content={"actions_list": actions_list})

        return JSONResponse(content={"error": "No actions found"}, status_code=500)

    return JSONResponse(content={"error": "Intent not recognized"}, status_code=400)


@app.post("/execute-voice-command")
async def execute_voice_prompt(request: Request):
    """
    음성 명령 실행기
    ASR 서버를 통해 변환된 텍스트를 받아 액션을 생성하는 function입니다.
    :param request:
    :return:
    """
    body = await request.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return JSONResponse(content={"error": "Empty prompt"}, status_code=400)

    intent_dicts = await classify_intents_with_keywords(
        prompt
    )  # 의도 및 키워드 분류기 호출부, coroutine 타입의 객체를 반환합니다.
    if len(
        intent_dicts
    ):  # 의도 및 keyword가 인식되지 않으면 다음 step으로 넘어가지 않습니다.
        team_configs = build_agent_teams(
            intent_dicts
        )  # 의도별 액션 생성 team 생성부(SelectorGroupChat 타입의 객체)

        start_time = time.time()  # timer start point timestamp

        actions_list: list[dict[str, str]] = []  # None은 받지 않습니다.
        for config in team_configs:
            intent = config["intent"]
            keywords = config["keywords"]
            team = config["team"]
            await team.reset()  # 순차적 team별 초기화 부분
            team_prompt = format_team_prompt(
                intent, keywords
            )  # 팀 별로 프롬프트를 새로 배치하는 부분
            print(f"[RUNNING TEAM '{intent}'] Prompt: {team_prompt}")
            
            # 각 team이 완료될 때까지 기다림
            try:
                task_result = await Console(
                    team.run_stream(task=team_prompt)
                )  # 액션 생성팀이 작업을 실행하는 부분
                
                # #ACTIONSGENERATIONDONE이 있는지 확인
                messages = getattr(task_result, "messages", [])
                has_actions_done = any(
                    "#ACTIONSGENERATIONDONE" in (
                        msg.content() if callable(getattr(msg, "content", None))
                        else getattr(msg, "content", "")
                    )
                    for msg in messages
                )
                
                if not has_actions_done:
                    print(f"[WARNING] Team '{intent}' did not complete properly - no #ACTIONSGENERATIONDONE found")
                
                action = extract_final_answer(task_result)  # 액션 추출기 호출부
                if action is not None:  # 유의미한 action만 수집합니다.
                    actions_list.append(action)
                else:
                    print(f"[WARNING] Team '{intent}' did not produce a valid action")
            except Exception as e:
                print(f"[ERROR] Team '{intent}' encountered an error: {e}")
                # 에러가 발생해도 다음 team 계속 실행

        end_time = time.time()  # timer end point timestamp
        print(f"[GroupChat session duration] {end_time - start_time:.2f} seconds")

        if len(actions_list):  # 유의미한 action이 생성돼야 응답합니다(액션이 없을 시
            return JSONResponse(content={"actions_list": actions_list})

        return JSONResponse(content={"error": "No actions found"}, status_code=500)

    return JSONResponse(content={"error": "Intent not recognized"}, status_code=400)
