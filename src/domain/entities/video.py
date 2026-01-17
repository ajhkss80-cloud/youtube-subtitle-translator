"""Video - Domain Entity for downloaded video."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Sequence

from src.domain.value_objects.video_id import VideoId

if TYPE_CHECKING:
    from src.domain.entities.subtitle import Subtitle


@dataclass(slots=True)
class Video:
    """다운로드된 영상 엔티티"""
    video_id: VideoId
    source_url: str
    file_path: Optional[Path] = None
    title: Optional[str] = None
    subtitles: Sequence["Subtitle"] = field(default_factory=tuple)
    has_embedded_subtitle: bool = False

    def with_subtitles(self, subtitles: Sequence["Subtitle"]) -> "Video":
        """자막이 추가된 새 Video 반환 (불변성 유지)"""
        return Video(
            video_id=self.video_id,
            source_url=self.source_url,
            file_path=self.file_path,
            title=self.title,
            subtitles=tuple(subtitles),
            has_embedded_subtitle=self.has_embedded_subtitle,
        )
    
    def with_file_path(self, path: Path) -> "Video":
        """파일 경로가 설정된 새 Video 반환"""
        return Video(
            video_id=self.video_id,
            source_url=self.source_url,
            file_path=path,
            title=self.title,
            subtitles=self.subtitles,
            has_embedded_subtitle=self.has_embedded_subtitle,
        )
