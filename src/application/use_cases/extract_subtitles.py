"""ExtractSubtitlesUseCase - 자막 추출 유스케이스."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.application.ports.subtitle_extractor import ProgressCallback, SubtitleExtractorPort
from src.domain.entities.subtitle import Subtitle
from src.domain.entities.video import Video


class ExtractSubtitlesUseCase:
    """자막 추출 유스케이스 (기존 자막 또는 STT)"""

    def __init__(self, subtitle_extractor: SubtitleExtractorPort) -> None:
        self._subtitle_extractor = subtitle_extractor

    def execute(
        self,
        video: Video,
        output_path: Path,
        language: str = "ko",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Subtitle:
        """영상에서 자막 추출"""
        return self._subtitle_extractor.extract(
            video=video,
            output_path=output_path,
            language=language,
            progress_callback=progress_callback,
        )
