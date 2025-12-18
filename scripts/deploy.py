#!/usr/bin/env python3
"""GCP Cloud Run 배포 자동화 스크립트"""

import os
import subprocess
import sys
from pathlib import Path

# ============================================================
# 배포 설정 (여기를 수정하세요!)
# ============================================================
PROJECT_ID = "gen-lang-client-0151610785"  # 여기에 GCP 프로젝트 ID 입력
REGION = "asia-northeast3"  # 서울 리전
SERVICE_NAME = "overmind-ai-gateway"

# Cloud SQL 설정 (PostgreSQL 사용 시)
CLOUD_SQL_INSTANCE = "overmind-db"  # Cloud SQL 인스턴스 이름
CLOUD_SQL_CONNECTION = f"{PROJECT_ID}:{REGION}:{CLOUD_SQL_INSTANCE}"  # 자동 생성
USE_CLOUD_SQL = True  # Cloud SQL 사용 여부 (False면 SQLite 사용)

# 색상 코드
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_step(msg):
    print(f"\n{GREEN}▶ {msg}{RESET}")


def print_info(msg):
    print(f"{BLUE}ℹ {msg}{RESET}")


def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{RESET}")


def print_error(msg):
    print(f"\n{RED}✗ {msg}{RESET}")
    sys.exit(1)


def run_command(cmd, error_msg, silent=False):
    """명령어 실행 및 에러 처리"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        if not silent and result.stdout:
            print(result.stdout.strip())
        return result.stdout
    except subprocess.CalledProcessError as e:
        if not silent:
            print_error(f"{error_msg}\n{e.stderr}")
        else:
            print_error(error_msg)


def check_gcloud():
    """gcloud CLI 설치 확인"""
    print_step("gcloud CLI 확인 중...")
    result = subprocess.run(
        "gcloud --version",
        shell=True,
        capture_output=True
    )
    if result.returncode != 0:
        print_error(
            "gcloud CLI가 설치되지 않았습니다.\n"
            "설치: https://cloud.google.com/sdk/docs/install"
        )
    print_info("gcloud CLI 확인 완료")


def check_project_id():
    """프로젝트 ID 확인"""
    if PROJECT_ID == "your-gcp-project-id":
        print_error(
            "PROJECT_ID가 설정되지 않았습니다!\n"
            "scripts/deploy.py 파일 상단의 PROJECT_ID를 수정해주세요."
        )


def setup_gcp():
    """GCP 프로젝트 설정"""
    print_step(f"GCP 프로젝트 설정: {PROJECT_ID}")

    run_command(
        f"gcloud config set project {PROJECT_ID}",
        "GCP 프로젝트 설정 실패",
        silent=True
    )
    print_info(f"프로젝트: {PROJECT_ID}")

    run_command(
        f"gcloud config set run/region {REGION}",
        "리전 설정 실패",
        silent=True
    )
    print_info(f"리전: {REGION}")

    print_step("필요한 API 활성화 중...")
    apis = [
        ("run.googleapis.com", "Cloud Run"),
        ("cloudbuild.googleapis.com", "Cloud Build")
    ]

    for api, name in apis:
        print_info(f"  - {name} API 활성화")
        run_command(
            f"gcloud services enable {api}",
            f"{name} API 활성화 실패",
            silent=True
        )


def load_env():
    """환경 변수 로드"""
    print_step(".env 파일 로드 중...")

    env_path = Path(".env")
    if not env_path.exists():
        print_error(
            ".env 파일을 찾을 수 없습니다.\n"
            ".env.example을 참고하여 .env 파일을 생성해주세요."
        )

    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    # 필수 키 확인
    required_keys = [
        "ANTHROPIC_API_KEY",
        "GOOGLE_AI_API_KEY",
        "OPENAI_API_KEY",
        "API_AUTH_KEY"
    ]

    missing_keys = [key for key in required_keys if key not in env_vars]
    if missing_keys:
        print_warning(
            f"누락된 환경 변수: {', '.join(missing_keys)}"
        )

    print_info(f"{len(env_vars)}개의 환경 변수 로드됨")
    return env_vars




def create_env_yaml(env_vars):
    """환경 변수 YAML 파일 생성"""
    print_step("환경 변수 YAML 파일 생성 중...")

    env_yaml_path = Path(".env.yaml")

    # Cloud Run 배포용 환경 변수 복사
    deploy_env_vars = env_vars.copy()

    # AI_SERVICE_URL은 localhost로 설정 (같은 컨테이너 내에서 실행)
    deploy_env_vars["AI_SERVICE_URL"] = "http://localhost:8080"

    # INTERNAL_API_KEY가 없으면 추가
    if "INTERNAL_API_KEY" not in deploy_env_vars:
        deploy_env_vars["INTERNAL_API_KEY"] = "internal-service-key-overmind-2025"
        print_info("INTERNAL_API_KEY 자동 생성")

    with open(env_yaml_path, "w") as f:
        for key, value in deploy_env_vars.items():
            # 모든 값을 문자열로 처리 (YAML 파싱 문제 방지)
            f.write(f'{key}: "{value}"\n')

    print_info(f"{len(deploy_env_vars)}개의 환경 변수를 .env.yaml에 저장")
    print_info("AI_SERVICE_URL: http://localhost:8080 (Cloud Run 내부)")
    return env_yaml_path


def deploy():
    """Cloud Run 배포 (--source 방식)"""
    print_step(f"Cloud Run에 {SERVICE_NAME} 배포 중...")
    print_info("Cloud Build가 자동으로 이미지를 빌드합니다...")
    print_info("이 작업은 5-10분 소요될 수 있습니다...")

    # Cloud SQL 연결 설정
    cloudsql_flag = ""
    if USE_CLOUD_SQL:
        cloudsql_flag = f"--add-cloudsql-instances={CLOUD_SQL_CONNECTION}"
        print_info(f"Cloud SQL 연결: {CLOUD_SQL_CONNECTION}")

    # --source 방식: gcloud가 자동으로 빌드
    deploy_cmd = f"""gcloud run deploy {SERVICE_NAME} \\
  --source . \\
  --platform managed \\
  --region {REGION} \\
  --allow-unauthenticated \\
  --env-vars-file .env.yaml \\
  {cloudsql_flag} \\
  --timeout 300 \\
  --memory 512Mi \\
  --cpu 1 \\
  --min-instances 0 \\
  --max-instances 10
"""

    run_command(deploy_cmd, "배포 실패")


def get_service_url():
    """배포된 서비스 URL 가져오기"""
    print_step("서비스 URL 확인 중...")

    url = run_command(
        f"gcloud run services describe {SERVICE_NAME} --region {REGION} --format='value(status.url)'",
        "서비스 URL 조회 실패",
        silent=True
    ).strip()

    return url


def main():
    print(f"\n{'=' * 60}")
    print(f"{GREEN}🚀 Overmind AI Gateway - GCP Cloud Run 배포{RESET}")
    print(f"{'=' * 60}")

    # 1. 프로젝트 ID 확인
    check_project_id()

    # 2. gcloud CLI 확인
    check_gcloud()

    # 3. GCP 설정
    setup_gcp()

    # 4. 환경 변수 로드
    env_vars = load_env()

    # 5. 환경 변수 YAML 생성
    create_env_yaml(env_vars)

    # 6. Cloud Run 배포
    deploy()

    # 7. 결과 출력
    service_url = get_service_url()

    print(f"\n{'=' * 60}")
    print(f"{GREEN}✓ 배포 완료!{RESET}")
    print(f"{'=' * 60}")
    print(f"\n{YELLOW}서비스 URL:{RESET}")
    print(f"{service_url}")
    print(f"\n{YELLOW}테스트 명령어:{RESET}")
    print(f"  # 헬스체크")
    print(f"  curl {service_url}/health")
    print(f"\n  # API 테스트")
    print(f"  curl -X POST \"{service_url}/api/req\" \\")
    print(f"    -H \"Content-Type: application/json\" \\")
    print(f"    -H \"X-API-Key: <YOUR_API_KEY>\" \\")
    print(f"    -d '{{\"provider\":\"claude\",\"prompt\":\"Hello!\",\"max_tokens\":50}}'")
    print(f"\n{YELLOW}로그 확인:{RESET}")
    print(f"  gcloud run logs read {SERVICE_NAME} --region {REGION}")
    print(f"\n{YELLOW}GCP Console:{RESET}")
    print(f"  https://console.cloud.google.com/run/detail/{REGION}/{SERVICE_NAME}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}✗ 배포 취소됨{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"예상치 못한 오류: {str(e)}")
