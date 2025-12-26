#!/usr/bin/env python3
"""서버 시작 스크립트 - 로컬/프로덕션 환경 자동 감지"""

import os
import sys
import multiprocessing
import subprocess
import signal
import time
from pathlib import Path
import uvicorn

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 작업 디렉토리를 프로젝트 루트로 변경
os.chdir(project_root)

# Cloud SQL Proxy 프로세스를 전역으로 관리
cloud_sql_proxy_process = None


def detect_environment() -> str:
    """환경 감지: Cloud Run은 K_SERVICE 환경 변수 존재"""
    if os.getenv("K_SERVICE"):
        return "production"
    return "local"


def get_workers() -> int:
    """프로덕션 환경의 worker 수 계산"""
    cpu_count = multiprocessing.cpu_count()
    # (2 * CPU 코어 수) + 1, 최대 4개로 제한
    return min(cpu_count * 2 + 1, 4)


def cleanup_proxy(signum=None, frame=None):
    """Cloud SQL Proxy 종료"""
    global cloud_sql_proxy_process
    if cloud_sql_proxy_process:
        print("\n🛑 Stopping Cloud SQL Proxy...")
        cloud_sql_proxy_process.terminate()
        try:
            cloud_sql_proxy_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cloud_sql_proxy_process.kill()
        print("✅ Cloud SQL Proxy stopped")
    sys.exit(0)


def start_cloud_sql_proxy():
    """Cloud SQL Proxy 시작"""
    global cloud_sql_proxy_process

    instance_connection = "gen-lang-client-0151610785:asia-northeast3:overmind-nana-20251218"

    print(f"🔌 Starting Cloud SQL Proxy for {instance_connection}...")

    try:
        cloud_sql_proxy_process = subprocess.Popen(
            ["cloud-sql-proxy", instance_connection],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 프록시가 준비될 때까지 대기 (약 2-3초)
        print("⏳ Waiting for Cloud SQL Proxy to be ready...")
        time.sleep(3)

        # 프로세스가 여전히 실행 중인지 확인
        if cloud_sql_proxy_process.poll() is not None:
            # 프로세스가 시작 직후 종료된 경우, 에러 메시지 출력
            stdout, stderr = cloud_sql_proxy_process.communicate()
            error_message = "Cloud SQL Proxy failed to start.\n"
            if stdout:
                error_message += f"--- STDOUT ---\n{stdout}\n"
            if stderr:
                error_message += f"--- STDERR ---\n{stderr}\n"
            raise Exception(error_message)

        print("✅ Cloud SQL Proxy is ready")
        return True

    except FileNotFoundError:
        print("❌ Error: cloud-sql-proxy not found. Please install it first.")
        print("   Install: brew install cloud-sql-proxy")
        return False
    except Exception as e:
        print(f"❌ Error starting Cloud SQL Proxy: {e}")
        return False


def main():
    env = detect_environment()
    port = int(os.getenv("PORT", "8000"))

    if env == "local":
        # Ctrl+C 시그널 핸들러 등록
        signal.signal(signal.SIGINT, cleanup_proxy)
        signal.signal(signal.SIGTERM, cleanup_proxy)

        # Cloud SQL Proxy 시작
        if not start_cloud_sql_proxy():
            print("❌ Failed to start Cloud SQL Proxy. Exiting...")
            sys.exit(1)

        print(f"\n🚀 Starting server in LOCAL mode on port {port}")
        print(f"📍 Access: http://localhost:{port}")
        print(f"📖 API Docs: http://localhost:{port}/docs")
        print(f"💡 Press Ctrl+C to stop both server and proxy\n")

        try:
            uvicorn.run(
                "app.main:app",
                host="0.0.0.0",
                port=port,
                reload=True,
                log_level="info"
            )
        except KeyboardInterrupt:
            cleanup_proxy()
    else:
        print(f"🚀 Starting server in PRODUCTION mode on port {port}")
        # Cloud Run은 인스턴스 수를 자동 관리하므로 workers=1
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )


if __name__ == "__main__":
    main()