# GCP Cloud SQL (PostgreSQL) 설정 가이드

이 가이드는 Overmind AI Gateway를 GCP Cloud SQL PostgreSQL과 연결하는 방법을 설명합니다.

## 📋 목차

1. [Cloud SQL 인스턴스 생성](#1-cloud-sql-인스턴스-생성)
2. [데이터베이스 및 사용자 설정](#2-데이터베이스-및-사용자-설정)
3. [Cloud Run과 연결](#3-cloud-run과-연결)
4. [로컬 개발 환경 설정](#4-로컬-개발-환경-설정)
5. [데이터 마이그레이션](#5-데이터-마이그레이션)
6. [문제 해결](#6-문제-해결)

---

## 1. Cloud SQL 인스턴스 생성

### 방법 A: GCP Console 사용 (권장 - 초보자용)

1. **GCP Console 접속**
   - https://console.cloud.google.com/ 접속
   - 프로젝트 선택

2. **Cloud SQL 페이지 이동**
   - 좌측 메뉴에서 "SQL" 검색 또는 선택
   - "인스턴스 만들기" 클릭

3. **PostgreSQL 선택**
   - "PostgreSQL" 선택
   - "다음" 클릭

4. **인스턴스 설정**
   ```
   인스턴스 ID: overmind-db
   비밀번호: [강력한 비밀번호 생성]
   데이터베이스 버전: PostgreSQL 15
   리전: asia-northeast3 (서울)
   영역 가용성: 단일 영역 (개발용) 또는 여러 영역 (프로덕션용)
   ```

5. **머신 구성**
   - **개발/테스트용**:
     - Shared core (공유 코어)
     - 1 vCPU, 0.614GB 메모리
     - 비용: 월 ~$10

   - **프로덕션용**:
     - Dedicated core (전용 코어)
     - 1 vCPU, 3.75GB 메모리
     - 비용: 월 ~$50

6. **스토리지**
   ```
   스토리지 유형: SSD
   스토리지 용량: 10GB (시작)
   자동 증가: 체크 (권장)
   ```

7. **연결**
   - "Private IP" 체크 해제 (Cloud Run 사용 시 불필요)
   - "Public IP" 체크 (관리용, 나중에 제거 가능)

8. **백업**
   - 자동 백업: 활성화 (프로덕션 필수)
   - 백업 시간: 새벽 시간 권장

9. **생성**
   - "인스턴스 만들기" 클릭
   - 생성 완료까지 5-10분 소요

### 방법 B: gcloud CLI 사용 (빠른 방법)

```bash
# Cloud SQL 인스턴스 생성
gcloud sql instances create overmind-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --root-password=YOUR_STRONG_PASSWORD
```

**인스턴스 생성 확인:**
```bash
gcloud sql instances list
```

---

## 2. 데이터베이스 및 사용자 설정

### 데이터베이스 생성

```bash
gcloud sql databases create overmind \
  --instance=overmind-db
```

### 사용자 생성

```bash
# PostgreSQL 사용자 생성
gcloud sql users create overmind-user \
  --instance=overmind-db \
  --password=YOUR_USER_PASSWORD
```

**💡 비밀번호 보안 팁:**
- 최소 16자 이상
- 대소문자, 숫자, 특수문자 포함
- 생성 도구: `openssl rand -base64 24`

### 연결 확인

```bash
# 인스턴스 정보 확인
gcloud sql instances describe overmind-db

# 연결 이름 확인 (중요!)
gcloud sql instances describe overmind-db --format="value(connectionName)"
```

**출력 예시:**
```
my-project-123456:asia-northeast3:overmind-db
```
이 연결 이름을 DATABASE_URL에 사용합니다.

---

## 3. Cloud Run과 연결

### 환경변수 설정

`.env` 파일 또는 Cloud Run 환경변수에 DATABASE_URL 설정:

```bash
# Unix Socket 방식 (Cloud Run 권장)
DATABASE_URL=postgresql+asyncpg://overmind-user:YOUR_PASSWORD@/overmind?host=/cloudsql/PROJECT_ID:asia-northeast3:overmind-db
```

**예시:**
```bash
DATABASE_URL=postgresql+asyncpg://overmind-user:MySecurePass123!@/overmind?host=/cloudsql/my-project-123456:asia-northeast3:overmind-db
```

### scripts/deploy.py 업데이트

`scripts/deploy.py` 파일을 다음과 같이 수정:

```python
# deploy 함수에서 추가
deploy_cmd = f"""gcloud run deploy {SERVICE_NAME} \\
  --source . \\
  --platform managed \\
  --region {REGION} \\
  --allow-unauthenticated \\
  --env-vars-file .env.yaml \\
  --add-cloudsql-instances=PROJECT_ID:asia-northeast3:overmind-db \\
  --timeout 300 \\
  --memory 512Mi \\
  --cpu 1 \\
  --min-instances 0 \\
  --max-instances 10
"""
```

**자동 배포:**
```bash
python scripts/deploy.py
```

### 수동 배포 (gcloud 직접 사용)

```bash
gcloud run deploy overmind-ai-gateway \
  --source . \
  --region=asia-northeast3 \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=postgresql+asyncpg://overmind-user:PASSWORD@/overmind?host=/cloudsql/PROJECT_ID:REGION:overmind-db" \
  --add-cloudsql-instances=PROJECT_ID:asia-northeast3:overmind-db
```

---

## 4. 로컬 개발 환경 설정

로컬에서 Cloud SQL에 연결하려면 **Cloud SQL Proxy**를 사용합니다.

### Cloud SQL Proxy 설치

**macOS:**
```bash
brew install cloud-sql-proxy
```

**Linux:**
```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy
sudo mv cloud-sql-proxy /usr/local/bin/
```

### Cloud SQL Proxy 실행

**터미널 1 (Proxy 실행):**
```bash
cloud-sql-proxy PROJECT_ID:asia-northeast3:overmind-db
```

프록시가 `127.0.0.1:5432`에서 실행됩니다.

**터미널 2 (앱 실행):**
```bash
# .env 파일 설정
DATABASE_URL=postgresql+asyncpg://overmind-user:PASSWORD@localhost:5432/overmind

# 앱 실행
uvicorn app.main:app --reload
```

### 대안: psql로 직접 연결

```bash
psql "host=127.0.0.1 port=5432 sslmode=disable dbname=overmind user=overmind-user"
```

---

## 5. 데이터 마이그레이션

### SQLite에서 PostgreSQL로 데이터 이동

#### 옵션 1: pgloader 사용 (권장)

```bash
# pgloader 설치 (macOS)
brew install pgloader

# 마이그레이션 실행
pgloader data/overmind.db postgresql://overmind-user:PASSWORD@localhost:5432/overmind
```

#### 옵션 2: 수동 Export/Import

**1. SQLite에서 데이터 덤프:**
```bash
sqlite3 data/overmind.db .dump > overmind_dump.sql
```

**2. PostgreSQL 형식으로 변환:**
```bash
# SQLite 특수 구문 제거
sed -i '' 's/AUTOINCREMENT/SERIAL/g' overmind_dump.sql
sed -i '' '/^PRAGMA/d' overmind_dump.sql
```

**3. PostgreSQL에 Import:**
```bash
psql "postgresql://overmind-user:PASSWORD@localhost:5432/overmind" < overmind_dump.sql
```

#### 옵션 3: Python 스크립트로 마이그레이션

새 스크립트 생성: `scripts/migrate_to_postgres.py`

```python
#!/usr/bin/env python3
"""SQLite → PostgreSQL 데이터 마이그레이션"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base

async def migrate():
    # SQLite 연결
    sqlite_url = "sqlite+aiosqlite:///./data/overmind.db"

    # PostgreSQL 연결 (환경변수에서)
    from app.config import settings
    postgres_url = settings.database_url

    print(f"Migrating from SQLite to PostgreSQL...")
    print(f"Source: {sqlite_url}")
    print(f"Target: {postgres_url}")

    # TODO: 실제 데이터 복사 로직 추가
    # (테이블별로 SELECT → INSERT)

if __name__ == "__main__":
    asyncio.run(migrate())
```

### 테이블 자동 생성

FastAPI 앱이 실행되면 자동으로 테이블이 생성됩니다:

```python
# app/database/config.py의 init_db() 함수가 자동 실행
await conn.run_sync(Base.metadata.create_all)
```

---

## 6. 문제 해결

### 연결 오류: "could not connect to server"

**원인:** Cloud SQL 인스턴스가 실행 중이 아니거나 연결 이름이 잘못됨

**해결:**
```bash
# 인스턴스 상태 확인
gcloud sql instances describe overmind-db --format="value(state)"

# 인스턴스 시작
gcloud sql instances patch overmind-db --activation-policy=ALWAYS
```

### 인증 오류: "password authentication failed"

**원인:** 잘못된 사용자명 또는 비밀번호

**해결:**
```bash
# 비밀번호 재설정
gcloud sql users set-password overmind-user \
  --instance=overmind-db \
  --password=NEW_PASSWORD
```

### Cloud Run에서 연결 안됨

**확인사항:**
1. `--add-cloudsql-instances` 플래그가 배포 시 포함되었는지 확인
2. DATABASE_URL에 `/cloudsql/...` Unix socket 경로 사용
3. Cloud Run 서비스 계정이 Cloud SQL 접근 권한 있는지 확인

```bash
# 서비스 계정에 Cloud SQL Client 역할 추가
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

### 성능 문제

**연결 풀 최적화:**

`app/database/config.py`에서 조정:
```python
engine_kwargs.update({
    "pool_size": 10,      # 동시 연결 수 증가
    "max_overflow": 20,   # 초과 연결 허용
    "pool_pre_ping": True,
    "pool_recycle": 1800, # 30분마다 재생성
})
```

### 비용 절감 팁

**개발 환경:**
```bash
# 사용하지 않을 때 자동 정지
gcloud sql instances patch overmind-db \
  --activation-policy=NEVER

# 다시 시작
gcloud sql instances patch overmind-db \
  --activation-policy=ALWAYS
```

**프로덕션 환경:**
- 백업 보관 기간 조정 (7일 → 3일)
- 고가용성 비활성화 (개발 초기)
- 인스턴스 크기 모니터링 후 조정

---

## 📊 비용 예상

| 구성 | 월 예상 비용 (USD) |
|------|------------------|
| db-f1-micro (개발용) | $10-15 |
| db-g1-small (소규모) | $25-35 |
| db-n1-standard-1 (프로덕션) | $50-70 |
| 스토리지 (10GB SSD) | $2 |
| 백업 (10GB) | $0.08 |

**총계 (개발):** 약 $12-17/월
**총계 (프로덕션):** 약 $52-72/월

---

## ✅ 체크리스트

설정 완료 확인:

- [ ] Cloud SQL 인스턴스 생성 완료
- [ ] 데이터베이스 `overmind` 생성
- [ ] 사용자 `overmind-user` 생성
- [ ] 연결 이름 확인 및 기록
- [ ] `.env` 파일에 DATABASE_URL 설정
- [ ] 로컬에서 Cloud SQL Proxy로 연결 테스트
- [ ] 테이블 자동 생성 확인 (`uvicorn app.main:app`)
- [ ] Cloud Run 배포 시 `--add-cloudsql-instances` 추가
- [ ] 배포 후 헬스체크 성공 확인 (`/health`)
- [ ] 데이터 마이그레이션 (SQLite → PostgreSQL)
- [ ] 백업 설정 확인

---

## 🚀 빠른 시작 명령어 모음

```bash
# 1. Cloud SQL 생성
gcloud sql instances create overmind-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-northeast3

# 2. 데이터베이스 생성
gcloud sql databases create overmind --instance=overmind-db

# 3. 사용자 생성
gcloud sql users create overmind-user \
  --instance=overmind-db \
  --password=$(openssl rand -base64 24)

# 4. 연결 이름 확인
gcloud sql instances describe overmind-db \
  --format="value(connectionName)"

# 5. 로컬 테스트 (Cloud SQL Proxy)
cloud-sql-proxy PROJECT_ID:asia-northeast3:overmind-db

# 6. 배포
python scripts/deploy.py
```

---

## 📚 참고 자료

- [Cloud SQL 공식 문서](https://cloud.google.com/sql/docs)
- [Cloud Run + Cloud SQL 연결](https://cloud.google.com/sql/docs/postgres/connect-run)
- [SQLAlchemy PostgreSQL 설정](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [asyncpg 문서](https://magicstack.github.io/asyncpg/)

---

**작성일:** 2025-12-18
**버전:** 1.0
