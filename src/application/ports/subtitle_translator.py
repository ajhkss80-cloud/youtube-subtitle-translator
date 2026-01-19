"""SubtitleTranslatorPort - Interface for subtitle translation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from src.domain.entities.subtitle import Subtitle


# Progress callback: (message: str, percent: float) -> None
ProgressCallback = Callable[[str, float], None]


class SubtitleTranslatorPort(ABC):
    """자막 번역 인터페이스"""

    @abstractmethod
    def translate(
        self,
        subtitle: Subtitle,
        target_language: str,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Subtitle:
        """자막을 대상 언어로 번역하여 새로운 Subtitle 반환

        Args:
            subtitle: 원본 자막 (Subtitle 객체)
            target_language: 목표 언어 코드 (예: "en", "ko", "ja")
            progress_callback: 진행 상황 콜백 함수

        Returns:
            번역된 Subtitle 객체 (source_language 필드에 원본 언어 기록)

        Raises:
            ValueError: 지원하지 않는 언어 또는 자막 형식
            RuntimeError: 번역 엔진 오류
        """
        pass

    @abstractmethod
    def list_supported_languages(self) -> List[str]:
        """지원하는 언어 목록 반환

        Returns:
            언어 코드 리스트 (예: ["en", "ko", "ja", "zh"])
        """
        pass

    @abstractmethod
    def is_language_pair_supported(
        self,
        source_language: str,
        target_language: str
    ) -> bool:
        """특정 언어 쌍의 번역 지원 여부 확인

        Args:
            source_language: 원본 언어 코드
            target_language: 목표 언어 코드

        Returns:
            지원 여부 (True/False)
        """
        pass
