"""SubtitleExtractorPort - Interface for subtitle extraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Optional

from src.domain.entities.video import Video
from src.domain.entities.subtitle import Subtitle


# Progress callback: (message: str, percent: float) -> None
ProgressCallback = Callable[[str, float], None]


class SubtitleExtractorPort(ABC):
    """자막 추출 인터페이스"""
    
    @abstractmethod
    def extract(
        self, 
        video: Video, 
        output_path: Path, 
        language: str = "ko",
        progress_callback: Optional[ProgressCallback] = None
    ) -> Subtitle:
        """영상에서 자막 추출 또는 STT 생성 후 Subtitle 반환"""
        pass

    @abstractmethod
    def list_available_languages(self, video: Video) -> List[str]:
        """사용 가능한 자막 언어 목록 반환"""
        pass
