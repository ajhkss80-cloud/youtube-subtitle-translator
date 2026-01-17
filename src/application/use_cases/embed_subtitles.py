"""EmbedSubtitlesUseCase - 자막 삽입 유스케이스."""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from src.application.ports.subtitle_embedder import ProgressCallback, SubtitleEmbedderPort
from src.domain.entities.subtitle import Subtitle
from src.domain.entities.video import Video


class EmbedSubtitlesUseCase:
    """자막 삽입 유스케이스 (소프트섭/하드섭)"""

    def __init__(self, subtitle_embedder: SubtitleEmbedderPort) -> None:
        self._subtitle_embedder = subtitle_embedder

    def execute(
        self,
        video: Video,
        subtitle: Subtitle,
        output_path: Path,
        mode: Literal["soft", "hard"] = "soft",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Video:
        """영상에 자막 삽입"""
        embedded_path = self._subtitle_embedder.embed(
            video=video,
            subtitle=subtitle,
            output_path=output_path,
            mode=mode,
            progress_callback=progress_callback,
        )
        
        # 새로운 Video 엔티티 반환 (파일 경로 업데이트)
        # 주의: Video 엔티티 정의에 subtitles 필드가 없으므로 포함하지 않음.
        return Video(
            video_id=video.video_id,
            source_url=video.source_url,
            file_path=embedded_path,
            title=video.title
        )
