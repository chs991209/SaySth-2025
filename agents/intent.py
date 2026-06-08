from collections import defaultdict

from agents.registry import intent_classifier
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

import asyncio
import json
from typing import List, Dict, Any

INTENT_LABELS = {"play", "open", "execute"}


async def classify_intents_with_keywords(prompt: str) -> List[Dict[str, Any]]:
    """
    Intention and keywords pairs Classification(의도 및 액션 키워드 분석기(븐류기)
    :param prompt:
    :return: intent dict list
    """
    cancellation_token = CancellationToken()
    try:
        response = await asyncio.wait_for(
            intent_classifier.on_messages(
                messages=[TextMessage(content=prompt, source="user")],
                cancellation_token=cancellation_token,
            ),
            timeout=10.0,
        )
        # reply: Extracted message content
        reply = ""
        if hasattr(response, "chat_message") and hasattr(
            response.chat_message, "content"
        ):
            reply = response.chat_message.content.strip()
        elif hasattr(response, "content"):
            reply = response.content.strip()

        # Code fences(Triple quotes) Removal
        if reply.startswith("```"):
            reply = reply.split("```")[1].strip()
        # parse to json (json.loads() 사용)
        try:
            parsed = json.loads(reply)
            result = [x for x in parsed if x.get("intent") in INTENT_LABELS]
            return result
        except json.JSONDecodeError as err:
            print(f"[classify_intents_with_keywords] Could not parse JSON: {err}")
            return []
    except asyncio.TimeoutError:
        print("[classify_intents_with_keywords] Intent classification timed out.")
        return []
    except Exception as e:
        print(
            f"[classify_intents_with_keywords] Error during intent classification: {e}"
        )
        return []


def merge_keywords_by_intent(intent_keyword_list, team_factory) -> List[Dict[str, Any]]:
    """
    Merge keywords by intent(의도에 따른 keywords 병합기)
    -> Prompt의 순서에 따라 keywords가 same intend의 여러 dict에 분산될 수 있으므로,
    이를 서비스 중인 intend 하나에 각 배치되도록 하여 intend당 keywords list가 존재하는 list를 만듭니다.
    :param intent_keyword_list:
    :param team_factory:
    :return: intent dict list
    """
    merged = defaultdict(list)
    for obj in intent_keyword_list:
        intent = obj.get("intent")
        keywords = obj.get("keywords", [])
        
        # keywords가 리스트가 아닌 경우 리스트로 변환
        if not isinstance(keywords, list):
            if keywords:  # None이 아니고 빈 값이 아닌 경우
                keywords = [keywords] if isinstance(keywords, str) else [str(keywords)]
            else:
                keywords = []
        
        # intent가 team_factory에 있고 keywords가 비어있지 않은 경우에만 병합
        if intent in team_factory and keywords:
            merged[intent].extend(keywords)
    # 중복 키워드 제거 (순서 유지)
    result = []
    for intent, keywords in merged.items():
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        result.append({"intent": intent, "keywords": unique_keywords})
    return result
