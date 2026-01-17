"""DownloadVideoUseCase - 영상 다운로드 유스케이스."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.application.ports.video_downloader import ProgressCallback, VideoDownloaderPort
from src.domain.entities.video import Video


class DownloadVideoUseCase:
    """YouTube 영상 다운로드 유스케이스"""

    def __init__(self, video_downloader: VideoDownloaderPort) -> None:
        self._video_downloader = video_downloader

    def execute(
        self,
        url: str,
        output_dir: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Video:
        """URL에서 영상 다운로드"""
        return self._video_downloader.download(
            url=url,
            output_dir=output_dir,
            progress_callback=progress_callback,
        )
