# AutoGen Install
<hr/>

AutoGen requires Python 3.10 or later.

## 가상 환경 세팅법
## Create and activate:
```
# On Windows, change `python3` to `python` (if `python` is Python 3).
python3 -m venv .venv

# On Windows, change `bin` to `scripts`.
source .venv/bin/activate
```
## To deactivate later, run:
```
deactivate
```

## pip Install
```
# Install AgentChat and OpenAI client from Extensions
pip install -U "autogen-agentchat" "autogen-ext[openai]" autogen-ext[openai,web-surfer]
playwright install
```

### 세팅 참고 링크
- [AutoGen 공식 Github](https://github.com/microsoft/autogen)
# 실행법
## mcp 서버
```
python mcp_server.py
```
## autogen 서버
```
uvicorn main:app --host 0.0.0.0 --port 8080
```
### 어시스턴트 사용
-위의 서버 구동 후에 autogen의 endpoint에 갖을 넣어야 한다. (text, voice 두가지로 나눠져 있음)
1) 음성파일을 사용하는 경우 -> http://0.0.0.0:8080/receive-voice
2) 텍스트만 사용하는 경우   -> http://0.0.0.0:8080/receive-text