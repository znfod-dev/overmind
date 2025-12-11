# Overmind AI Gateway

여러 AI 서비스(Claude, Google AI Studio, OpenAI)를 하나의 통합 API로 연결하는 게이트웨이 서버

🌐 **AI 채팅** + **번역 서비스**를 제공하는 통합 플랫폼

## 🎉 배포 완료!

**Production URL**: https://overmind-ai-gateway-wzyyrcmd6a-du.a.run.app

## 기능

### AI 채팅 서비스 (`/ai`)
- 🤖 다중 AI 제공자 통합 (Claude, Google AI Studio, OpenAI)
- 🔄 통일된 요청/응답 형식
- 🌊 스트리밍 응답 지원
- 📊 요청/응답 로깅

### 번역 서비스 (`/translate`)
- 🌐 5개 언어 지원 (한국어, 베트남어, 영어, 중국어, 러시아어)
- 🔁 양방향 번역 (모든 언어 쌍)
- 💬 웹 UI 제공 (Google Translate 스타일)
- 🎯 REST API 제공
- 🤖 선택 가능한 AI 제공자

### 공통 기능
- ⚡ FastAPI Sub-Application 아키텍처
- 🔐 API 키 인증 (X-API-Key 헤더)
- 🚦 Rate Limiting (분당 10회)
- ☁️ GCP Cloud Run 배포

## 기술 스택

- **언어**: Python 3.11+
- **프레임워크**: FastAPI 0.115.6
- **비동기 처리**: asyncio, httpx
- **배포**: GCP Cloud Run
- **컨테이너**: Docker (멀티 스테이지 빌드)

## 빠른 시작

### 로컬 개발

```bash
# 1. 저장소 클론
git clone <repository-url>
cd overmind

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일에 실제 API 키 입력

# 5. Admin 계정 생성 (서버 실행 전)
python scripts/create_admin.py --email admin@example.com --password yourpassword

# 6. 서버 실행
python scripts/start.py
```

서버 접속:
- **메인**: http://localhost:8000
- **회원가입**: http://localhost:8000/auth/signup
- **로그인**: http://localhost:8000/auth/login
- **Admin 대시보드**: http://localhost:8000/admin/ (Admin 계정 필요)
- **AI 채팅 API**: http://localhost:8000/ai/docs
- **번역 웹 UI**: http://localhost:8000/translate
- **번역 API**: http://localhost:8000/translate/docs
- **Health Check**: http://localhost:8000/health

### Docker로 실행

```bash
# Docker Compose 사용
docker-compose up --build

# 또는 Docker 직접 사용
docker build -t overmind-ai-gateway .
docker run -p 8000:8080 --env-file .env overmind-ai-gateway
```

## API 사용법

### 헬스 체크

```bash
curl https://overmind-ai-gateway-wzyyrcmd6a-du.a.run.app/health
```

### AI 채팅 API

**일반 요청** (POST /ai/api/req):

```bash
curl -X POST "https://overmind-ai-gateway-wzyyrcmd6a-du.a.run.app/ai/api/req" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: user19881205qkrwhdgus" \
  -d '{
    "provider": "claude",
    "model": "claude-3-5-sonnet-20241022",
    "prompt": "Hello!",
    "max_tokens": 100
  }'
```

**스트리밍 요청** (POST /ai/api/req/stream):

```bash
curl -X POST "https://overmind-ai-gateway-wzyyrcmd6a-du.a.run.app/ai/api/req/stream" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: user19881205qkrwhdgus" \
  -d '{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "prompt": "Tell me a joke",
    "max_tokens": 100
  }'
```

### 번역 API

**웹 UI 접속**:
```
https://overmind-ai-gateway-wzyyrcmd6a-du.a.run.app/translate
```

**번역 요청** (POST /translate/api/translate):

```bash
# 번역 API는 인증 불필요 - 누구나 사용 가능
curl -X POST "https://overmind-ai-gateway-wzyyrcmd6a-du.a.run.app/translate/api/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "ko",
    "provider": "claude"
  }'
```

**지원 언어 조회** (GET /translate/api/languages):

```bash
curl "https://overmind-ai-gateway-wzyyrcmd6a-du.a.run.app/translate/api/languages"
```

### 지원 제공자

| 제공자 | provider 값 | 기본 모델 |
|--------|------------|-----------|
| Claude (Anthropic) | `claude` | claude-3-5-sonnet-20241022 |
| Google AI Studio | `google_ai` | gemini-2.0-flash-exp |
| OpenAI | `openai` | gpt-4o-mini |

### 지원 언어 (번역)

| 언어 | 코드 | 원어 표기 |
|------|------|-----------|
| 한국어 | `ko` | 한국어 |
| 베트남어 | `vi` | Tiếng Việt |
| 영어 | `en` | English |
| 중국어 | `zh` | 中文 |
| 러시아어 | `ru` | Русский |

## GCP 배포

### 사전 준비

1. [gcloud CLI](https://cloud.google.com/sdk/docs/install) 설치
2. GCP 프로젝트 생성
3. Docker Desktop 실행 (선택사항)

### 배포 방법

```bash
# 1. scripts/deploy.py에서 PROJECT_ID 수정
# PROJECT_ID = "your-gcp-project-id"

# 2. .env 파일에 API 키 설정
cp .env.example .env
# API 키 입력

# 3. 배포 실행
python3 scripts/deploy.py
```

배포 스크립트가 자동으로:
- ✅ GCP 프로젝트 설정
- ✅ 필요한 API 활성화
- ✅ 환경 변수 설정
- ✅ Cloud Build로 이미지 빌드
- ✅ Cloud Run에 배포

배포 완료 후 서비스 URL이 출력됩니다.

### 로그 확인

```bash
gcloud run logs read overmind-ai-gateway --region asia-northeast3
```

## 프로젝트 구조

```
overmind/
├── app/
│   ├── ai/                   # AI 채팅 Sub-App
│   │   ├── routers/
│   │   │   └── chat.py      # 채팅 엔드포인트
│   │   └── main.py          # AI Sub-App
│   ├── translation/          # 번역 Sub-App
│   │   ├── routers/
│   │   │   ├── api.py       # 번역 API
│   │   │   └── web.py       # 웹 UI
│   │   ├── schemas/
│   │   │   ├── requests.py  # 요청 모델
│   │   │   └── responses.py # 응답 모델
│   │   ├── services/
│   │   │   ├── prompts.py   # 번역 프롬프트
│   │   │   └── translator.py # 번역 서비스
│   │   ├── templates/
│   │   │   └── translate.html # 웹 UI
│   │   └── main.py          # 번역 Sub-App
│   ├── clients/              # AI 제공자 클라이언트
│   │   ├── claude_client.py
│   │   ├── google_ai_client.py
│   │   └── openai_client.py
│   ├── core/                 # 핵심 설정
│   │   ├── config.py
│   │   ├── http_client.py
│   │   └── logging_config.py
│   ├── middleware/           # 미들웨어
│   │   ├── rate_limiter.py
│   │   └── request_logger.py
│   ├── schemas/              # 공통 스키마
│   │   ├── requests.py
│   │   └── responses.py
│   └── main.py               # Main FastAPI App
├── scripts/
│   ├── start.py              # 서버 시작
│   └── deploy.py             # GCP 배포 자동화
├── tests/                    # 테스트
│   ├── test_translation/    # 번역 테스트
│   ├── test_clients/        # 클라이언트 테스트
│   └── test_routers/        # 라우터 테스트
├── docs/                     # 문서
│   ├── PLAN.md              # 개발 계획서
│   └── TESTING.md           # 테스트 가이드
├── Dockerfile                # 컨테이너 이미지
├── docker-compose.yml        # 로컬 Docker 환경
├── .env.example             # 환경 변수 템플릿
└── requirements.txt         # Python 의존성
```

## 개발 진행 상황

### AI 채팅 서비스
✅ **Phase 1**: 프로젝트 기본 구조
✅ **Phase 2**: AI 클라이언트 모듈
✅ **Phase 3**: 통합 API 엔드포인트
✅ **Phase 4**: Rate Limiting, 로깅, 스트리밍
✅ **Phase 5**: GCP Cloud Run 배포

### 번역 서비스
✅ **Phase 6**: 번역 스키마 및 프롬프트
✅ **Phase 7**: TranslationService 구현
✅ **Phase 8**: 번역 API 엔드포인트
✅ **Phase 9**: 웹 UI 구현
✅ **Phase 10**: Sub-Application 아키텍처 적용
✅ **Phase 11**: 테스트 및 문서

자세한 내용은 [PLAN.md](docs/PLAN.md)를 참조하세요.

## Admin 계정 관리

### Admin 계정 생성 (서버 실행 전)

서버를 실행하기 전에 Admin 계정을 미리 생성해야 합니다:

```bash
# 새 Admin 계정 생성
python scripts/create_admin.py --email admin@example.com --password yourpassword
```

### 기존 사용자를 Admin으로 승격

```bash
# 기존 일반 사용자를 Admin으로 승격
python scripts/create_admin.py --email user@example.com --promote
```

### Admin 계정 목록 확인

```bash
# 모든 Admin 계정 목록 보기
python scripts/create_admin.py --list
```

### Admin 기능

- ✅ 전체 사용자 목록 조회 및 관리
- ✅ 사용자 계정 활성화/비활성화
- ✅ 사용자 계정 차단/차단 해제
- ✅ 사용자 역할 변경 (user ↔ admin)
- ✅ 사용자 프로필 조회 및 수정
- ✅ 사용자 삭제
- ✅ 시스템 통계 확인

## 환경 변수

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | Anthropic (Claude) API 키 | ✅ |
| `GOOGLE_AI_API_KEY` | Google AI Studio API 키 | ✅ |
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ |
| `API_AUTH_KEY` | 외부 사용자 인증 키 (X-API-Key 헤더) | ✅ |
| `INTERNAL_API_KEY` | 내부 서비스 간 통신용 키 | ✅ |
| `AI_SERVICE_URL` | AI 서비스 URL (기본값: http://localhost:8000) | ❌ |
| `JWT_SECRET_KEY` | JWT 토큰 암호화 키 | ✅ |
| `DEBUG` | 디버그 모드 (True/False) | ❌ |

## 라이선스

MIT License
