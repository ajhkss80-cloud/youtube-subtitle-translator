"""Subtitle - Domain Value Object for subtitle content."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from src.domain.value_objects.video_id import VideoId


@dataclass(frozen=True, slots=True)
class Subtitle:
    """자막 값 객체 (Value Object)"""
    video_id: VideoId
    language: str
    format: Literal["srt", "vtt"]
    file_path: Optional[Path] = None
    text: Optional[str] = None
    source_language: Optional[str] = None  # None이면 원본, 값이 있으면 번역됨
    source: Literal["download", "whisper", "manual"] = "download"

    @property
    def is_translated(self) -> bool:
        """source_language가 있으면 번역된 자막"""
        return self.source_language is not None

    def validate(self) -> None:
        """자막 유효성 검증"""
        if not self.language.strip():
            raise ValueError("language cannot be empty")
        if self.text is not None and not self.text.strip():
            raise ValueError("subtitle text cannot be empty if provided")
        if self.file_path is None and self.text is None:
            raise ValueError("either file_path or text must be provided")
    
    def with_translation(self, translated_text: str, target_language: str) -> "Subtitle":
        """번역된 새 Subtitle 반환"""
        return Subtitle(
            video_id=self.video_id,
            language=target_language,
            format=self.format,
            file_path=None,
            text=translated_text,
            source_language=self.language,
            source="manual",
        )
