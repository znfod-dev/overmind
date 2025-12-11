# Overmind - AI 통합 플랫폼 프로토타입

## 📋 프로젝트 개요

여러 AI 서비스를 통합하고, AI 기반의 다양한 애플리케이션을 제공하는 통합 플랫폼입니다.

### 핵심 기능
- **AI Gateway**: 여러 AI 서비스(Claude, Google AI, OpenAI)를 하나의 API로 통합
- **번역 서비스**: AI 기반 다국어 번역 (5개 언어 지원)
- **AI 일기장**: 대화형 일기 작성 시스템
- **사용자 인증**: JWT 기반 회원가입/로그인
- **관리자 시스템**: 사용자 관리 대시보드

---

## 🏗️ 시스템 아키텍처

### 기술 스택
- **언어**: Python 3.13
- **프레임워크**: FastAPI (비동기)
- **데이터베이스**: SQLite + SQLAlchemy (AsyncIO)
- **인증**: JWT (JSON Web Tokens)
- **AI 통합**: httpx (비동기 HTTP 클라이언트)
- **배포**: GCP Cloud Run (컨테이너 기반)

### Sub-Application 구조
```
/                     # 메인 페이지 (로그인 여부에 따라 리다이렉트)
/auth/                # 인증 시스템 (회원가입, 로그인, 프로필)
/diary/               # AI 일기장 (대화형 작성, 조회, 관리)
/translate/           # 번역 서비스
/admin/               # 관리자 대시보드
/ai/api/req           # AI Gateway 통합 엔드포인트
```

---

## 🎯 완성된 기능

### 1. AI Gateway
**목적**: 여러 AI 서비스를 하나의 통일된 API로 제공

**지원 AI 서비스**:
- Claude (Anthropic)
- Google AI Studio (Gemini)
- OpenAI (GPT)

**주요 엔드포인트**:
- `POST /ai/api/req` - 통합 AI 요청 (일반)
- `POST /ai/api/req/stream` - 스트리밍 응답

**요청 예시**:
```bash
curl -X POST http://localhost:8000/ai/api/req \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "claude",
    "prompt": "Hello, how are you?",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

**특징**:
- 통일된 요청/응답 형식
- API 키 인증 (X-API-Key 헤더)
- Rate limiting (분당 제한)
- 상세한 로깅 및 에러 핸들링

---

### 2. 번역 서비스

**지원 언어**: 한국어(ko), 베트남어(vi), 영어(en), 중국어(zh), 러시아어(ru)

**엔드포인트**:
- `GET /translate/` - 번역 웹 UI (Google Translate 스타일)
- `POST /translate/api/translate` - 번역 API (인증 불필요)
- `GET /translate/api/languages` - 지원 언어 목록

**웹 UI 기능**:
- 실시간 번역
- 언어 자동 감지
- 소스/타겟 언어 전환
- AI 제공자 선택 (Claude/OpenAI/Google AI)

---

### 3. AI 일기장 시스템

**컨셉**: AI와 대화하며 하루 일과를 자연스럽게 수집하고, 일기로 자동 생성

#### 3.1 대화형 일기 작성
- AI가 친근하게 하루 일과를 질문
- 사용자 답변에 공감하며 대화 진행
- 출근/퇴근, 감정, 특별한 사건 등을 자연스럽게 파악

#### 3.2 일기 생성 옵션
| 옵션 | 분량 | 토큰 수 |
|------|------|---------|
| 요약본 (summary) | 5~10줄 | 500 |
| 일반 (normal) | 20~30줄 | 2000 |
| 상세본 (detailed) | 50줄 이상 | 4000 |

#### 3.3 주요 기능
- **달력 UI**: 월별 일기 조회, 일기 있는 날짜 표시
- **감정 분석**: AI가 자동으로 감정 분석 (긍정적/부정적/중립 등)
- **자동 요약**: 일기 내용을 한 줄로 요약
- **프로필 연동**: 사용자 정보를 바탕으로 맞춤형 일기 생성

#### 3.4 데이터베이스 구조
```
Conversation (대화 세션)
  ├─ entry_date: 일기 날짜
  ├─ status: active/completed
  └─ messages: 대화 메시지들

Message (개별 메시지)
  ├─ role: ai/user
  └─ content: 메시지 내용

DiaryEntry (생성된 일기)
  ├─ title: 일기 제목
  ├─ content: 일기 본문
  ├─ entry_date: 일기 날짜
  ├─ length_type: 분량 타입
  ├─ mood: 감정 분석 결과
  └─ summary: 요약
```

#### 3.5 API 엔드포인트
```
# 대화 관리
POST   /diary/api/conversations              # 대화 시작
GET    /diary/api/conversations/active       # 활성 대화 조회
POST   /diary/api/conversations/{id}/messages # 메시지 전송
POST   /diary/api/conversations/{id}/complete # 대화 완료

# 일기 관리
POST   /diary/api/diaries                    # 일기 생성
GET    /diary/api/diaries                    # 일기 목록 (날짜 필터)
GET    /diary/api/diaries/date/{date}        # 특정 날짜 일기 조회
GET    /diary/api/diaries/{id}               # 일기 상세 조회
DELETE /diary/api/diaries/{id}               # 일기 삭제

# 웹 페이지
GET    /diary/                               # 달력 + 일기 조회
GET    /diary/write                          # 일기 작성 (채팅)
```

---

### 4. 사용자 인증 시스템

#### 4.1 회원가입/로그인
- 이메일 + 비밀번호 기반
- JWT 토큰 인증 (7일 유효)
- 자동 로그인 지원 (localStorage)

#### 4.2 프로필 관리
사용자가 선택적으로 입력 가능하며, AI 일기 작성 시 참고:

| 항목 | 용도 |
|------|------|
| 닉네임 | AI가 이름 부를 때 |
| 생년월일 | 나이대 파악 |
| 성별 | 말투/공감 스타일 조절 |
| 직업 | 업무 관련 대화 이해 |
| 취미 | 대화 주제 확장 |
| 가족 구성 | 가족 관련 일과 파악 |
| 반려동물 | 일상 대화 맥락 |

#### 4.3 API 엔드포인트
```
POST   /auth/api/signup       # 회원가입
POST   /auth/api/login        # 로그인
GET    /auth/api/me           # 내 정보 조회
PUT    /auth/api/profile      # 프로필 업데이트
PUT    /auth/api/password     # 비밀번호 변경

GET    /auth/signup           # 회원가입 페이지
GET    /auth/login            # 로그인 페이지
GET    /auth/me               # 마이페이지
```

---

### 5. 관리자 시스템

**접근 제한**: `role=admin` 사용자만 접근 가능

#### 5.1 주요 기능
- 사용자 목록 조회 (검색, 필터링)
- 사용자 상세 정보 조회
- 역할 변경 (admin/user)
- 계정 활성화/차단
- 프로필 정보 수정

#### 5.2 API 엔드포인트
```
GET    /admin/api/users              # 사용자 목록
GET    /admin/api/users/{id}         # 사용자 상세
PUT    /admin/api/users/{id}         # 사용자 상태 변경
PUT    /admin/api/users/{id}/profile # 프로필 수정
DELETE /admin/api/users/{id}         # 사용자 삭제

GET    /admin/                       # 대시보드
GET    /admin/users                  # 사용자 관리 페이지
GET    /admin/users/{id}             # 사용자 상세 페이지
```

#### 5.3 관리자 계정 생성
```bash
python scripts/create_admin.py
```

---

## 🚀 실행 방법

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어서 API 키 입력
```

### 2. 데이터베이스 초기화

서버 첫 실행 시 자동으로 테이블이 생성됩니다.

### 3. 서버 실행

```bash
# 로컬 개발 서버
python -m uvicorn app.main:app --reload

# 또는 스크립트 사용
python scripts/start.py
```

서버 실행 후 접속:
- 메인: http://localhost:8000
- API 문서: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 4. 관리자 계정 생성

```bash
python scripts/create_admin.py
```

---

## 📁 프로젝트 구조

```
overmind/
├── app/
│   ├── main.py                    # FastAPI 메인 애플리케이션
│   ├── config.py                  # 환경 설정
│   ├── database/                  # 데이터베이스 설정
│   │   └── config.py              # AsyncSession, Base
│   ├── models/                    # SQLAlchemy 모델
│   │   ├── user.py                # User, Profile
│   │   └── diary.py               # Conversation, Message, DiaryEntry
│   ├── dependencies/              # FastAPI 의존성
│   │   └── auth.py                # JWT 인증 의존성
│   ├── auth/                      # 인증 시스템
│   │   ├── main.py                # Sub-Application
│   │   ├── routers/               # 라우터 (API + 웹)
│   │   ├── schemas/               # Pydantic 스키마
│   │   ├── services/              # 비즈니스 로직
│   │   └── templates/             # Jinja2 템플릿
│   ├── diary/                     # 일기장 시스템
│   │   ├── main.py
│   │   ├── routers/               # conversation, diary, web
│   │   ├── schemas/
│   │   ├── services/              # conversation, diary, prompts
│   │   └── templates/             # index.html, write.html
│   ├── admin/                     # 관리자 시스템
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── templates/
│   ├── translation/               # 번역 서비스
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── templates/
│   ├── ai/                        # AI Gateway
│   │   ├── main.py
│   │   ├── routers/
│   │   └── services/              # claude, google_ai, openai
│   └── templates/                 # 공통 템플릿
├── scripts/
│   ├── start.py                   # 서버 시작 스크립트
│   ├── deploy.py                  # GCP 배포 스크립트
│   └── create_admin.py            # 관리자 생성 스크립트
├── data/
│   └── overmind.db                # SQLite 데이터베이스
├── logs/                          # 로그 파일
├── docs/                          # 문서
├── requirements.txt               # Python 의존성
├── .env                           # 환경 변수 (git 제외)
└── README.md                      # 프로젝트 소개
```

---

## 🔧 환경 변수

`.env` 파일에 다음 항목을 설정:

```bash
# AI API Keys
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...
OPENAI_API_KEY=sk-...

# API Authentication
API_AUTH_KEY=your-api-key

# Internal Service Authentication
INTERNAL_API_KEY=internal-secret-key

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# Service URLs
AI_SERVICE_URL=http://localhost:8000

# App Settings
APP_NAME=Overmind AI Gateway
DEBUG=false
DATABASE_ECHO=false
```

---

## 🐛 알려진 이슈 및 해결

### 1. Literal 타입 에러
**문제**: `NameError: name 'Literal' is not defined`

**해결**: 모든 Pydantic 스키마에서 `Literal` 타입을 `str`로 변경
- `Literal["summary", "normal", "detailed"]` → `str`

### 2. 날짜 표시 오류
**문제**: 12월 11일에 작성한 일기가 12월 12일에 표시됨

**원인**: JavaScript의 `toISOString()`이 UTC 시간 반환

**해결**: 로컬 시간을 정확하게 변환하는 `toLocalISODate()` 함수 추가
```javascript
function toLocalISODate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
```

---

## 📊 개발 현황

### ✅ 완료된 Phase

- **Phase 1**: 기본 구조 (FastAPI, 환경 설정)
- **Phase 2**: AI 클라이언트 구현 (Claude, Google AI, OpenAI)
- **Phase 3**: 통합 API 구현 (라우팅, 에러 핸들링)
- **Phase 4**: 추가 기능 (스트리밍, 로깅, Rate Limiting)
- **Phase 5**: 배포 준비 (Docker, GCP Cloud Run)
- **Phase 6**: 번역 서비스 구현
- **Phase 7**: AI 일기장 시스템 구현
- **Phase 8**: 사용자 인증 시스템 구현
- **Phase 9**: 관리자 시스템 구현
- **Phase 10**: 프로토타입 완성 및 버그 수정

### 🎯 프로토타입 완성!

현재 상태: **프로토타입 완성** (2025-12-11)

---

## 📝 라이선스

Private Project

---

## 👨‍💻 개발자

- 개발: FastAPI + Claude Code
- 기간: 2024.11 ~ 2025.12
- 버전: 1.0.0 (Prototype)
