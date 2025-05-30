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
        Given a Korean user prompt, respond with one of: 'play', 'open', 'run' or 'unknown'.
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
        First, use YoutubeSearchAgent to search youtube videos, and let the YoutubeVideoIdExtractor to find out the first videoId.
        And after that finding out the first videoId, the CodeGeneratorAgent's generation of the code is the last task of this groupchat.
        So let the CodeGeneratorAgent generate python code string with that videoID data.
    """,
)

# planning agent(계획자) for open
open_planner = AssistantAgent(
    name="BrowserWebSiteOpenPlannerAgent",
    model_client=model_client03,
    system_message="""
        You are a planner that understands user intent and coordinates task execution. 
        Break down user goals into actionable steps and forward them to the correct assistant. 
        You should plan like this.
        First, find out a suggestion website url related to user's prompt.
        And after that, the CodeGeneratorAgent's generation of the code is the last task of this groupchat.
        So let the CodeGeneratorAgent generate python code string with that url.
    """,
)

# planning agent(계획자) for run
run_planner = AssistantAgent(
    name="WindowProgramRunPlannerAgent",
    model_client=model_client03,
    system_message="""
        You are an agent who creates Python code that runs a program.
        You are a planning agent that understands user intent and coordinates multiple assistant agents to complete a goal in a structured sequence.

        ## Your Objective:
        Interpret the user's input, break it into discrete steps, and assign tasks to the appropriate assistant agents in the exact order described below.

        ## Task Flow:

        1. **Search the mentioned program shorcut name**:
        - First, search the web for the program shorcut that the user said.
        - If there is no program, output "Tell me again".
        
        2. **Code Generation**:
        - If find program shortcut name, forward it to the `CodeGeneratorAgent`.
        - Instruct the agent to generate a **Python code string** that utilizes the program.
    """,
)


# Play Process Agents
youtube_searcher = AssistantAgent(
    name="YoutubeSearchAgent",
    model_client=model_client03,
    tools=[youtube_tools.search_youtube_tool],
    system_message=(
        """
        You are a youtube video searcher. Call Youtube MCP server's searchVideos function and receive the result of the search.
        """
    ),
)

videoId_extractor = AssistantAgent(
    name="YoutubeVideoIdExtractor",
    model_client=model_client04,
    system_message=(
        """
        You are an extractor for navigating the list of the youtube search result.
        Find the first result of the youtube search results.
        The list of the results is composed as structure like [{}, {}].
        You should find the { "id": { "videoId": ... }} and the  "videoId" key's value of the first result, which is index 0.
        When you find 'videoId' key in the dictionary inside the result, get that videoId value and stop your work

        """
    ),
)

# Open Process Agents
url_searcher = AssistantAgent(
    name="SuggestionWebsiteUrlSearchAgent",
    model_client=model_client03,
    system_message="""
    You are a url searcher.
    Find a suggestible website url for user's prompt.
    Leave only the most suggestible one and your job is that.
    """,
)

#프로그램 이름 탐색기
program_searcher = AssistantAgent(
    name="ProgramNameSearchAgent",
    model_client=model_client03,
    system_message="""
    You are a program shortcut searcher.
    Search for the shortcut name of the program at the user prompt.
    Just leave the most likely and that's your mission.
    """,
)

code_generator_youtube_play = AssistantAgent(
    name="CodeGeneratorAgent",
    model_client=model_client04,
    system_message="""
        You are a Python code generator. Generate Python code to open a YouTube video, based on the collected videoID data 
        using `webbrowser.open`, and the open target url is 'https://www.youtube.com/watch?v=' + videoID. "
        Output ONLY the Python code string, which includes escapes so it can be just pasted to an empty python file and be implemented without dividing by lines. 
        Don't write any message except for code string, let that the last message of you.And after outputting the code data, end with "#CommandDone".
         ## Example Output:
        import webbrowser\\n\\nvideo_id = \\"abc123XYZ\\"\\nurl = \\"https://www.youtube.com/watch?v=\\" + video_id\\nwebbrowser.open(url)
        """,
)

code_generator_browser_website_open = AssistantAgent(
    name="CodeGeneratorAgent",
    model_client=model_client04,
    system_message="""
        You are a Python code generator. Generate Python code to open a website url, based on the collected url.
        using `webbrowser.open`, and the open target url is the suggested url. "
        Output ONLY the Python code string, which includes escapes so it can be just pasted to an empty python file and be implemented without dividing by lines. 
        Don't write any message except for code string, let that the last message of you.And after outputting the code data, end with "#CommandDone".
        ## Example Output:
        import webbrowser\\n\\nurl = \\"https://example.com\\"\\nwebbrowser.open(url)
        """,
)

code_generator_program_shortcut_run = AssistantAgent(
    name="CodeGeneratorAgent",
    model_client=model_client04,
    system_message="""
        You are a Python code generator. Generate Python code that runs a program shortcut based on the given shortcut name.

        Use `os.startfile` to open the target program shortcut.
        Output ONLY the Python code string, including necessary escape characters, so it can be pasted directly into an empty Python file and run without modification.
        Do NOT write any messages except for the code string. Your last output must end with the comment `#CommandDone`.
        
        ## Example Output:
        import os\\n\\nshortcut_name = \\"example.lnk\\"\\nshortcut_path = r\\"C:\\\\ProgramData\\\\Microsoft\\\\Windows\\\\Start Menu\\\\Programs\\\\" + shortcut_name\\nos.startfile(shortcut_path)
        """
)