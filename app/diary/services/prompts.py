"""AI prompt templates for diary service"""

from typing import Optional
from datetime import date, datetime


def create_conversation_prompt(
    user_message: str,
    conversation_history: list[dict],
    profile: Optional[dict] = None
) -> str:
    """
    Create AI prompt for diary conversation

    Args:
        user_message: Latest user message
        conversation_history: Previous messages [{"role": "ai"|"user", "content": str}]
        profile: User profile data (nickname, job, hobbies, etc.)

    Returns:
        Formatted prompt for AI
    """
    # Build profile context
    profile_context = ""
    if profile:
        parts = []
        if profile.get("nickname"):
            parts.append(f"닉네임: {profile['nickname']}")
        if profile.get("job"):
            parts.append(f"직업: {profile['job']}")
        if profile.get("hobbies"):
            parts.append(f"취미: {profile['hobbies']}")
        if profile.get("family_composition"):
            parts.append(f"가족: {profile['family_composition']}")
        if profile.get("pets"):
            parts.append(f"반려동물: {profile['pets']}")

        if parts:
            profile_context = f"\n\n사용자 프로필:\n" + "\n".join(f"- {p}" for p in parts)

    # Build conversation history
    history_text = ""
    if conversation_history:
        history_parts = []
        for msg in conversation_history[-10:]:  # Last 10 messages
            role = "AI" if msg["role"] == "ai" else "사용자"
            history_parts.append(f"{role}: {msg['content']}")
        history_text = "\n\n이전 대화:\n" + "\n".join(history_parts)

    prompt = f"""당신은 친근하고 공감을 잘하는 일기 도우미 AI입니다.
사용자와 대화하면서 하루 일과를 자연스럽게 수집하고, 적절한 공감과 꼬리 질문을 통해 대화를 이어갑니다.

역할:
- 친근하고 따뜻한 말투 사용
- 사용자의 감정에 공감
- 하루 일과에 대해 자연스럽게 질문 (출근/퇴근, 점심, 특별한 일, 감정 등)
- 간결하고 자연스러운 응답 (1-3문장)
- 질문은 한 번에 하나씩

응답 스타일:
- "오늘 하루 어떠셨어요?"
- "점심은 뭐 드셨어요?"
- "그랬구나! 기분이 어떠셨어요?"
- "더 얘기하고 싶은 게 있으세요?"{profile_context}{history_text}

사용자의 최신 메시지:
{user_message}

위 메시지에 공감하고, 자연스러운 꼬리 질문을 1-2개 해주세요.
응답만 출력하고, 다른 설명은 하지 마세요."""

    return prompt


def create_diary_generation_prompt(
    conversation_messages: list[dict],
    length_type: str,
    entry_date: datetime,
    profile: Optional[dict] = None
) -> str:
    """
    Create AI prompt for generating diary entry

    Args:
        conversation_messages: Full conversation history
        length_type: "summary" | "normal" | "detailed"
        entry_date: Date of diary entry
        profile: User profile data

    Returns:
        Formatted prompt for diary generation
    """
    # Format conversation
    conversation_text = ""
    for msg in conversation_messages:
        role = "AI" if msg["role"] == "ai" else "나"
        conversation_text += f"{role}: {msg['content']}\n"

    # Length guidelines
    length_guide = {
        "summary": "5-10줄의 간단한 요약본",
        "normal": "20-30줄의 일반 일기",
        "detailed": "50줄 이상의 상세한 일기"
    }

    # Profile context
    profile_note = ""
    if profile and profile.get("nickname"):
        profile_note = f"\n(일기 작성 시 사용자를 '{profile['nickname']}'이라고 부르지 말고, '나'로 작성)"

    date_str = entry_date.strftime("%Y년 %m월 %d일 %A")

    prompt = f"""다음은 사용자와 AI가 나눈 하루 일과 대화입니다.
이 대화 내용을 바탕으로 자연스러운 일기를 작성해주세요.

대화 내용:
{conversation_text}

일기 작성 요구사항:
- 날짜: {date_str}
- 분량: {length_guide.get(length_type, '일반 일기')}
- 시간 순서대로 정리
- 사용자의 감정과 생각 반영
- 자연스러운 일기 형식
- 1인칭 ('나', '내가') 사용{profile_note}

일기 내용만 출력하고, 다른 설명은 하지 마세요.
날짜를 맨 위에 포함해주세요."""

    return prompt


def create_mood_analysis_prompt(diary_content: str) -> str:
    """
    Create prompt for analyzing mood from diary content

    Args:
        diary_content: Generated diary text

    Returns:
        Formatted prompt for mood analysis
    """
    prompt = f"""다음 일기 내용에서 작성자의 전반적인 감정 상태를 분석해주세요.

일기 내용:
{diary_content}

다음 중 하나로만 답변해주세요:
- 긍정적
- 부정적
- 중립
- 복합적 (긍정과 부정이 섞임)

한 단어로만 답변하고, 다른 설명은 하지 마세요."""

    return prompt


def create_summary_prompt(diary_content: str) -> str:
    """
    Create prompt for summarizing diary

    Args:
        diary_content: Generated diary text

    Returns:
        Formatted prompt for summary generation
    """
    prompt = f"""다음 일기 내용을 1-2문장으로 요약해주세요.

일기 내용:
{diary_content}

요구사항:
- 1-2문장으로 핵심 내용 요약
- 자연스러운 한국어
- 요약만 출력하고 다른 설명은 하지 마세요

요약:"""

    return prompt


def create_initial_greeting_prompt(entry_date: date, current_time: datetime) -> str:
    """
    Create prompt for AI to generate contextual initial greeting

    AI generates a greeting based on:
    - Time of day (morning/afternoon/evening)
    - Entry date context (today/yesterday/past)

    Args:
        entry_date: Date for the diary entry
        current_time: Client's current local time (timezone-aware)

    Returns:
        Formatted prompt for greeting generation
    """
    # Determine time of day
    hour = current_time.hour
    if 5 <= hour < 12:
        time_of_day = "아침"
        time_context = "아침이 시작되었고"
    elif 12 <= hour < 18:
        time_of_day = "점심"
        time_context = "점심 시간이 지나가고 있고"
    else:
        time_of_day = "저녁"
        time_context = "하루가 저물어가고 있고"

    # Determine date context
    today = current_time.date()
    days_diff = (today - entry_date).days

    if entry_date == today:
        date_context = "오늘"
        date_instruction = "오늘 하루에 대해 물어보세요"
    elif days_diff == 1:
        date_context = "어제"
        date_instruction = "어제 하루에 대해 물어보세요"
    elif days_diff == 2:
        date_context = "그저께"
        date_instruction = "그저께 하루에 대해 물어보세요"
    elif days_diff <= 7:
        date_context = f"{entry_date.month}월 {entry_date.day}일"
        date_instruction = f"{date_context}의 하루에 대해 물어보세요"
    else:
        date_context = f"{entry_date.month}월 {entry_date.day}일"
        date_instruction = f"{date_context}을 기억해보며 그날의 일들에 대해 물어보세요"

    prompt = f"""당신은 친근하고 공감을 잘하는 일기 도우미 AI입니다.

현재 상황:
- 시간대: {time_of_day} ({time_context})
- 일기 날짜: {date_context}

사용자와 대화를 시작하기 위한 자연스러운 인사말을 생성해주세요.
시간대와 날짜를 고려하여, 짧은 인사말과 함께 {date_instruction}.

요구사항:
- 1-2개의 질문만 포함
- 자연스럽고 친근한 톤
- 응답만 출력하고, 다른 설명은 하지 마세요

출력 예시:
"안녕하세요! 오늘 하루는 어떠셨나요?"

인사말:"""

    return prompt
