from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from agents.model_clients import model_client00, model_client01, model_client02, model_client03, model_client04
from tools import youtube_tools

user_proxy = UserProxyAgent(name="user_proxy")

# ---- INTENT CLASSIFIER ----
intent_classifier = AssistantAgent(
    name="IntentWithKeywordsClassifyAgent",
    model_client=model_client03,
    system_message="""
        You are an intentions and keywords extraction agent.
        Classify a user's prompt into mult:
          - play: For any request to play, stream, watch, or listen to a video, music, or media. (e.g. 'play', 'stream', 'watch', '틀어줘', '재생해줘', etc.)
          - open: For any request to open, access, visit, or enter a website or online service. (e.g. 'open', 'visit', 'enter', '접속', '열어줘', etc.)
          - execute: For any request to run, start, launch, or execute a program or application. (e.g. '실행해', 'launch', 'run', 'start', etc.)
          - unknown: If none applies.
        EXAMPLES:
          - 'IVE 뮤비 틀어줘' -> play
          - 'launch Excel' -> execute
          - 'open news site' -> open
          - '엑셀 실행해 줘' -> execute
        Rules:
          - For ambiguous play/open, prefer play if video/music/entertainment.
          = Make as a JSON list of objects following this pattern:
            [
              {"intent": "play", "keywords": ["IVE music video"]},
              {"intent": "execute", "keywords": ["Photoshop", "Kakaotalk"]},
              {"intent": "open", "keywords": ["News", "Weather forecasting"]},
            ]
          = intent value ONLY play, open, or execute.
          - ONLY identified intents with their keywords matching the intent should be in the output.
        OUTPUT JSON list format and your job is done.
    """,
)

# planning agent(계획자)
play_planner = AssistantAgent(
    name="PlayPlannerAgent",
    model_client=model_client00,
    system_message="""
        You are the planner for YouTube video urls generation task. 
        Your job is to coordinate the following subtasks for every keyword from the user:
        
        1. For each keyword in the user's keyword list, instruct 'YouTubeVideoSearcherAgent' to:
            a. Use the 'search_youtube_videos' tool with the keyword.
            b. Extract ONLY the first video's 'videoId' from the result (if available).
        
        2. After all keywords are processed, for each videoId, create the corresponding YouTube URL by appending it to:
           https://www.youtube.com/watch?v=<videoId>
        
        3. Collect all valid YouTube URLs into a list.
        
        4. Reply with a single dictionary in this format: 
           {"open_webbrowser": [list of YouTube URLs]}

        Rules:
        - If a keyword fails to find a videoId, skip it (do NOT include "None" or "ERROR" in the page list).
        - Plan in clear steps and assign only one keyword at a time to the YouTubeVideoSearcherAgent.
        - You are ONLY the coordinator: you never use tools yourself, you give precise instructions to the other agent.
        - At the end, confirm output to user_proxy.
        
        Example output (after all tasks):
        
        {"open_webbrowser": ["https://www.youtube.com/watch?v=XXXXXXXX", "https://www.youtube.com/watch?v=YYYYYYYY"]}
        
        If no results found, return {"open_webbrowser": []}
        
        5. After replying with the result as: {"open_webbrowser": [ ... ]}
        ALWAYS output "#ACTIONSGENERATIONDONE" on a new line. This signals the group chat is finished.
        
        Example final message:
        {"open_webbrowser": ["https://www.youtube.com/watch?v=abc123", ...]}
        #ACTIONSGENERATIONDONE
    """,
)

open_planner = AssistantAgent(
    name="OpenPlannerAgent",
    model_client=model_client00,
    system_message="""
        You are the planner for a YouTube video play utltask. 
        Your job is to coordinate the following subtasks for every keyword from the user:

        1. For each keyword in the user's keyword list, instruct 'SuggestionWebsiteUrlSearchAgent' to:
            a. Collect the suggestion url with the keyword.
            b. Reply the suggestion url for each keyword.
            
            

        2. After all keywords are processed, combine all the collected suggestion urls into a single list.

        3. Reply with a single dictionary in this format: 
           {"open_webbrowser": [list of suggestion URLs]}

        Rules:
        - Plan in clear steps and assign only one keyword at a time to the SuggestionWebsiteUrlSearchAgent.
        - You are ONLY the coordinator: you never use tools yourself, you give precise instructions to the other agent.
        - At the end, confirm output to user_proxy.

        Example output (after all tasks):

        {"open_webbrowser": ["https://www.news.naver.com", "https://weather.naver.com/]}

        If no results found, return {"open_webbrowser": []}
        
        5. After replying with the result as: {"open_webbrowser": [ ... ]}
        ALWAYS output "#ACTIONSGENERATIONDONE" on a new line. This signals the group chat is finished.
        
        Example final message:
        {"open_webbrowser": ["https://www.news.naver.com", ...}
        #ACTIONSGENERATIONDONE
    """,
)

execute_planner = AssistantAgent(
    name="ExecutePlannerAgent",
    model_client=model_client00,
    system_message="""
        You are the planner for a Windows program execution preparation task.
        Your job is to coordinate the following subtasks for every program name from the user:
        
        1. For each program name in the user's list:
           a. Instruct 'ExecuteProgramsParameterAgent' to map the given program name to the correct Windows exe filename.
           b. If no exact exe filename is returned, repeat the lookup using:
              - Commonly used synonyms, alternate spellings, and direct English translations (e.g., '포토샵' -> 'Photoshop').
              - If needed, use a web/model search to verify standard Windows exe names for popular programs.
           c. Collect the returned exe filename for each name (if found).
        
        2. Once all names are processed, gather all valid exe filenames into a single Python list.
        
        3. Reply with a single dictionary in this format:
           {"execute_programs": [list of exe filenames]}
        
        Rules:
        - Always process one program name at a time with ExecuteProgramsParameterAgent.
        - Never include null, None, or NOT_FOUND in the list; only confirmed exe filenames.
        - Do not use tools yourself, just provide precise instructions to the sub-agent.
        
        If no results are found for any program, return {"execute_programs": []}
        
        After replying with the result as: {"execute_programs": [ ... ]}
        ALWAYS output "#ACTIONSGENERATIONDONE" on a new line to signal the group chat is finished.
        
        Example final message:
        {"execute_programs": ["Photoshop.exe", "notepad.exe", ...]}
        #ACTIONSGENERATIONDONE
        
        Tip: Always consider user-localized, translated, or synonimized names for common programs. If you cannot find a mapping directly, ask your sub-agent to try the English equivalent or check common exe file lists.
    """,
)

# ---- ACTION TARGET ARGUMENT COLLECTING AGENTS ----

url_searcher = AssistantAgent(
    name="SuggestionWebsiteUrlSearchAgent",
    model_client=model_client00,
    system_message="""
    You are a website URL suggestion search and collecting agent.
    
    When given a keyword, do this:
    1. Given a user request to open a site or topic, collect ONLY the most official/obvious URL for that query.
    2. OUTPUT FORMAT: Always reply with only url in the exact format below and NOTHING ELSE.
    
    Example output: "https://www.news.naver.com"
    Don't explain, just output the url. No explanation needed, only the url is needed.    
""",
)

# YouTube video agent
youtube_video_searcher = AssistantAgent(
    name="YouTubeVideoSearcherAgent",
    model_client=model_client00,
    tools=[youtube_tools.search_youtube_videos],  # tool using search agent
    system_message="""
You are an assistant with access to the search_youtube_videos tool.

When given a keyword, do this:
1. Use 'search_youtube_videos' tool with the keyword (provided by PlayPlannerAgent).
2. From the returned result, extract ONLY the first video's 'videoId'.
   - If extraction fails, reply with "videoId: NOT_FOUND".
   - If successful, reply with "videoId: <actual_video_id>" (replace <actual_video_id>).
3. OUTPUT FORMAT: Always reply with only the videoId in the exact format above and NOTHING ELSE.
""",
)

# Program exe mapping agent
executable_program_filename_finder = AssistantAgent(
    name="ExecuteProgramsParameterAgent",
    model_client=model_client00,
    system_message="""
        You are a Windows executable filename resolver.
        When given a program name (for example: '포토샵', 'Photoshop', '메모장', 'notepad'), do the following:

        1. Map it to the exact matching existing Windows exe file name (e.g., 'Photoshop.exe', 'notepad.exe').
        2. OUTPUT FORMAT: 
            - If found: only reply with the exe filename (e.g., "notepad.exe").
            - If NOT found: reply exactly with "NOT_FOUND".
        Do NOT explain your answer; return ONLY the exe filename or NOT_FOUND.
    """,
)
