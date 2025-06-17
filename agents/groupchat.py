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

termination = TextMentionTermination("#ACTIONSGENERATIONDONE") | MaxMessageTermination(
    200
)


def make_candidate_func(planner_agent, process_agents):
    def candidate_func(messages):
        if messages[-1].source == "user":
            return [planner_agent.name]
        last_message = messages[-1]
        if last_message.source == planner_agent.name:
            participants = []
            msg_text = last_message.to_text()
            for agent in process_agents:
                if agent.name in msg_text:
                    participants.append(agent.name)
            if participants:
                return participants
        agents_already_turn = set(msg.source for msg in messages)
        if all(agent.name in agents_already_turn for agent in process_agents):
            return [planner_agent.name]
        return [planner_agent.name] + [
            agent.name
            for agent in process_agents
            if agent.name not in agents_already_turn
        ]

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
    teams = []
    for item in merged_intents:
        factory = TEAM_FACTORY.get(item["intent"])
        if factory:
            team = factory(item["keywords"])
            teams.append(team)
    return teams
