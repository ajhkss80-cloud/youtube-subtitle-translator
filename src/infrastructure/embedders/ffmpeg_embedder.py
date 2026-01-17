"""FfmpegEmbedder - ffmpeg 기반 자막 삽입 어댑터."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal, Optional

from src.application.ports.subtitle_embedder import ProgressCallback, SubtitleEmbedderPort
from src.domain.entities.subtitle import Subtitle
from src.domain.entities.video import Video


class FfmpegEmbedder(SubtitleEmbedderPort):
    """ffmpeg 기반 자막 삽입기."""

    _HARDSUB_STYLE = {
        "FontName": "Noto Sans CJK KR",
        "FontSize": "24",
        "PrimaryColour": "&HFFFFFF&",
        "OutlineColour": "&H000000&",
        "Outline": "2",
    }

    def embed(
        self,
        video: Video,
        subtitle: Subtitle,
        output_path: Path,
        mode: Literal["soft", "hard"] = "soft",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Path:
        if video.file_path is None:
            raise ValueError("video.file_path is required to embed subtitles")
        if subtitle.file_path is None:
            raise ValueError("subtitle.file_path is required to embed subtitles")
        if not video.file_path.exists():
            raise FileNotFoundError(f"Video file not found: {video.file_path}")
        if not subtitle.file_path.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle.file_path}")
        if mode not in ("soft", "hard"):
            raise ValueError("mode must be 'soft' or 'hard'")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if progress_callback:
            progress_callback(f"Embedding subtitles ({mode})", 0.0)

        if mode == "hard":
            escaped_sub_path = self._escape_ffmpeg_path(subtitle.file_path)
            force_style = self._build_force_style()
            # FFMPEG 명령어 (하드섭)
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video.file_path),
                "-vf", f"subtitles={escaped_sub_path}:force_style='{force_style}'",
                "-c:a", "copy",
                str(output_path),
            ]
        else:
            # FFMPEG 명령어 (소프트섭)
            language = subtitle.language.strip() if subtitle.language else "und"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video.file_path),
                "-i", str(subtitle.file_path),
                "-map", "0:v",
                "-map", "0:a",
                "-map", "1:0",
                "-c:v", "copy",
                "-c:a", "copy",
                "-c:s", "mov_text",
                "-metadata:s:s:0", f"language={language}",
                str(output_path),
            ]

        try:
            # check=False로 실행 후 returncode 확인 (상세 에러 처리를 위해)
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        except OSError as exc:
            raise RuntimeError("Failed to start ffmpeg") from exc
        
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise RuntimeError(f"ffmpeg failed: {stderr}")

        if progress_callback:
            progress_callback("Subtitle embedding complete", 100.0)

        return output_path

    @staticmethod
    def _escape_ffmpeg_path(path: Path) -> str:
        path_str = str(path)
        # Windows/Linux 경로 이스케이프 (ffmpeg 특수 문자)
        # ':' (드라이브), '\', quotes, brackets 등
        escape_chars = ["\\", ":", "'", ",", "[", "]"]
        for char in escape_chars:
            path_str = path_str.replace(char, f"\\{char}")
        return path_str

    @classmethod
    def _build_force_style(cls) -> str:
        return ",".join(f"{k}={v}" for k, v in cls._HARDSUB_STYLE.items())
