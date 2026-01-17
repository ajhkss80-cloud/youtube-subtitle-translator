#!/usr/bin/env python3
"""
자막 추출 및 STT 생성 스크립트 (Clean Architecture 적용 + 호환성 Fix)

- Dual Fix: --video_id 옵션 및 위치 인자(ID 형식) 모두 지원
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.application.use_cases.extract_subtitles import ExtractSubtitlesUseCase
from src.domain.entities.video import Video
from src.domain.value_objects.video_id import VideoId
from src.infrastructure.extractors.whisper_extractor import WhisperExtractor

DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
INPUT_SUBS_DIR = PROJECT_ROOT / "input_subs"


def _progress_callback(message: str, percent: float) -> None:
    print(f"[자막추출] {message} ({percent:.1f}%)")


def _resolve_video_from_id(video_id_str: str) -> Tuple[Video, Path]:
    try:
        vid = VideoId(video_id_str)
    except ValueError as exc:
        raise ValueError(f"유효하지 않은 Video ID: {video_id_str}") from exc

    # 가정: downloads/{video_id}/video.mp4
    video_path = DOWNLOADS_DIR / str(vid) / "video.mp4"
    if not video_path.exists():
        # 폴더 구조가 다를 수 있으니 downloads/video_id.mp4 도 체크해보거나 에러
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_path}")

    video = Video(
        video_id=vid,
        source_url=f"https://youtu.be/{vid}",
        file_path=video_path,
    )
    output_srt = INPUT_SUBS_DIR / f"{vid}.srt"
    return video, output_srt


def _resolve_video_from_path(path: Path) -> Tuple[Video, Path]:
    if path.is_dir():
        video_file = path / "video.mp4"
        inferred_id = path.name
    else:
        video_file = path
        # parent dir name or file stem
        inferred_id = path.parent.name if path.name == "video.mp4" else path.stem

    if not video_file.exists():
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_file}")

    try:
        video_id = VideoId(inferred_id)
    except ValueError:
        # ID 추론 실패 시 임시 ID (md5 등) 사용 가능하나, 여기서는 엄격하게 처리하거나
        # 혹은 Clean Arch 원칙상 ID가 필요하므로 에러.
        # 기존 로직과 호환 위해 에러 발생 시킴.
        raise ValueError(f"경로에서 VideoID를 추론할 수 없습니다: {path}")

    video = Video(
        video_id=video_id,
        source_url="local",
        file_path=video_file,
    )
    output_srt = INPUT_SUBS_DIR / f"{video_id}.srt"
    return video, output_srt


def main() -> None:
    parser = argparse.ArgumentParser(description="자막 추출 (Whisper)")
    parser.add_argument("--video_id", help="영상 ID (downloads 폴더 내 검색)")
    parser.add_argument("--language", default="ko", help="자막 언어 (기본: ko)")
    parser.add_argument("--model", default="base", help="Whisper 모델 크기")
    parser.add_argument("paths", nargs="*", help="영상 파일/폴더 경로 또는 VideoID")
    args = parser.parse_args()

    targets: List[Tuple[Video, Path]] = []

    # 1. --video_id 명시적 사용
    if args.video_id:
        targets.append(_resolve_video_from_id(args.video_id))

    # 2. 위치 인자 처리 (Dual Fix)
    if args.paths:
        for raw in args.paths:
            path = Path(raw)
            # A) 실제 존재하는 경로인가?
            if path.exists():
                targets.append(_resolve_video_from_path(path))
            # B) 11자리 VideoID 형식인가? (경로는 없지만 ID로 간주)
            elif re.match(r"^[a-zA-Z0-9_-]{11}$", raw):
                targets.append(_resolve_video_from_id(raw))
            else:
                print(f"❌ 유효하지 않은 경로 또는 ID: {raw}")
                sys.exit(1)

    if not targets:
        parser.print_help()
        sys.exit(1)

    # 3. UseCase 실행
    extractor = WhisperExtractor(model_name=args.model)
    use_case = ExtractSubtitlesUseCase(subtitle_extractor=extractor)

    for video, output_path in targets:
        try:
            print(f"🎬 처리 중: {video.video_id} ({video.file_path})")
            result = use_case.execute(
                video=video,
                output_path=output_path,
                language=args.language,
                progress_callback=_progress_callback
            )
            print(f"✅ 완료: {result.file_path}")
        except Exception as exc:
            print(f"❌ 실패: {video.video_id} - {exc}")
            # sys.exit(1) # 하나 실패해도 나머지는 진행? 아니면 중단? 기존엔 중단.
            sys.exit(1)


if __name__ == "__main__":
    main()
