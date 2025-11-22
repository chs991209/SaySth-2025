from autogen_agentchat.teams import SelectorGroupChat

from agents.intent import merge_keywords_by_intent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination

from agents.registry import (
    user_proxy,
    play_planner,
    open_planner,
    execute_planner,
    youtube_video_searcher,
    url_searcher,
    executable_program_filename_finder,
)

# === TEMPLATE SELECTOR PROMPT: ===

selector_prompt_template = """\
You are managing a team of agent specialists to accomplish a user request.
Each session has a specific intent -- "{intent}" -- and the following keywords:
- {keywords}

Roles in this team:
{roles}

Session requirements:
- The planner agent will break down the user's request into explicit tasks.
- For each keyword, a process agent may be assigned to collect or derive a result.
- Results from all keywords must be gathered, assembled,
  and the planner agent must output ONE JSON dict with the agent's result type as a single key
  and a _list_ of results as value, for example:
  {example_output}

- The planner agent must END the output with "#ACTIONSGENERATIONDONE" (on its own line).

When not yet broken down, always select the planner agent. Only hand off to process agents when a request is clear.
Always select only one agent to speak next.

Which agent should reply next?
"""

# #ACTIONSGENERATIONDONE이 반드시 있어야 종료되도록 설정
# MaxMessageTermination은 안전장치로만 사용 (더 큰 값으로 설정)
termination = TextMentionTermination("#ACTIONSGENERATIONDONE") | MaxMessageTermination(
    500
)


def make_candidate_func(planner_agent, process_agents):
    def candidate_func(messages):
        if messages[-1].source == "user":
            return [planner_agent.name]
        
        last_message = messages[-1]
        msg_text = last_message.to_text()
        
        # #ACTIONSGENERATIONDONE이 있으면 종료 (planner만 반환하여 종료 처리)
        if "#ACTIONSGENERATIONDONE" in msg_text:
            return [planner_agent.name]
        
        # Planner가 메시지를 보낸 경우
        if last_message.source == planner_agent.name:
            # Planner가 process agent를 언급했는지 확인
            mentioned_agents = []
            for agent in process_agents:
                if agent.name in msg_text:
                    mentioned_agents.append(agent.name)
            
            if mentioned_agents:
                # 언급된 agent들이 응답해야 함
                return mentioned_agents
            
            # Planner가 최종 결과를 출력했는지 확인 (JSON 형식)
            if "{" in msg_text and "}" in msg_text:
                # 이미 결과를 출력했지만 #ACTIONSGENERATIONDONE이 없으면 planner에게 다시 요청
                return [planner_agent.name]
        
        # Process agent가 응답한 경우, planner로 돌아가기
        if last_message.source in [agent.name for agent in process_agents]:
            return [planner_agent.name]
        
        # 기본적으로 planner와 아직 응답하지 않은 process agents 반환
        agents_already_turn = set(msg.source for msg in messages)
        remaining_agents = [
            agent.name
            for agent in process_agents
            if agent.name not in agents_already_turn
        ]
        
        # 아직 응답하지 않은 agent가 있으면 그들을 우선, 없으면 planner
        if remaining_agents:
            return [planner_agent.name] + remaining_agents
        else:
            return [planner_agent.name]

    return candidate_func


def build_play_team(keywords):
    roles = """
- user_proxy: presents the original query/judges completion.
- PlayPlannerAgent: coordinates below agents and builds the final JSON output.
- YouTubeVideoSearcherAgent: uses the search_youtube_videos tool to find videoId for each keyword.
"""
    example_output = (
        '{{"open_webbrowser": [ "https://www.youtube.com/watch?v=xxx", ... ]}}'
    )
    agents = [user_proxy, play_planner, youtube_video_searcher]
    prompt = selector_prompt_template.format(
        intent="play",
        keywords=", ".join(keywords),
        roles=roles,
        example_output=example_output,
    )
    return SelectorGroupChat(
        participants=agents,
        model_client=play_planner._model_client,
        selector_prompt=prompt,
        termination_condition=termination,
        candidate_func=make_candidate_func(play_planner, agents[2:]),
    )


def build_open_team(keywords):
    roles = """
- user_proxy: presents the original query/judges completion.
- OpenPlannerAgent: coordinates below agents and builds the final JSON output.
- SuggestionWebsiteUrlSearchAgent: determines the best URL for each keyword/topic.
"""
    example_output = '{{"open_webbrowser": [ "https://...", ... ]}}'
    agents = [user_proxy, open_planner, url_searcher]
    prompt = selector_prompt_template.format(
        intent="open",
        keywords=", ".join(keywords),
        roles=roles,
        example_output=example_output,
    )
    return SelectorGroupChat(
        participants=agents,
        model_client=open_planner._model_client,
        selector_prompt=prompt,
        termination_condition=termination,
        candidate_func=make_candidate_func(open_planner, agents[2:]),
    )


def build_execute_team(keywords):
    roles = """
- user_proxy: presents the original query/judges completion.
- ExecutePlannerAgent: coordinates below agent and builds the final JSON output.
- ExecuteProgramsParameterAgent: resolves executable file names for each program keyword.
"""
    example_output = '{{"execute_programs": [ "Photoshop.exe", "Excel.exe", ... ]}}'
    agents = [user_proxy, execute_planner, executable_program_filename_finder]
    prompt = selector_prompt_template.format(
        intent="execute",
        keywords=", ".join(keywords),
        roles=roles,
        example_output=example_output,
    )
    return SelectorGroupChat(
        participants=agents,
        model_client=execute_planner._model_client,
        selector_prompt=prompt,
        termination_condition=termination,
        candidate_func=make_candidate_func(
            execute_planner, [executable_program_filename_finder]
        ),
    )


TEAM_FACTORY = {
    "play": build_play_team,
    "open": build_open_team,
    "execute": build_execute_team,
}


def build_agent_teams(intent_dicts):
    merged_intents = merge_keywords_by_intent(intent_dicts, TEAM_FACTORY)
    print(f"Merged intents: {merged_intents}")
    team_configs = []
    for item in merged_intents:
        factory = TEAM_FACTORY.get(item["intent"])
        if factory and item.get("keywords"):  # keywords가 비어있지 않은 경우에만 team 생성
            team = factory(item["keywords"])
            # intent 정보와 team을 함께 담아서 반환
            team_configs.append({
                "intent": item["intent"],
                "keywords": item["keywords"],
                "team": team
            })
    return team_configs
