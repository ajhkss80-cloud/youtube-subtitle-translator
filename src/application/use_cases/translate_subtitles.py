"""TranslateSubtitlesUseCase - 자막 번역 유스케이스."""
from __future__ import annotations

from typing import Optional

from src.application.ports.subtitle_translator import (
    ProgressCallback,
    SubtitleTranslatorPort,
)
from src.domain.entities.subtitle import Subtitle


class TranslateSubtitlesUseCase:
    """자막 번역 유스케이스"""

    def __init__(self, subtitle_translator: SubtitleTranslatorPort) -> None:
        """
        Args:
            subtitle_translator: 자막 번역 포트 구현체
        """
        self._subtitle_translator = subtitle_translator

    def execute(
        self,
        subtitle: Subtitle,
        target_language: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Subtitle:
        """자막 번역 실행

        Args:
            subtitle: 원본 자막 객체
            target_language: 목표 언어 코드 (예: "en", "ko", "ja")
            progress_callback: 진행 상황 콜백 함수

        Returns:
            번역된 Subtitle 객체

        Raises:
            ValueError: 지원하지 않는 언어 또는 형식
            RuntimeError: 번역 엔진 오류
        """
        # 자막 유효성 검증
        subtitle.validate()

        # 번역 실행
        translated_subtitle = self._subtitle_translator.translate(
            subtitle=subtitle,
            target_language=target_language,
            progress_callback=progress_callback,
        )

        # 번역된 자막 유효성 검증
        translated_subtitle.validate()

        return translated_subtitle
