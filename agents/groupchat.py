from agents.registry import (
    user_proxy,
    play_planner,
    open_planner,
    youtube_searcher,
    videoId_extractor,
    url_searcher,
    code_generator_youtube_play,
    code_generator_browser_website_open,
)
from agents.model_clients import model_client03, model_client04
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from typing import List, Sequence

#play_team에 사용될 candidate_func
def play_candidate_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> List[str]:

    #play_planner가 가장 첫번째 실행
    if messages[-1].source == "user":
        return [play_planner.name]
    #마지막 메세지를 기준으로 작업에 참여할 agent 선택
    last_message=messages[-1]
    if last_message.source == play_planner.name:
        participants=[]
        if youtube_searcher.name in last_message.to_text():
            participants.append(youtube_searcher.name)
        if videoId_extractor.name in last_message.to_text():
            participants.append(videoId_extractor.name)
        if participants:
            return participants #planner가 지정한 agent만 리턴
    
    #이미 youbue_searcher와 videoID agent가 사용되었으면 코드 생성 agent 실행
    previous_set_of_agents=set(message.source for message in messages)
    if youtube_searcher.name in previous_set_of_agents and videoId_extractor.name in previous_set_of_agents:
        return [code_generator_youtube_play.name]
    
    #아무런 정보가 없으면 모든 agent 리턴턴
    return [play_planner.name, youtube_searcher.name, videoId_extractor.name, code_generator_youtube_play.name]

#open_team 에서 사용될 candidate func
def open_candidate_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> List[str]:

    #oepn_planner가 가장 첫번째 실행
    if messages[-1].source == "user":
        return [open_planner.name]
    #마지막 메세지를 기준으로 작업에 참여할 agent 선택
    last_message=messages[-1]
    if last_message.source == open_planner.name:
            return [url_searcher.name] #planner가 지정한 agent만 리턴
    
    #이미 url_searcher가 사용되었으면 코드 생성 agent 실행
    previous_set_of_agents=set(message.source for message in messages)
    if url_searcher.name in previous_set_of_agents:
        return [code_generator_browser_website_open.name]
    
    #정보가 없으면 모든 agent 출력
    return [open_planner.name, url_searcher.name, code_generator_browser_website_open]


selector_prompt = """Select an agent to perform task.

{roles}

Current conversation context:
{history}

Read the above conversation, then select an agent from {participants} to perform the next task.
Make sure the planner agent has assigned tasks before other agents start working.
Only select one agent.
"""

text_mention_termination = TextMentionTermination("#CommandDone")
max_messages_termination = MaxMessageTermination(max_messages=25)
termination = text_mention_termination | max_messages_termination

play_team_agents = [
    user_proxy,
    play_planner,
    youtube_searcher,
    videoId_extractor,
    code_generator_youtube_play,
]
open_team_agents = [
    user_proxy,
    open_planner,
    url_searcher,
    code_generator_browser_website_open,
]

play_team = SelectorGroupChat(
    participants=play_team_agents,
    model_client=model_client04,
    selector_prompt=selector_prompt,
    termination_condition=termination,
    candidate_func= play_candidate_func,
)

open_team = SelectorGroupChat(
    participants=open_team_agents,
    model_client=model_client03,
    selector_prompt=selector_prompt,
    termination_condition=termination,
    candidate_func=open_candidate_func,
)

intent_to_groupchat = {
    "play": play_team,
    "open": open_team,
}
