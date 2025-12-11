"""Translation prompt templates"""

from typing import Dict

# Language name mapping
LANGUAGE_NAMES: Dict[str, str] = {
    "ko": "Korean",
    "vi": "Vietnamese",
    "en": "English",
    "zh": "Chinese",
    "ru": "Russian",
}

# Language info for API response
LANGUAGE_INFO = [
    {"code": "ko", "name": "Korean", "native_name": "한국어"},
    {"code": "vi", "name": "Vietnamese", "native_name": "Tiếng Việt"},
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "zh", "name": "Chinese", "native_name": "中文"},
    {"code": "ru", "name": "Russian", "native_name": "Русский"},
]


def create_translation_prompt(
    text: str,
    source_lang: str,
    target_lang: str,
    use_json_output: bool = True,
) -> str:
    """
    Create translation prompt for AI models

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        use_json_output: Whether to request JSON output

    Returns:
        Formatted translation prompt
    """
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang.upper())
    target_name = LANGUAGE_NAMES.get(target_lang, target_lang.upper())

    if use_json_output:
        # Request structured JSON output for easier parsing
        prompt = f"""You are a professional translator. Translate the following text from {source_name} to {target_name}.

**Instructions:**
1. Provide an accurate, natural translation that preserves the original meaning and tone
2. Maintain any formatting (line breaks, punctuation)
3. Do NOT add explanations or notes
4. Respond ONLY with valid JSON in this exact format:

{{
  "translated_text": "your translation here"
}}

**Text to translate:**
{text}

**Response (JSON only):**"""
    else:
        # Simple text output (fallback for models without good JSON support)
        prompt = f"""You are a professional translator. Translate the following text from {source_name} to {target_name}.

Provide ONLY the translation, without any explanations or additional text.

Text to translate:
{text}

Translation:"""

    return prompt
