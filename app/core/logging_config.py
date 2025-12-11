"""로깅 설정"""

import os
import logging
import sys
from pathlib import Path

# 로그 포맷
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """로깅 설정 초기화"""

    # 루트 로거 설정
    logger = logging.getLogger("overmind")
    logger.setLevel(logging.INFO)

    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()

    # 환경 감지: Cloud Run은 K_SERVICE 환경 변수 존재
    is_cloud_run = os.getenv("K_SERVICE") is not None

    if is_cloud_run:
        # Cloud Run: 콘솔만 (Cloud Logging 자동 수집)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        )
        logger.addHandler(console_handler)

        logger.info("Logging configured for Cloud Run (stdout only)")

    else:
        # 로컬: 파일 + 콘솔
        LOG_DIR = Path("logs")
        LOG_DIR.mkdir(exist_ok=True)

        # 파일 핸들러 (모든 로그)
        file_handler = logging.FileHandler(
            LOG_DIR / "app.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        )

        # 에러 파일 핸들러 (ERROR 이상만)
        error_handler = logging.FileHandler(
            LOG_DIR / "error.log",
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        )

        # 콘솔 핸들러 (개발용)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        )

        # 핸들러 추가
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(console_handler)

        logger.info("Logging configured for local environment (file + console)")

    return logger


# 전역 로거
logger = setup_logging()
