# Overmind Project Document

## 1. 프로젝트 개요

'Overmind'는 사용자별 맞춤형 AI 서비스를 제공하는 FastAPI 기반 백엔드 애플리케이션입니다.
주요 기능으로는 사용자 인증 및 프로필 관리, 국가 기반 AI 모델 선택, 구독 시스템, 일기/대화 기록 관리, 번역 서비스 등이 있습니다.

## 2. 주요 기능 및 아키텍처

### 2.1. 사용자 및 인증 (Auth Module)

*   **설명**: 사용자 회원가입, 로그인, 프로필 관리 기능을 제공합니다. 사용자의 국가 정보를 프로필에 저장하여 AI 모델 선택에 활용하며, 회원가입 시 자동으로 FREE 구독이 생성됩니다.
*   **관련 파일**:
    *   `app/auth/routers/auth.py`: 회원가입 (`POST /api/signup`), 로그인 (`POST /api/login`), 계정 삭제, 비밀번호 변경
    *   `app/auth/routers/profile.py`: 프로필 조회 (`GET /api/profile`), 프로필 업데이트 (`PUT /api/profile`), 프로필 이미지 업로드
    *   `app/auth/services/auth.py`: 인증 및 프로필 관련 비즈니스 로직
    *   `app/auth/services/security.py`: JWT 토큰 생성/검증, 비밀번호 해싱
    *   `app/auth/schemas/requests.py`: 회원가입 및 프로필 업데이트 요청 스키마 (`SignupRequest`, `ProfileUpdateRequest`)
    *   `app/models/user.py`: `User` 및 `Profile` 데이터베이스 모델
        - **Profile 모델**:
          - `country` (String(2)): 국가 코드 (KR, VN, US, JP, WW), AI 모델 선택에 사용
          - `profile_image_url` (String(500)): 프로필 이미지 URL 또는 경로
        - **User 모델**:
          - `subscription` relationship 추가 (1:1, CASCADE)

**회원가입 플로우:**
1. 사용자가 이메일, 비밀번호, 국가 코드를 입력하여 회원가입
2. User 레코드 생성 (role: "user", is_active: true)
3. Profile 레코드 생성 (country 포함)
4. FREE 구독 자동 생성 (tier: FREE, is_active: false)

### 2.2. 구독 시스템 (Subscription System)

*   **설명**: 사용자별 구독 티어를 관리하여 AI 모델 선택 및 서비스 기능을 차별화합니다.
*   **구독 티어**:
    - **FREE**: 기본 무료 티어 (회원가입 시 자동 생성)
      - Basic AI 모델 사용 (gpt-4o-mini, claude-haiku 등)
      - 광고 표시 (일회 결제로 제거 가능)
    - **PREMIUM**: 프리미엄 티어 (유료 구독)
      - Premium AI 모델 사용 (gpt-4o, claude-opus 등)
      - 광고 없음
      - 추가 기능 접근

*   **주요 필드** (`Subscription` 모델):
    - `user_id`: 사용자 ID (unique, CASCADE)
    - `tier`: 구독 티어 (FREE/PREMIUM)
    - `ad_free_purchased`: 광고 제거 일회 구매 여부
    - `ad_free_purchased_at`: 광고 제거 구매 시간
    - `starts_at`: 프리미엄 구독 시작 시간
    - `expires_at`: 프리미엄 구독 만료 시간
    - `is_active`: 구독 활성 상태

*   **관련 파일**:
    *   `app/models/subscription.py`: Subscription 모델 및 SubscriptionTier enum
    *   `app/auth/services/auth.py`: 회원가입 시 FREE 구독 자동 생성
    *   `app/core/model_selector.py`: 구독 티어 기반 AI 모델 선택

*   **자동 생성 메커니즘**: 모든 신규 사용자는 회원가입 시 자동으로 FREE 구독이 생성되며, Admin API를 통해 PREMIUM으로 업그레이드 가능합니다.

### 2.3. AI 모델 선택 (AI Model Selection)

*   **설명**: 사용자의 **국가** 및 **구독 티어**에 따라 최적의 AI 모델(OpenAI, Google AI, Claude 등)을 동적으로 선택합니다. 3단계 우선순위 폴백 시스템을 통해 장애 대응이 가능합니다.

*   **선택 기준**:
    1. **국가 기반 선택**: 사용자 프로필의 `country` 필드 (KR, VN, US, JP, WW)
    2. **티어 기반 선택**: 구독 티어 (basic = FREE, premium = PREMIUM)
    3. **우선순위 폴백**: priority_1 → priority_2 → priority_3

*   **지원 국가**:
    - **KR**: 대한민국
    - **VN**: 베트남
    - **US**: 미국
    - **JP**: 일본
    - **WW**: 전세계 (기본값, 폴백용)

*   **AI 제공자 및 모델 매핑**:

    | Provider | Basic Tier (FREE) | Premium Tier (PREMIUM) |
    |----------|-------------------|------------------------|
    | OpenAI | gpt-4o-mini | gpt-4o |
    | Google AI | gemini-2.0-flash-exp | gemini-2.0-flash-exp |
    | Claude | claude-haiku-4-5 | claude-opus-4-5-20251101 |

*   **모델 선택 플로우** (`AIModelSelector.get_model_for_user()`):
    1. 사용자 프로필에서 `country` 조회
    2. 사용자 구독에서 `tier` 조회 (PREMIUM이면 "premium", 아니면 "basic")
    3. `ai_model_priorities` 테이블에서 (country, tier)로 우선순위 조회
    4. 우선순위가 없으면 (WW, tier)로 폴백
    5. `priority_1` provider를 선택
    6. Provider와 tier에 맞는 모델 반환

*   **우선순위 설정 예시**:
    ```python
    # KR, basic: OpenAI (1순위) → Google AI (2순위) → Claude (3순위)
    country="KR", tier="basic",
    priority_1="openai", priority_2="google_ai", priority_3="claude"

    # KR, premium: Claude (1순위) → OpenAI (2순위) → Google AI (3순위)
    country="KR", tier="premium",
    priority_1="claude", priority_2="openai", priority_3="google_ai"
    ```

*   **관련 파일**:
    *   `app/core/model_selector.py`: `AIModelSelector` 클래스 - 핵심 선택 로직
    *   `app/models/ai_config.py`: `AIModelPriority` 데이터베이스 모델
    *   `app/admin/services/ai_config.py`: AI 우선순위 CRUD 서비스
    *   `app/admin/routers/api.py`: Admin API 엔드포인트 (우선순위 관리)

*   **장점**:
    - 국가별 AI 서비스 최적화 (규제, 성능, 비용)
    - 티어별 차별화된 모델 제공
    - 3단계 폴백으로 서비스 안정성 확보
    - Admin API를 통한 실시간 우선순위 변경 가능

### 2.4. 일기 및 대화 (Diary Module)

*   **설명**: 사용자의 일기 작성 및 AI와의 대화 기록을 관리합니다. 사용자의 프로필 정보를 기반으로 개인화된 AI 응답을 제공하며, 대화 내용을 바탕으로 일기를 자동 생성합니다.
*   **관련 파일**:
    *   `app/diary/routers/diary.py`: 일기 생성, 조회, 삭제 (`POST /api/diaries`, `GET /api/diaries`, `DELETE /api/diaries/{diary_id}`)
    *   `app/diary/routers/conversation.py`: AI와의 대화 메시지 송수신
    *   `app/diary/services/diary.py`: 일기 생성 로직, 감정 분석, 요약 생성
    *   `app/diary/services/conversation.py`: 대화 관리, AI 서비스 호출 (`call_ai_for_user` 사용)
    *   `app/diary/services/prompts.py`: AI 프롬프트 템플릿
    *   `app/models/diary.py`: `DiaryEntry`, `Conversation`, `Message` 데이터베이스 모델

*   **일기 생성 옵션**:
    - `summary`: 간단한 요약 형태
    - `normal`: 표준 일기 형태
    - `detailed`: 상세한 일기 형태

### 2.5. 번역 서비스 (Translation Module)

*   **설명**: 텍스트 번역 기능을 제공합니다. 다국어 지원 (ko, vi, en, zh, ru)과 여러 AI 제공자를 활용합니다.
*   **관련 파일**:
    *   `app/translation/routers/api.py`: 번역 API 엔드포인트
    *   `app/translation/services/translator.py`: 번역 비즈니스 로직
    *   `app/translation/services/prompts.py`: 번역 프롬프트 템플릿

### 2.6. 기타 핵심 컴포넌트

*   `app/main.py`: FastAPI 애플리케이션 진입점, 라우터 및 미들웨어 설정
*   `app/database/config.py`: 데이터베이스 연결 및 세션 관리 (SQLite with async)
*   `app/core/ai_helper.py`: 중앙화된 AI 서비스 호출 함수 (`call_ai_for_user`)
*   `app/dependencies/auth.py`: JWT 인증 및 현재 사용자 의존성 주입 (`get_current_user`, `get_admin_user`)
*   `app/middleware/`: 요청 로거, 레이트 리미터 (10 req/min) 등 미들웨어

## 3. 개발 환경 설정 및 실행

### 3.1. 환경 설정

1.  Python 3.10+ 설치
2.  가상 환경 생성 및 활성화:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  필요 라이브러리 설치:
    ```bash
    pip install -r requirements.txt
    ```
4.  `.env` 파일 설정 (예시):
    ```
    DATABASE_URL="sqlite+aiosqlite:///./data/overmind.db"
    SECRET_KEY="YOUR_SUPER_SECRET_KEY"
    JWT_SECRET_KEY="YOUR_JWT_SECRET_KEY"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=10080

    ANTHROPIC_API_KEY="sk-ant-api03-..."
    GOOGLE_AI_API_KEY="..."
    OPENAI_API_KEY="sk-..."

    API_AUTH_KEY="your-api-key"
    INTERNAL_API_KEY="internal-service-key"
    ```

### 3.2. 데이터베이스 초기화

*   FastAPI 앱이 처음 실행될 때 자동으로 모든 데이터베이스 테이블이 생성됩니다.
*   SQLAlchemy의 `Base.metadata.create_all()`을 사용하여 모델 정의에 따라 테이블을 자동 생성합니다.
*   초기 데이터 (AI 모델 우선순위 등)는 애플리케이션 시작 시 또는 Admin API를 통해 수동으로 설정할 수 있습니다.

**주의사항:**
- 데이터베이스 파일은 `data/` 디렉토리에 생성됩니다.
- 프로덕션 환경에서는 PostgreSQL 등의 RDBMS 사용을 권장합니다.

### 3.3. 애플리케이션 실행

*   **로컬 실행**:
    ```bash
    uvicorn app.main:app --reload
    ```
*   **프로덕션 환경**:
    ```bash
    python scripts/start.py
    ```
    (Cloud Run 배포 시 `scripts/deploy.py` 사용)

## 4. API 문서

애플리케이션 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

*   **Swagger UI**: `http://localhost:8000/docs`
*   **ReDoc**: `http://localhost:8000/redoc`

## 5. 에러 처리 및 예외 코드

### 5.1. 에러 응답 형식

모든 커스텀 에러는 다음의 통일된 JSON 형식으로 응답됩니다:

```json
{
  "detail": {
    "error_code": "AUTH_1001",
    "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "details": {
      "field": "email",
      "reason": "account not found"
    }
  }
}
```

**주요 필드:**
- `error_code`: 에러를 구분하는 고유 코드 (카테고리_번호 형식)
- `message`: 사용자에게 표시할 에러 메시지 (한국어/영어)
- `details`: 추가 상세 정보 (선택사항, dict)

### 5.2. 예외 클래스 계층구조

`app/core/exceptions.py`에 정의된 커스텀 예외 클래스:

- **AppException** (베이스 클래스)
  - 모든 커스텀 예외의 기본 클래스
  - HTTPException을 상속하여 FastAPI와 통합

- **AuthenticationError** (HTTP 401)
  - 인증 실패 관련 에러
  - 예: 잘못된 자격증명, 만료된 토큰

- **NotFoundError** (HTTP 404)
  - 리소스를 찾을 수 없음
  - 예: 존재하지 않는 사용자, 일기, 대화

- **BadRequestError** (HTTP 400)
  - 잘못된 요청 형식 또는 데이터
  - 예: 유효하지 않은 날짜 형식, 필수 필드 누락

- **ServiceError** (HTTP 500)
  - 서버 내부 에러
  - 예: AI 서비스 타임아웃, 데이터베이스 에러

### 5.3. 에러 코드 참조표

에러 코드는 카테고리별로 4자리 숫자로 구성:
- **1xxx**: 인증 (AUTH) 에러
- **2xxx**: 사용자/프로필 (USER) 에러
- **3xxx**: 대화 (CONV) 에러
- **4xxx**: 일기 (DIARY) 에러
- **5xxx**: AI 서비스 (AI) 에러
- **6xxx**: 구독 (SUB) 에러
- **9xxx**: 검증 (VAL) 에러

#### 인증 에러 (1xxx)

| 에러 코드 | HTTP 상태 | 메시지 | 설명 |
|---------|---------|--------|------|
| AUTH_1001 | 401 | Invalid credentials | 이메일 또는 비밀번호가 올바르지 않습니다 |
| AUTH_1002 | 400 | Email already exists | 이미 가입된 이메일 주소입니다 |
| AUTH_1003 | 401 | Account inactive | 비활성화된 계정입니다. 관리자에게 문의하세요 |
| AUTH_1004 | 401 | Account blocked | 차단된 계정입니다. 관리자에게 문의하세요 |
| AUTH_1005 | 401 | Invalid token | 유효하지 않은 인증 토큰입니다 |
| AUTH_1006 | 401 | Token expired | 인증 토큰이 만료되었습니다. 다시 로그인하세요 |
| AUTH_1007 | 403 | Insufficient permissions | 권한이 부족합니다 |

#### 사용자/프로필 에러 (2xxx)

| 에러 코드 | HTTP 상태 | 메시지 | 설명 |
|---------|---------|--------|------|
| USER_2001 | 404 | User not found | 사용자를 찾을 수 없습니다 |
| USER_2002 | 404 | Profile not found | 프로필을 찾을 수 없습니다 |
| USER_2003 | 400 | Invalid profile data | 프로필 데이터가 유효하지 않습니다 |

#### 대화 에러 (3xxx)

| 에러 코드 | HTTP 상태 | 메시지 | 설명 |
|---------|---------|--------|------|
| CONV_3001 | 404 | Conversation not found | 대화를 찾을 수 없습니다 |
| CONV_3002 | 400 | Conversation not active | 대화가 활성화되지 않았습니다 |
| CONV_3003 | 400 | Conversation already completed | 대화가 이미 완료되었습니다 |

#### 일기 에러 (4xxx)

| 에러 코드 | HTTP 상태 | 메시지 | 설명 |
|---------|---------|--------|------|
| DIARY_4001 | 404 | Diary not found | 일기를 찾을 수 없습니다 |
| DIARY_4002 | 400 | Conversation has no messages | 대화 내용이 없어 일기를 생성할 수 없습니다 |
| DIARY_4003 | 500 | Diary generation failed | 일기 생성 중 오류가 발생했습니다 |
| DIARY_4004 | 400 | Invalid date format | 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD 필요) |

#### AI 서비스 에러 (5xxx)

| 에러 코드 | HTTP 상태 | 메시지 | 설명 |
|---------|---------|--------|------|
| AI_5001 | 504 | AI service timeout | AI 서비스 타임아웃. 잠시 후 다시 시도하세요 |
| AI_5002 | 502 | AI service error | AI 서비스 오류. 잠시 후 다시 시도하세요 |
| AI_5003 | 503 | AI service unavailable | AI 서비스에 연결할 수 없습니다 |
| AI_5004 | 404 | AI priority not found | AI 우선순위 설정을 찾을 수 없습니다 |

#### 구독 에러 (6xxx)

| 에러 코드 | HTTP 상태 | 메시지 | 설명 |
|---------|---------|--------|------|
| SUB_6001 | 404 | Subscription not found | 구독 정보를 찾을 수 없습니다 |
| SUB_6002 | 400 | Subscription expired | 구독이 만료되었습니다 |
| SUB_6003 | 403 | Upgrade required | 프리미엄 기능입니다. 업그레이드가 필요합니다 |

#### 검증 에러 (9xxx)

| 에러 코드 | HTTP 상태 | 메시지 | 설명 |
|---------|---------|--------|------|
| VAL_9001 | 400 | Invalid request | 잘못된 요청입니다 |
| VAL_9002 | 422 | Validation error | 요청 데이터 검증 실패 |

## 6. 데이터베이스 스키마

### 6.1. 주요 테이블

#### users (사용자 계정)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | Integer | PK | 사용자 ID |
| email | String(255) | UNIQUE, NOT NULL | 이메일 (로그인 ID) |
| hashed_password | String(255) | NOT NULL | 해싱된 비밀번호 |
| role | String(20) | NOT NULL, DEFAULT 'user' | 역할 (admin/user) |
| is_active | Boolean | NOT NULL, DEFAULT true | 계정 활성화 여부 |
| is_blocked | Boolean | NOT NULL, DEFAULT false | 계정 차단 여부 |
| created_at | DateTime | NOT NULL | 생성 시간 |
| updated_at | DateTime | NOT NULL | 업데이트 시간 |

**Relationships:**
- `profile`: Profile (1:1, CASCADE)
- `subscription`: Subscription (1:1, CASCADE)
- `conversations`: Conversation[] (1:N, CASCADE)
- `diary_entries`: DiaryEntry[] (1:N, CASCADE)

#### profiles (사용자 프로필)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | Integer | PK | 프로필 ID |
| user_id | Integer | FK(users), UNIQUE, NOT NULL | 사용자 ID |
| nickname | String(50) | NULLABLE | 닉네임 |
| birth_date | Date | NULLABLE | 생년월일 |
| gender | String(20) | NULLABLE | 성별 |
| job | String(100) | NULLABLE | 직업 |
| hobbies | Text | NULLABLE | 취미 (JSON string) |
| family_composition | String(200) | NULLABLE | 가족 구성 |
| pets | String(200) | NULLABLE | 반려동물 |
| country | String(2) | NULLABLE, DEFAULT 'WW' | 국가 코드 (KR, VN, US, JP, WW) |
| profile_image_url | String(500) | NULLABLE | 프로필 이미지 URL/경로 |

**Relationships:**
- `user`: User (1:1)

#### subscriptions (구독 정보)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | Integer | PK | 구독 ID |
| user_id | Integer | FK(users), UNIQUE, NOT NULL | 사용자 ID |
| tier | Enum(SubscriptionTier) | NOT NULL, DEFAULT FREE | 구독 티어 (FREE/PREMIUM) |
| ad_free_purchased | Boolean | NOT NULL, DEFAULT false | 광고 제거 구매 여부 |
| ad_free_purchased_at | DateTime | NULLABLE | 광고 제거 구매 시간 |
| starts_at | DateTime | NULLABLE | 프리미엄 시작 시간 |
| expires_at | DateTime | NULLABLE | 프리미엄 만료 시간 |
| is_active | Boolean | NOT NULL, DEFAULT false | 구독 활성 여부 |
| created_at | DateTime | NOT NULL | 생성 시간 |
| updated_at | DateTime | NOT NULL | 업데이트 시간 |

**Relationships:**
- `user`: User (1:1)

**특징:**
- 회원가입 시 자동으로 FREE 구독 생성
- PREMIUM 구독은 starts_at, expires_at으로 기간 관리
- is_active는 현재 구독이 활성 상태인지 나타냄

#### ai_model_priorities (AI 모델 우선순위)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | Integer | PK | 우선순위 ID |
| country | String(2) | NOT NULL, INDEX | 국가 코드 (KR, VN, US, JP, WW) |
| tier | String(20) | NOT NULL, INDEX | 티어 (basic, premium) |
| priority_1 | String(20) | NOT NULL | 1순위 AI 제공자 |
| priority_2 | String(20) | NOT NULL | 2순위 AI 제공자 |
| priority_3 | String(20) | NOT NULL | 3순위 AI 제공자 |
| created_at | DateTime | NOT NULL | 생성 시간 |
| updated_at | DateTime | NOT NULL | 업데이트 시간 |

**제약조건:**
- Unique Constraint: (country, tier) - 각 국가/티어 조합당 1개만 존재

**AI 제공자 값:**
- `openai`: OpenAI (GPT 모델)
- `google_ai`: Google AI (Gemini 모델)
- `claude`: Anthropic Claude

**기본 설정 예시:**
- (KR, basic): openai → google_ai → claude
- (KR, premium): claude → openai → google_ai
- (WW, basic): openai → google_ai → claude (전세계 기본값)
- (WW, premium): claude → openai → google_ai (전세계 기본값)

#### conversations (대화)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | Integer | PK | 대화 ID |
| user_id | Integer | FK(users), NOT NULL | 사용자 ID |
| entry_date | Date | NOT NULL | 대화 날짜 |
| started_at | DateTime | NOT NULL | 대화 시작 시간 |
| ended_at | DateTime | NULLABLE | 대화 종료 시간 |
| status | Enum | NOT NULL | 대화 상태 (active/completed) |

**Relationships:**
- `user`: User (N:1)
- `messages`: Message[] (1:N, CASCADE)
- `diary_entries`: DiaryEntry[] (1:N, SET NULL)

#### messages (메시지)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | Integer | PK | 메시지 ID |
| conversation_id | Integer | FK(conversations), NOT NULL | 대화 ID |
| role | Enum | NOT NULL | 메시지 역할 (user/ai) |
| content | Text | NOT NULL | 메시지 내용 |
| created_at | DateTime | NOT NULL | 생성 시간 |

**Relationships:**
- `conversation`: Conversation (N:1)

#### diary_entries (일기)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|---------|------|
| id | Integer | PK | 일기 ID |
| user_id | Integer | FK(users), NOT NULL | 사용자 ID |
| conversation_id | Integer | FK(conversations), NULLABLE | 대화 ID (SET NULL) |
| title | String(200) | NOT NULL | 일기 제목 |
| content | Text | NOT NULL | 일기 내용 |
| entry_date | Date | NOT NULL, INDEX | 일기 날짜 |
| length_type | Enum | NOT NULL | 일기 길이 (summary/normal/detailed) |
| mood | String(50) | NULLABLE | 감정 분석 결과 |
| summary | Text | NULLABLE | 자동 생성 요약 |
| created_at | DateTime | NOT NULL | 생성 시간 |

**Relationships:**
- `user`: User (N:1)
- `conversation`: Conversation (N:1, SET NULL)

### 6.2. 관계 요약

```
User (1) ←→ (1) Profile
User (1) ←→ (1) Subscription
User (1) ←→ (N) Conversation ←→ (N) Message
User (1) ←→ (N) DiaryEntry
Conversation (1) ←→ (N) DiaryEntry
```

**CASCADE 삭제:**
- User 삭제 시: Profile, Subscription, Conversation, DiaryEntry 모두 삭제
- Conversation 삭제 시: Message 삭제, DiaryEntry는 conversation_id만 NULL 설정

## 7. 관리자 API (Admin API)

관리자 권한(`role="admin"`)이 필요한 엔드포인트입니다. 모든 엔드포인트는 `get_admin_user` 의존성을 통해 인증됩니다.

### 7.1. 사용자 관리

#### GET /admin/api/users
**모든 사용자 조회** (페이지네이션 및 필터링 지원)

**Query Parameters:**
- `limit` (int): 반환할 사용자 수 (1-100, 기본값: 50)
- `offset` (int): 페이지네이션 오프셋 (기본값: 0)
- `role` (str, optional): 역할 필터 (admin/user)
- `status` (str, optional): 상태 필터 (blocked/inactive)

**응답 예시:**
```json
{
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "role": "user",
      "is_active": true,
      "is_blocked": false,
      "created_at": "2025-01-15T10:30:00",
      "profile": {
        "nickname": "홍길동",
        "country": "KR"
      }
    }
  ],
  "total": 150
}
```

#### GET /admin/api/users/{user_id}
**사용자 상세 정보 조회** (프로필 포함)

**응답 예시:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "is_blocked": false,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00",
  "profile": {
    "nickname": "홍길동",
    "country": "KR",
    "job": "개발자",
    "hobbies": "[\"독서\", \"게임\"]"
  }
}
```

#### PUT /admin/api/users/{user_id}
**사용자 상태 업데이트** (role, is_active, is_blocked)

**요청 Body:**
```json
{
  "role": "admin",
  "is_active": true,
  "is_blocked": false
}
```

**제약사항:**
- 자신의 역할 변경 불가
- 자신을 비활성화/차단 불가

**응답:** UserDetailResponse (업데이트된 사용자 정보)

#### PUT /admin/api/users/{user_id}/profile
**사용자 프로필 업데이트**

**요청 Body:**
```json
{
  "nickname": "새로운닉네임",
  "country": "US",
  "job": "디자이너"
}
```

**응답:** ProfileResponse (업데이트된 프로필)

#### DELETE /admin/api/users/{user_id}
**사용자 영구 삭제**

**제약사항:**
- 자신 삭제 불가
- CASCADE 삭제: Profile, Subscription, Conversation, Message, DiaryEntry 모두 삭제

**응답:** 204 No Content

### 7.2. AI 모델 우선순위 관리

#### GET /admin/api/ai-priorities
**모든 AI 모델 우선순위 조회**

**응답 예시:**
```json
[
  {
    "id": 1,
    "country": "KR",
    "tier": "basic",
    "priority_1": "openai",
    "priority_2": "google_ai",
    "priority_3": "claude",
    "created_at": "2025-01-15T10:00:00",
    "updated_at": "2025-01-15T10:00:00"
  },
  {
    "id": 2,
    "country": "KR",
    "tier": "premium",
    "priority_1": "claude",
    "priority_2": "openai",
    "priority_3": "google_ai",
    "created_at": "2025-01-15T10:00:00",
    "updated_at": "2025-01-15T10:00:00"
  }
]
```

#### PUT /admin/api/ai-priorities
**AI 모델 우선순위 생성 또는 업데이트**

**요청 Body:**
```json
{
  "country": "KR",
  "tier": "basic",
  "priority_1": "openai",
  "priority_2": "google_ai",
  "priority_3": "claude"
}
```

**동작:**
- (country, tier) 조합이 존재하면 업데이트
- 존재하지 않으면 새로 생성
- provider 값 검증: `openai`, `google_ai`, `claude`만 허용

**응답:** AIModelPriorityResponse (생성/업데이트된 우선순위)

#### DELETE /admin/api/ai-priorities/{country}/{tier}
**AI 모델 우선순위 삭제**

**예시:** `DELETE /admin/api/ai-priorities/KR/basic`

**동작:**
- 해당 국가/티어 조합의 우선순위 설정 삭제
- 삭제 후 해당 국가/티어 사용자는 WW(전세계) 기본값으로 폴백

**응답:** 204 No Content

### 7.3. 시스템 통계

#### GET /admin/api/stats
**시스템 전체 통계 조회**

**응답 예시:**
```json
{
  "total_users": 1500,
  "admin_users": 3,
  "active_users": 1480,
  "blocked_users": 5,
  "total_diaries": 8500
}
```

**통계 항목:**
- `total_users`: 전체 사용자 수
- `admin_users`: 관리자 수
- `active_users`: 활성 사용자 수
- `blocked_users`: 차단된 사용자 수
- `total_diaries`: 전체 일기 수

### 7.4. 관련 파일

*   `app/admin/routers/api.py`: Admin API 엔드포인트 정의
*   `app/admin/services/admin.py`: AdminService - 사용자 관리 로직
*   `app/admin/services/ai_config.py`: AIConfigService - AI 우선순위 CRUD 로직
*   `app/admin/schemas/requests.py`: 요청 스키마 (UserUpdateRequest, AIModelPriorityUpdateRequest 등)
*   `app/admin/schemas/responses.py`: 응답 스키마 (UserDetailResponse, StatsResponse 등)
*   `app/dependencies/auth.py`: `get_admin_user` - 관리자 인증 의존성

---
