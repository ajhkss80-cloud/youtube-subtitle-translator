#!/usr/bin/env python3
"""
자막 삽입 스크립트 (Clean Architecture 적용)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Tuple

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.application.use_cases.embed_subtitles import EmbedSubtitlesUseCase
from src.domain.entities.subtitle import Subtitle
from src.domain.entities.video import Video
from src.domain.value_objects.video_id import VideoId
from src.infrastructure.embedders.ffmpeg_embedder import FfmpegEmbedder

DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
TRANSLATED_SUBS_DIR = PROJECT_ROOT / "translated_subs"
FINAL_VIDEOS_DIR = PROJECT_ROOT / "final_videos"


def _progress_callback(message: str, percent: float) -> None:
    print(f"[자막삽입] {message} ({percent:.1f}%)")


def _resolve_target(video_id_str: str) -> Tuple[Video, Subtitle, Path]:
    try:
        vid = VideoId(video_id_str)
    except ValueError as exc:
         raise ValueError(f"유효하지 않은 Video ID: {video_id_str}") from exc
    
    # 1. 영상 파일 찾기
    video_path = DOWNLOADS_DIR / str(vid) / "video.mp4"
    if not video_path.exists():
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_path}")
    
    video = Video(
        video_id=vid,
        source_url=f"https://youtu.be/{vid}",
        file_path=video_path
    )

    # 2. 번역된 자막 파일 찾기
    sub_path = TRANSLATED_SUBS_DIR / f"{vid}.srt"
    if not sub_path.exists():
        raise FileNotFoundError(f"번역된 자막 파일을 찾을 수 없습니다: {sub_path}")
    
    subtitle = Subtitle(
        video_id=vid,
        language="ko", # 가정
        format="srt",
        file_path=sub_path,
        source="manual"
    )

    # 3. 출력 경로
    output_path = FINAL_VIDEOS_DIR / f"{vid}_translated.mp4"

    return video, subtitle, output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="영상에 자막 삽입 (FFmpeg)")
    parser.add_argument("--video_id", required=True, help="Video ID")
    parser.add_argument("--hard", action="store_true", help="하드코딩 자막 (Burn-in)")
    args = parser.parse_args()

    try:
        video, subtitle, output_path = _resolve_target(args.video_id)
        
        mode = "hard" if args.hard else "soft"
        
        embedder = FfmpegEmbedder()
        use_case = EmbedSubtitlesUseCase(subtitle_embedder=embedder)

        print(f"🎬 자막 삽입 시작 ({mode}): {video.video_id}")
        result_video = use_case.execute(
            video=video,
            subtitle=subtitle,
            output_path=output_path,
            mode=mode,
            progress_callback=_progress_callback
        )
        print(f"✅ 완료: {result_video.file_path}")

    except Exception as exc:
        print(f"❌ 실패: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
