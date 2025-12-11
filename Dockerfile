# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# 빌더에서 설치된 패키지 복사
COPY --from=builder /root/.local /root/.local

# 애플리케이션 코드 복사
COPY app ./app
COPY scripts/start.py ./start.py

# 로그 디렉토리 생성
RUN mkdir -p logs

# PATH 설정
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 포트 노출
EXPOSE 8080

# 실행 (Cloud Run은 PORT 환경 변수로 포트 지정)
CMD ["python3", "start.py"]
