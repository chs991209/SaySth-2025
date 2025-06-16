# main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from agents.intent import classify_intent
from agents.groupchat import intent_to_groupchat
from autogen_agentchat.ui import Console
import time
import collections
import asyncio

app = FastAPI()

agent_timings = collections.defaultdict(list)

# --- Robust: get agents from the right attribute ---
def get_team_agents(team):
    return getattr(team, "participants", None) or getattr(team, "_participants", None)

def patch_agent_generate_reply(agents):
    import types

    for agent in agents:
        if hasattr(agent, "generate_reply") and not getattr(agent, "_timed", False):
            original = agent.generate_reply

            if asyncio.iscoroutinefunction(original):
                async def timed_generate_reply(self, *args, **kwargs):
                    start = time.time()
                    try:
                        out = await original(*args, **kwargs)
                    except Exception as e:
                        raise
                    finally:
                        elapsed = time.time() - start
                        agent_timings[self.name].append(elapsed)
                        print(f"[AgentTiming] {self.name}: {elapsed:.2f} seconds")
                    return out
            else:
                def timed_generate_reply(self, *args, **kwargs):
                    start = time.time()
                    try:
                        out = original(*args, **kwargs)
                    except Exception as e:
                        raise
                    finally:
                        elapsed = time.time() - start
                        agent_timings[self.name].append(elapsed)
                        print(f"[AgentTiming] {self.name}: {elapsed:.2f} seconds")
                    return out

            agent.generate_reply = types.MethodType(timed_generate_reply, agent)
            agent._timed = True  # Avoid double-patching

def extract_final_answer(task_result):
    code_candidates = []
    for msg in task_result.messages:
        if getattr(msg, "type", None) == "TextMessage" and msg.content:
            content = msg.content.strip()
            if "#CommandCode" in content:
                break
            if content.startswith("{") and content.endswith("}"):
                continue
            if content.startswith("```"):
                content = content.strip("`").replace("python", "").strip()
            code_candidates.append(content)
    return code_candidates[-1] if code_candidates else ""

@app.post("/execute")
async def execute_prompt(request: Request):
    body = await request.json()

    prompt = body.get("prompt", "").strip()
    print(prompt)
    if not prompt:
        return JSONResponse(content={"error": "Empty prompt"}, status_code=400)

    intent = await classify_intent(prompt)

    if intent == "unknown":
        return JSONResponse(content={"error": "Intent not recognized"}, status_code=400)

    team = intent_to_groupchat.get(intent)
    if not team:
        return JSONResponse(
            content={"error": "No groupchat found for intent"}, status_code=500
        )

    # Robust: supports both .participants and ._participants attributes
    patch_agent_generate_reply(get_team_agents(team))

    start_time = time.time()

    await team.reset()
    task_result = await Console(team.run_stream(task=prompt))
    code = extract_final_answer(task_result)
    # print(f"Final Command Code:", code)

    end_time = time.time()
    elapsed = end_time - start_time
    print(f"[GroupChat session duration] {elapsed:.2f} seconds")

    # --- Print per-agent timing summary ---
    print("=== Per-Agent Timing Summary ===")
    for agent, times in agent_timings.items():
        if times:
            total = sum(times)
            avg = total / len(times)
            print(f"{agent}: total {total:.2f}s, avg {avg:.2f}s, {len(times)} turn(s)")
    agent_timings.clear()  # Reset for next request

    return JSONResponse(content={"code": code})