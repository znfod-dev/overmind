"""Custom exceptions and error codes"""

from enum import Enum
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ErrorCode(str, Enum):
    """에러 코드 정의"""

    # Authentication errors (1xxx)
    INVALID_CREDENTIALS = "AUTH_1001"
    EMAIL_ALREADY_EXISTS = "AUTH_1002"
    ACCOUNT_INACTIVE = "AUTH_1003"
    ACCOUNT_BLOCKED = "AUTH_1004"
    INVALID_TOKEN = "AUTH_1005"
    TOKEN_EXPIRED = "AUTH_1006"
    INSUFFICIENT_PERMISSIONS = "AUTH_1007"

    # User/Profile errors (2xxx)
    USER_NOT_FOUND = "USER_2001"
    PROFILE_NOT_FOUND = "USER_2002"
    INVALID_PROFILE_DATA = "USER_2003"

    # Conversation errors (3xxx)
    CONVERSATION_NOT_FOUND = "CONV_3001"
    CONVERSATION_NOT_ACTIVE = "CONV_3002"
    CONVERSATION_ALREADY_COMPLETED = "CONV_3003"

    # Diary errors (4xxx)
    DIARY_NOT_FOUND = "DIARY_4001"
    CONVERSATION_NO_MESSAGES = "DIARY_4002"
    DIARY_GENERATION_FAILED = "DIARY_4003"
    INVALID_DATE_FORMAT = "DIARY_4004"
    FUTURE_DIARY_NOT_ALLOWED = "DIARY_4005"
    INSUFFICIENT_CONVERSATION = "DIARY_4006"

    # AI Service errors (5xxx)
    AI_SERVICE_TIMEOUT = "AI_5001"
    AI_SERVICE_ERROR = "AI_5002"
    AI_SERVICE_UNAVAILABLE = "AI_5003"
    AI_PRIORITY_NOT_FOUND = "AI_5004"

    # Subscription errors (6xxx)
    SUBSCRIPTION_NOT_FOUND = "SUB_6001"
    SUBSCRIPTION_EXPIRED = "SUB_6002"
    UPGRADE_REQUIRED = "SUB_6003"

    # Validation errors (9xxx)
    INVALID_REQUEST = "VAL_9001"
    VALIDATION_ERROR = "VAL_9002"


class AppException(HTTPException):
    """
    커스텀 애플리케이션 예외

    클라이언트가 에러를 구분할 수 있도록 error_code를 포함합니다.
    """

    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}

        detail = {
            "error_code": error_code.value,
            "message": message,
            "details": self.details
        }

        super().__init__(status_code=status_code, detail=detail)


# 자주 사용하는 에러들을 미리 정의
class AuthenticationError(AppException):
    """인증 에러"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=message,
            details=details
        )


class NotFoundError(AppException):
    """리소스를 찾을 수 없음"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            message=message,
            details=details
        )


class BadRequestError(AppException):
    """잘못된 요청"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=message,
            details=details
        )


class ServiceError(AppException):
    """서비스 에러 (5xx)"""
    def __init__(self, error_code: ErrorCode, message: str, details: Optional[Dict] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=message,
            details=details
        )
