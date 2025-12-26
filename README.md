# Overmind API

> 지능형 일기 작성을 위한 AI 기반 FastAPI 애플리케이션

## 📖 개요

Overmind API는 사용자가 작성한 일기를 AI가 분석하고 상호작용하여 더 깊은 성찰을 돕는 서비스입니다. FastAPI를 기반으로 구축되었으며, 모듈화된 아키텍처를 통해 확장성과 유지보수성을 극대화했습니다.

## ✨ 주요 기능

- **사용자 인증**: JWT 기반의 안전한 회원가입, 로그인 및 세션 관리 기능을 제공합니다.
- **일기 관리 (CRUD)**: 사용자는 자신의 일기를 생성, 조회, 수정, 삭제할 수 있습니다.
- **AI 기반 대화**: 사용자가 작성한 일기 내용을 바탕으로 AI와 대화를 나눌 수 있습니다.
- **이미지 생성**: 일기 내용에 어울리는 이미지를 AI를 통해 생성하고 저장합니다.
- **관리자 대시보드**: 사용자 및 AI 설정 관리를 위한 관리자 페이지를 제공합니다.
- **다국어 번역**: 텍스트 번역 기능을 지원합니다.

## 🚀 기술 스택

- **백엔드**: FastAPI, Python 3.11+
- **데이터베이스**: PostgreSQL (Async aio-pika), SQLAlchemy (Async ORM)
- **데이터베이스 마이그레이션**: Alembic
- **인증**: JWT (JSON Web Tokens), OAuth2
- **데이터 유효성 검사**: Pydantic
- **API 클라이언트**: aiohttp
- **테스트**: Pytest
- **컨테이너**: Docker, Docker Compose

## 🏗️ 아키텍처

이 프로젝트는 기능별로 독립된 **Sub-Application** 구조를 채택하여 높은 모듈성을 가집니다.

- `app/main.py`는 중앙 진입점(Entrypoint) 역할을 하며, 각 기능별 앱을 마운트(Mount)합니다.
- 각 기능(예: `app/diary`, `app/auth`)은 자체적인 라우터, 서비스, 스키마를 갖춘 독립적인 FastAPI 앱으로 구성되어 있습니다.
- **계층(Layer) 분리**:
  - `routers`: HTTP 요청 수신, 데이터 유효성 검사 및 서비스 계층 호출
  - `services`: 핵심 비즈니스 로직 처리
  - `models`: SQLAlchemy ORM 모델을 통한 데이터베이스 스키마 정의
  - `schemas`: Pydantic 모델을 이용한 API 데이터 형태 정의

### 폴더 구조

```
/
├── alembic/              # 데이터베이스 마이그레이션 스크립트
├── app/                  # 핵심 애플리케이션 코드
│   ├── admin/            # 관리자 기능 모듈
│   ├── auth/             # 인증 기능 모듈
│   ├── diary/            # 일기 기능 모듈
│   ├── clients/          # 외부 AI API 클라이언트
│   ├── core/             # 로깅, 예외 처리 등 공통 로직
│   ├── database/         # 데이터베이스 설정 및 세션 관리
│   ├── models/           # SQLAlchemy 데이터베이스 모델
│   └── ...
├── scripts/              # 배포, DB 리셋 등 유틸리티 스크립트
├── tests/                # Pytest 테스트 코드
├── alembic.ini           # Alembic 설정 파일
├── docker-compose.yml    # Docker Compose 설정
├── Dockerfile            # Docker 이미지 빌드 파일
└── requirements.txt      # Python 의존성 목록
```

## ⚙️ 설치 및 설정

### 1. 소스 코드 복제

```bash
git clone https://your-repository-url.com/overmind.git
cd overmind
```

### 2. 가상 환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

루트 디렉터리에 `.env` 파일을 생성하고 아래 내용을 참고하여 환경 변수를 설정합니다.

```env
# .env 예시

# 데이터베이스 설정
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=overmind_db

# JWT 설정
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 외부 API 키
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
CLAUDE_API_KEY=...
```

## ▶️ 실행 방법

### 1. 데이터베이스 마이그레이션

애플리케이션을 실행하기 전에 데이터베이스 스키마를 최신 상태로 마이그레이션해야 합니다.

```bash
alembic upgrade head
```

### 2. FastAPI 서버 실행

Uvicorn을 사용하여 개발 서버를 실행합니다.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`--reload` 플래그는 코드 변경 시 서버를 자동으로 재시작합니다.

### 3. (선택) Docker Compose로 실행

Docker가 설치되어 있다면 다음 명령어로 데이터베이스와 애플리케이션을 한 번에 실행할 수 있습니다.

```bash
docker-compose up --build
```

## ✅ 테스트

프로젝트의 테스트는 Pytest를 사용하여 작성되었습니다. 아래 명령어로 전체 테스트를 실행할 수 있습니다.

```bash
pytest
```