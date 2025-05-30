import asyncio
from agents.registry import intent_classifier

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken


async def classify_intent(prompt: str) -> str:
    cancellation_token = CancellationToken()
    try:
        response = await asyncio.wait_for(
            intent_classifier.on_messages(
                messages=[TextMessage(content=prompt, source="user")],
                cancellation_token=cancellation_token,
            ),
            timeout=10.0,
        )
        reply = response.chat_message.content.strip().lower()
        return reply if reply in {"play", "open", "run"} else "unknown"
    except asyncio.TimeoutError:
        return "unknown"
    except Exception as e:
        print(f"Error during intent classification: {e}")
        return "unknown"
