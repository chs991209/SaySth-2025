import re
import json


def extract_final_answer(task_result) -> dict | None:
    """
    Extract the Python dict action result from the message containing '#ACTIONSGENERATIONDONE'.
    Returns:
        dict: The extracted action dictionary (e.g. {"open_webbrowser": [...]}) if possible.
        None: If not found or not valid JSON.
    """
    messages = getattr(task_result, "messages", [])
    for msg in reversed(messages):
        content = (
            msg.content()
            if callable(getattr(msg, "content", None))
            else getattr(msg, "content", None)
        )
        if not content:
            continue

        if "#ACTIONSGENERATIONDONE" in content:
            # JSON dict를 추출합니다.
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                json_str = match.group(0)
                try:
                    obj = json.loads(json_str)
                    if isinstance(obj, dict):
                        return obj
                except Exception:
                    pass

            return None
    return None


def format_team_prompt(intent: str, keywords: list[str]) -> str:
    """
    Prompt for each team Formatter(팀별 프롬프트 재배치기)
    Return a prompt like 'play IVE MV, BTS MV' or 'execute Photoshop, Notepad'.
    """
    if not keywords:
        return ""
    kw_part = ", ".join(keywords)
    return f"{intent} {kw_part}"


# def patch_agent_generate_reply(agents):
#     import types
#
#     for agent in agents:
#         if hasattr(agent, "generate_reply") and not getattr(agent, "_timed", False):
#             original = agent.generate_reply
#
#             if asyncio.iscoroutinefunction(original):
#
#                 async def timed_generate_reply(self, *args, **kwargs):
#                     start = time.time()
#                     try:
#                         out = await original(*args, **kwargs)
#                     except Exception as e:
#                         raise
#                     finally:
#                         elapsed = time.time() - start
#                         agent_timings[self.name].append(elapsed)
#                         print(f"[AgentTiming] {self.name}: {elapsed:.2f} seconds")
#                     return out
#
#             else:
#
#                 def timed_generate_reply(self, *args, **kwargs):
#                     start = time.time()
#                     try:
#                         out = original(*args, **kwargs)
#                     except Exception as e:
#                         raise
#                     finally:
#                         elapsed = time.time() - start
#                         agent_timings[self.name].append(elapsed)
#                         print(f"[AgentTiming] {self.name}: {elapsed:.2f} seconds")
#                     return out
#
#             agent.generate_reply = types.MethodType(timed_generate_reply, agent)
#             agent._timed = True
