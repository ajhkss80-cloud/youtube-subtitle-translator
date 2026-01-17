"""YtDlpDownloader - yt-dlp 기반 영상 다운로드 어댑터."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

from src.application.ports.video_downloader import ProgressCallback, VideoDownloaderPort
from src.domain.entities.video import Video
from src.domain.value_objects.video_id import VideoId


class YtDlpDownloader(VideoDownloaderPort):
    """yt-dlp 기반 영상 다운로드 어댑터"""

    _VIDEO_ID_PATTERNS = (
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    )

    def __init__(self, yt_dlp_path: str = "yt-dlp") -> None:
        self._yt_dlp_path = yt_dlp_path

    def extract_video_id(self, url: str) -> VideoId:
        """URL에서 VideoId 추출"""
        for pattern in self._VIDEO_ID_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return VideoId(match.group(1))

        # 패턴 매칭 실패 시 fallback (md5)은 도메인 규칙상 VideoId(11자) 위반 가능성 있음
        # 하지만 기존 로직 호환성을 위해 유지하거나, strict하게 에러를 낼지 결정 필요.
        # 여기서는 기존 gui_app.py의 fallback 로직(md5 11자)을 따름.
        import hashlib
        fallback_id = hashlib.md5(url.encode()).hexdigest()[:11]
        return VideoId(fallback_id)

    def download(
        self,
        url: str,
        output_dir: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Video:
        """yt-dlp를 사용하여 영상 다운로드"""
        try:
            video_id = self.extract_video_id(url)
        except ValueError as e:
            raise ValueError(f"Invalid URL or Video ID: {url}") from e

        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 출력 템플릿: output_dir/video_id/video.mp4 (기존 호환)
        # 하지만 clean arch에서는 output_dir가 루트일 수도 있음.
        # 여기서는 target_dir = output_dir / video_id 로 설정
        target_dir = output_dir / str(video_id)
        target_dir.mkdir(exist_ok=True)
        
        output_template = str(target_dir / "video.%(ext)s")

        cmd = [
            self._yt_dlp_path,
            "--no-warnings",
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--output", output_template,
            url,
        ]

        if progress_callback:
            progress_callback(f"Downloading {video_id}...", 0.0)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # stdout 파싱하여 진행률 표시 (간소화)
        if process.stdout:
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    try:
                        # 예: [download] 12.5% of ...
                        parts = line.split()
                        percent_str = next((p for p in parts if "%" in p), None)
                        if percent_str:
                            # 12.5% -> 12.5
                            percent = float(percent_str.strip("%"))
                            if progress_callback:
                                progress_callback(f"Downloading {video_id}...", percent)
                    except ValueError:
                        pass

        returncode = process.wait()
        if returncode != 0:
            stderr = process.stderr.read() if process.stderr else ""
            raise RuntimeError(f"yt-dlp failed with code {returncode}: {stderr}")
        
        if progress_callback:
            progress_callback("Download complete", 100.0)

        # 실제 다운로드된 파일 찾기
        video_path = target_dir / "video.mp4"
        if not video_path.exists():
             raise FileNotFoundError(f"Downloaded file not found at {video_path}")

        return Video(
            video_id=video_id,
            source_url=url,
            file_path=video_path,
            title=str(video_id) # yt-dlp JSON dump로 title 가져올 수 있으나 현재는 ID 사용
        )
