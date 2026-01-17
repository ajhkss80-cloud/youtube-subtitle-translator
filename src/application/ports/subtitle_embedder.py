"""SubtitleEmbedderPort - Interface for subtitle embedding."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Literal, Optional

from src.domain.entities.video import Video
from src.domain.entities.subtitle import Subtitle


# Progress callback: (message: str, percent: float) -> None
ProgressCallback = Callable[[str, float], None]


class SubtitleEmbedderPort(ABC):
    """자막 삽입 인터페이스"""
    
    @abstractmethod
    def embed(
        self, 
        video: Video, 
        subtitle: Subtitle, 
        output_path: Path, 
        mode: Literal["soft", "hard"] = "soft",
        progress_callback: Optional[ProgressCallback] = None
    ) -> Path:
        """영상에 자막 삽입 후 출력 파일 경로 반환"""
        pass
