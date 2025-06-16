from agents.registry import (
    user_proxy,
    play_planner,
    open_planner,
    youtube_videoid_finder,  # <== new
    url_searcher,
    code_generator_youtube_play,
    code_generator_browser_website_open,
)
from agents.model_clients import model_client03, model_client04
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination

selector_prompt = """You are managing a team of agents to perform a task.
Available agents and their roles:
{roles}

Conversation context so far:
{history}

Available participants: {participants}

Instructions:
- If the task has not yet been broken down, always select the planner agent.
- Only select a non-planner agent if a specific task was clearly assigned by the planner.
- Only select one agent to speak next.

Which agent should respond next?
"""

text_mention_termination = TextMentionTermination("#CommandDone")
max_messages_termination = MaxMessageTermination(max_messages=35)
termination = text_mention_termination | max_messages_termination

# === Custom candidate_func ==

def make_candidate_func(planner_agent, non_planner_agents):
    def candidate_func(messages):
        # User triggers planning agent first (skip user_proxy if present)
        if messages[-1].source == "user":
            return [planner_agent.name]

        # If previous message is planner, see who was assigned
        last_message = messages[-1]
        if last_message.source == planner_agent.name:
            participants = []
            msg_text = last_message.to_text()
            for agent in non_planner_agents:
                if agent.name in msg_text:
                    participants.append(agent.name)
            if participants:
                return participants

        # Check if all non-planners have spoken; if so, let planner finish
        agents_already_turn = set(msg.source for msg in messages)
        if all(agent.name in agents_already_turn for agent in non_planner_agents):
            return [planner_agent.name]

        # Otherwise, all agents are possible
        return [planner_agent.name] + [agent.name for agent in non_planner_agents]
    return candidate_func


# === Actual Teams ===
play_team_agents = [
    play_planner,
    youtube_videoid_finder,
    code_generator_youtube_play,
]
open_team_agents = [
    open_planner,
    url_searcher,
    code_generator_browser_website_open,
]

play_team = SelectorGroupChat(
    participants=[user_proxy] + play_team_agents,
    model_client=model_client04,
    selector_prompt=selector_prompt,
    termination_condition=termination,
    candidate_func=make_candidate_func(play_planner, play_team_agents[1:]),
)

open_team = SelectorGroupChat(
    participants=[user_proxy] + open_team_agents,
    model_client=model_client03,
    selector_prompt=selector_prompt,
    termination_condition=termination,
    candidate_func=make_candidate_func(open_planner, open_team_agents[1:]),
)

intent_to_groupchat = {
    "play": play_team,
    "open": open_team,
}