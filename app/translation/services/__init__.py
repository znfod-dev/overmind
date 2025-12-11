"""Translation services package"""

from app.translation.services.prompts import LANGUAGE_INFO, LANGUAGE_NAMES
from app.translation.services.translator import TranslationService

__all__ = ["TranslationService", "LANGUAGE_NAMES", "LANGUAGE_INFO"]
