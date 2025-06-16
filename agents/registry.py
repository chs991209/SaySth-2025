from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from agents.model_clients import model_client03, model_client04
from tools import *

user_proxy = UserProxyAgent(name="user_proxy")

# Intent 분석기
intent_classifier = AssistantAgent(
    name="IntentClassifierAgent",
    model_client=model_client04,
    system_message="""
        You are an intent classification agent. 
        Given a Korean user prompt, respond with one of: 'play', 'open', or 'unknown'.
        Respond with ONLY the word.
        """,
)

intent_user_proxy = UserProxyAgent(name="intent_user_proxy")


# planning agent(계획자)
play_planner = AssistantAgent(
    name="YoutubeVideoPlayPlannerAgent",
    model_client=model_client03,
    system_message="""
        You are a planner that understands user intent and coordinates task execution. 
        Break down user goals into actionable steps and forward them to the correct assistant. 
        You should plan like this.
        First, have YoutubeVideoIdFinder search for and extract the first videoId in a single step. 
        Then, have the CodeGeneratorAgent generate Python code using that videoID, as before.
    """,
)

# planning agent(계획자) for open
open_planner = AssistantAgent(
    name="BrowserWebSiteOpenPlannerAgent",
    model_client=model_client03,
    system_message="""
        You are a planner that understands user intent and coordinates task execution. 
        You should plan like this.
        First, find out a suggestion website url related to user's prompt.
        And after that, the CodeGeneratorAgent's generation of the code is the last task of this groupchat.
        So let the CodeGeneratorAgent generate python code string with that url.
    """,
)

# Play Process Agents
youtube_videoid_finder = AssistantAgent(
    name="YoutubeVideoIdFinder",
    model_client=model_client03,
    tools=[youtube_tools.search_youtube_tool],
    system_message=(
        """
        You are a YouTube video search+extract agent.
        1. Use the search_youtube_tool with the provided query.
        2. From the returned search result, extract ONLY the first video's 'videoId'.
        3. Respond with exactly: videoID: <video id> (replace <video id> with the actual id) and nothing else.
        If any step fails, respond with "videoID: ERROR".
        Output nothing else—no explanation, no JSON, no code, just the above format.
        """
    ),
)

# Open Process Agents
url_searcher = AssistantAgent(
    name="SuggestionWebsiteUrlSearchAgent",
    model_client=model_client04,
    system_message="""
    You are a url searcher.
    Find a suggestible website url for user's prompt.
    Leave only the most suggestible one and your job is that.
    """,
)

code_generator_youtube_play = AssistantAgent(
    name="CodeGeneratorAgent",
    model_client=model_client03,
    system_message="""
    You are a Python code generator. Your only job is to generate Python code that opens a YouTube video, given a video ID variable called videoID.
    
    Always output Python code in the following exact format, and nothing else:
    
    import webbrowser
    
    videoID = '<videoID>'
    url = 'https://www.youtube.com/watch?v=' + videoID
    
    webbrowser.open(url)
    #CommandDone
    
    - Replace <videoID> with the actual video ID value produced by the team (e.g., g36q0ZLvygQ).
    - Output ONLY the Python code above, as plain text, not in markdown or triple-backticks.
    - Do not include explanations, comments (except for #CommandDone at the very end), or anything else.
    - Your reply must be suitable to be pasted into a Python file and run directly.
    """,
)
# Leave the rest of registry.py unchanged

code_generator_browser_website_open = AssistantAgent(
    name="CodeGeneratorAgent",
    model_client=model_client03,
    system_message="""
        You are a Python code generator. Generate Python code to open a website url, based on the collected url.
        using `webbrowser.open`, and the open target url is the suggested url. "
        Output ONLY the Python code string, which includes escapes so it can be just pasted to an empty python file and be implemented without dividing by lines. 
        Don't write any message except for code string, let that the last message of you.And after outputting the code data, end with "#CommandDone".
        """,
)
