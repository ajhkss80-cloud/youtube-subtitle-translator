#!/usr/bin/env python3
"""
영상 다운로드 스크립트 (Clean Architecture 적용)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.application.ports.video_downloader import ProgressCallback 
from src.application.use_cases.download_video import DownloadVideoUseCase
from src.infrastructure.downloaders.ytdlp_downloader import YtDlpDownloader


def _progress_callback(message: str, percent: float) -> None:
    """CLI 진행률 콜백"""
    print(f"[다운로드] {message} ({percent:.1f}%)")


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube 영상 다운로드")
    parser.add_argument("urls", nargs="+", help="YouTube URL 목록")
    parser.add_argument("--output_dir", "-o", default="downloads", help="다운로드 폴더")
    args = parser.parse_args()

    # 1. 의존성 주입 (Dependency Injection)
    downloader = YtDlpDownloader(yt_dlp_path="yt-dlp")
    use_case = DownloadVideoUseCase(video_downloader=downloader)

    output_dir = PROJECT_ROOT / args.output_dir

    for url in args.urls:
        try:
            video = use_case.execute(
                url=url, 
                output_dir=output_dir, 
                progress_callback=_progress_callback
            )
            print(f"✅ 다운로드 완료: {video.title} -> {video.file_path}")
        except Exception as exc:
            print(f"❌ 다운로드 실패: {url} - {exc}")
            sys.exit(1)


if __name__ == "__main__":
    main()
