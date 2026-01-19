#!/usr/bin/env python3
"""Argos Translate 기반 자막 번역 스크립트

이 스크립트는 input_subs/의 SRT 파일을 읽어 ArgosTranslatorAdapter를 사용하여
로컬에서 번역한 후 translated_subs/에 저장합니다.

사용법:
    python scripts/translate_argos.py <video_id> [--source-lang SOURCE] [--target-lang TARGET]

예시:
    python scripts/translate_argos.py dQw4w9WgXcQ
    python scripts/translate_argos.py dQw4w9WgXcQ --source-lang en --target-lang ko
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 경로 상수
INPUT_SUBS_DIR = PROJECT_ROOT / "input_subs"
TRANSLATED_SUBS_DIR = PROJECT_ROOT / "translated_subs"

from src.domain.entities.subtitle import Subtitle
from src.domain.value_objects.video_id import VideoId
from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter


def progress_callback(message: str, percent: float) -> None:
    """진행 상황 출력 콜백"""
    print(f"[{percent:5.1f}%] {message}")


def translate_subtitle(
    video_id: str,
    source_lang: str = "en",
    target_lang: str = "ko",
) -> Path:
    """SRT 파일을 Argos Translate로 번역

    Args:
        video_id: 비디오 ID
        source_lang: 원본 언어 코드 (기본값: "en")
        target_lang: 목표 언어 코드 (기본값: "ko")

    Returns:
        번역된 자막 파일 경로

    Raises:
        FileNotFoundError: 입력 파일이 없을 경우
        ValueError: 번역 실패 시
    """
    input_path = INPUT_SUBS_DIR / f"{video_id}.srt"
    output_path = TRANSLATED_SUBS_DIR / f"{video_id}.srt"

    if not input_path.exists():
        raise FileNotFoundError(f"입력 자막을 찾을 수 없습니다: {input_path}")

    print(f"[번역 시작] {input_path.name}")
    print(f"[번역 엔진] Argos Translate (로컬)")
    print(f"[언어 방향] {source_lang} -> {target_lang}")

    # SRT 파일 읽기
    srt_content = input_path.read_text(encoding="utf-8")

    # Subtitle 도메인 객체 생성
    try:
        subtitle = Subtitle(
            video_id=VideoId(video_id),
            language=source_lang,
            format="srt",
            text=srt_content,
            source="file"
        )
        subtitle.validate()
    except Exception as e:
        raise ValueError(f"자막 객체 생성 실패: {e}")

    # ArgosTranslatorAdapter 생성 및 번역
    try:
        adapter = ArgosTranslatorAdapter()

        # 언어 쌍 지원 확인
        if not adapter.is_language_pair_supported(source_lang, target_lang):
            print(f"\n[오류] {source_lang} -> {target_lang} 번역이 지원되지 않습니다.")
            print("[안내] 언어 패키지를 설치해야 합니다.")
            print(f"[명령] python -m argostranslate.package install --from-code {source_lang} --to-code {target_lang}")
            raise ValueError(f"Unsupported language pair: {source_lang} -> {target_lang}")

        translated_subtitle = adapter.translate(
            subtitle,
            target_language=target_lang,
            progress_callback=progress_callback
        )

        # 번역된 자막 검증
        translated_subtitle.validate()

    except Exception as e:
        raise ValueError(f"번역 실패: {e}")

    # 번역된 자막 저장
    TRANSLATED_SUBS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_text(translated_subtitle.text, encoding="utf-8")

    print(f"\n[번역 완료] {output_path}")
    return output_path


def main() -> int:
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="Argos Translate 기반 자막 번역",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  %(prog)s dQw4w9WgXcQ
  %(prog)s dQw4w9WgXcQ --source-lang en --target-lang ko
  %(prog)s video123 --source-lang en --target-lang ja
        """
    )
    parser.add_argument(
        "video_id",
        help="번역할 비디오 ID"
    )
    parser.add_argument(
        "--source-lang",
        default="en",
        help="원본 언어 코드 (기본값: en)"
    )
    parser.add_argument(
        "--target-lang",
        default="ko",
        help="목표 언어 코드 (기본값: ko)"
    )

    args = parser.parse_args()

    try:
        translate_subtitle(
            video_id=args.video_id,
            source_lang=args.source_lang,
            target_lang=args.target_lang,
        )
        return 0
    except Exception as e:
        print(f"\n❌ 실패: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
