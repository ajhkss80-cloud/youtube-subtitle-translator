"""VideoDownloaderPort - Interface for video downloading."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional

from src.domain.value_objects.video_id import VideoId
from src.domain.entities.video import Video


# Progress callback: (message: str, percent: float) -> None
ProgressCallback = Callable[[str, float], None]


class VideoDownloaderPort(ABC):
    """영상 다운로드 인터페이스"""
    
    @abstractmethod
    def download(
        self, 
        url: str, 
        output_dir: Path, 
        progress_callback: Optional[ProgressCallback] = None
    ) -> Video:
        """URL에서 영상 다운로드 후 Video 엔티티 반환"""
        pass
    
    @abstractmethod
    def extract_video_id(self, url: str) -> VideoId:
        """URL에서 VideoId 추출"""
        pass
