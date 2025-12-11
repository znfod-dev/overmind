#!/usr/bin/env python3
"""서버 시작 스크립트 - 로컬/프로덕션 환경 자동 감지"""

import os
import sys
import multiprocessing
from pathlib import Path
import uvicorn

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 작업 디렉토리를 프로젝트 루트로 변경
os.chdir(project_root)


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


def main():
    env = detect_environment()
    port = int(os.getenv("PORT", "8000"))

    if env == "local":
        print(f"🚀 Starting server in LOCAL mode on port {port}")
        print(f"📍 Access: http://localhost:{port}")
        print(f"📖 API Docs: http://localhost:{port}/docs")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
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
