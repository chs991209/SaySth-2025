# SaySth-2025
Cap Stone Project in 2025 

## 프로젝트 구조

- `main.py`: FastAPI 서버 엔트리포인트
- `agents/`: AI 에이전트 관련 코드
- `tools/`: 외부 API 도구 (YouTube 등)
- `client/`: TypeScript 기반 웹 클라이언트 (Vite + React)
- `frontend-server/`: Next.js 기반 API 프록시 서버 (ASR, Agentic AI, MCP 서버 프록시)
- `localMCPServer/`: Local MCP 서버

## 서버 실행

### 1. Agentic AI 서버 실행

```bash
# 가상환경 활성화
source agenticai-saysth/bin/activate

# 서버 실행
uvicorn main:app --port 8002 --reload
```

### 2. Local MCP 서버 실행

```bash
# localMCPServer 디렉토리로 이동
cd localMCPServer

# 가상환경 활성화 (필요한 경우)
source local-mcp-server/bin/activate

# MCP 서버 실행
uvicorn local-mcp-server:app --port 8003 --reload
```

### 3. Frontend Server 실행 (API 프록시)

```bash
# frontend-server 디렉토리로 이동
cd frontend-server

# 환경 변수 설정 (필수!)
# .env.local 파일을 생성하고 다음 내용을 추가:
# ASR_SERVER_URL=http://your-asr-server-url:8004
# AGENTIC_AI_SERVER_URL=http://127.0.0.1:8002
# MCP_SERVER_URL=http://127.0.0.1:8003

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

Frontend Server는 `http://localhost:3000`에서 실행됩니다.

**중요:** 
- `.env.local` 파일에 모든 서버 주소를 설정해야 합니다. 설정하지 않으면 서버가 오류를 반환합니다.
- 이 서버는 API 엔드포인트만 제공하며, 웹페이지는 제공하지 않습니다.

### 4. 클라이언트 실행 (기존 Vite 클라이언트)

```bash
# client 디렉토리로 이동
cd client

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

**참고:** 다음 서버들을 실행해야 정상적으로 동작합니다:
- Agentic AI 서버: `http://127.0.0.1:8002`
- Local MCP 서버: `http://127.0.0.1:8003`
- Frontend Server (Next.js): `http://localhost:3000` (API 프록시만 제공, 웹페이지 없음)
- 클라이언트 (Vite): `http://localhost:5173` (또는 다른 포트, 웹페이지 제공)

**Frontend Server 역할:**
- 클라이언트의 요청을 ASR 서버, Agentic AI 서버, MCP 서버로 프록시
- 웹페이지는 제공하지 않으며, API 엔드포인트만 제공

## API 엔드포인트

### POST /execute

텍스트 프롬프트를 실행하여 액션을 생성합니다.

**Request:**
```json
{
  "prompt": "아이브 뮤비 재생"
}
```

**Response:**
```json
{
  "actions_list": [
    {
      "open_webbrowser": ["https://www.youtube.com/watch?v=xxx"]
    }
  ]
}
```

### POST /execute-voice

음성 명령(ASR을 통해 변환된 텍스트)을 실행하여 액션을 생성합니다.

**Request:**
```json
{
  "prompt": "아이브 뮤비 재생"
}
```

**Response:**
```json
{
  "actions_list": [
    {
      "open_webbrowser": ["https://www.youtube.com/watch?v=xxx"]
    }
  ]
}
```

## 동작 흐름

### 텍스트 입력
1. 사용자가 텍스트 입력
2. Frontend Server → Agentic AI 서버 (`/execute`)
3. 액션 생성
4. Frontend Server → MCP 서버 (`/pc_action_execute`)
5. 액션 실행

### 음성 입력
1. 클라이언트에서 마이크 버튼 클릭
2. 음성 녹음
3. 클라이언트 → Frontend Server (`/api/asr`) → ASR 서버 (음성 → 텍스트 변환)
4. 클라이언트 → Frontend Server (`/api/execute-voice`) → Agentic AI 서버 (`/execute-voice`)
5. 액션 생성
6. 클라이언트 → Frontend Server (`/api/execute-actions`) → MCP 서버 (`/pc_action_execute`)
7. 액션 실행

