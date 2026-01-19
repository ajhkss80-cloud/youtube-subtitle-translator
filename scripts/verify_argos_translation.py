#!/usr/bin/env python3
"""Argos Translation Adapter 검증 스크립트

이 스크립트는 다음을 수행합니다:
1. Argos Translate 설치 확인
2. en -> ko 번역 패키지 자동 설치 (없을 경우)
3. ArgosTranslatorAdapter 인스턴스화
4. 샘플 SRT 자막 번역 테스트
5. 번역 결과 출력 및 검증 성공 메시지 표시
"""
from __future__ import annotations

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import argostranslate.package
    import argostranslate.translate
except ImportError:
    print("ERROR: argostranslate is not installed.")
    print("Install it with: pip install argostranslate")
    sys.exit(1)

from src.domain.entities.subtitle import Subtitle
from src.domain.value_objects.video_id import VideoId
from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter


def install_language_package(from_code: str, to_code: str) -> bool:
    """언어 패키지 설치

    Args:
        from_code: 원본 언어 코드 (예: 'en')
        to_code: 목표 언어 코드 (예: 'ko')

    Returns:
        설치 성공 여부
    """
    print(f"\n[1/5] Checking language package: {from_code} -> {to_code}")

    # 패키지 인덱스 업데이트
    print("   Updating package index...")
    argostranslate.package.update_package_index()

    # 이미 설치되어 있는지 확인
    installed_languages = argostranslate.translate.get_installed_languages()

    # from_code와 to_code가 모두 설치되어 있고, 번역이 가능한지 확인
    translator_found = False
    source_lang_obj = None
    target_lang_obj = None

    for lang in installed_languages:
        if lang.code == from_code:
            source_lang_obj = lang
        if lang.code == to_code:
            target_lang_obj = lang

    if source_lang_obj is not None and target_lang_obj is not None:
        translator = source_lang_obj.get_translation(target_lang_obj)
        if translator is not None:
            translator_found = True

    if translator_found:
        print(f"   ✓ Package already installed: {from_code} -> {to_code}")
        return True

    # 설치되지 않았다면 설치
    print(f"   Package not found. Installing {from_code} -> {to_code}...")

    available_packages = argostranslate.package.get_available_packages()
    package_to_install = None

    for pkg in available_packages:
        if pkg.from_code == from_code and pkg.to_code == to_code:
            package_to_install = pkg
            break

    if package_to_install is None:
        print(f"   ✗ Package {from_code} -> {to_code} not available")
        return False

    print(f"   Downloading and installing package...")
    argostranslate.package.install_from_path(package_to_install.download())
    print(f"   ✓ Package installed successfully: {from_code} -> {to_code}")
    return True


def create_sample_srt() -> str:
    """샘플 SRT 자막 생성"""
    return """1
00:00:00,000 --> 00:00:02,500
Hello, welcome to this video.

2
00:00:02,500 --> 00:00:05,000
Today we will learn about Clean Architecture.

3
00:00:05,000 --> 00:00:08,000
It separates concerns into layers.

4
00:00:08,000 --> 00:00:11,000
This makes code more maintainable and testable.
"""


def progress_callback(message: str, percent: float) -> None:
    """진행 상황 출력 콜백"""
    print(f"   [{percent:5.1f}%] {message}")


def main() -> int:
    """메인 실행 함수"""
    print("=" * 60)
    print("Argos Translation Adapter Verification")
    print("=" * 60)

    # 1. 언어 패키지 설치 확인 및 자동 설치
    if not install_language_package("en", "ko"):
        print("\n✗ VERIFICATION FAILED: Could not install language package")
        return 1

    # 2. ArgosTranslatorAdapter 인스턴스 생성
    print("\n[2/5] Instantiating ArgosTranslatorAdapter...")
    try:
        adapter = ArgosTranslatorAdapter()
        print("   ✓ Adapter created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create adapter: {e}")
        return 1

    # 3. 지원 언어 목록 확인
    print("\n[3/5] Checking supported languages...")
    try:
        supported_languages = adapter.list_supported_languages()
        print(f"   ✓ Supported languages: {', '.join(supported_languages)}")

        if not adapter.is_language_pair_supported("en", "ko"):
            print("   ✗ en -> ko translation not supported")
            return 1
        print("   ✓ en -> ko translation is supported")
    except Exception as e:
        print(f"   ✗ Failed to check languages: {e}")
        return 1

    # 4. 샘플 SRT 자막 생성 및 번역
    print("\n[4/5] Translating sample SRT subtitle...")
    sample_srt = create_sample_srt()

    print("\n   Original SRT:")
    print("   " + "-" * 56)
    for line in sample_srt.strip().split("\n"):
        print(f"   {line}")
    print("   " + "-" * 56)

    # Subtitle 도메인 객체 생성
    try:
        subtitle = Subtitle(
            video_id=VideoId("dQw4w9WgXcQ"),  # 샘플 비디오 ID
            language="en",
            format="srt",
            text=sample_srt,
            source="manual"
        )
        subtitle.validate()
    except Exception as e:
        print(f"   ✗ Failed to create Subtitle object: {e}")
        return 1

    # 번역 실행
    try:
        print("\n   Translation in progress:")
        translated_subtitle = adapter.translate(
            subtitle,
            target_language="ko",
            progress_callback=progress_callback
        )
    except Exception as e:
        print(f"   ✗ Translation failed: {e}")
        return 1

    # 5. 번역 결과 출력
    print("\n[5/5] Translation completed successfully!")
    print("\n   Translated SRT:")
    print("   " + "-" * 56)
    for line in translated_subtitle.text.strip().split("\n"):
        print(f"   {line}")
    print("   " + "-" * 56)

    # 번역된 자막 검증
    try:
        translated_subtitle.validate()
        print("\n   ✓ Translated subtitle validation passed")
        print(f"   ✓ Source language: {translated_subtitle.source_language}")
        print(f"   ✓ Target language: {translated_subtitle.language}")
        print(f"   ✓ Is translated: {translated_subtitle.is_translated}")
    except Exception as e:
        print(f"   ✗ Validation failed: {e}")
        return 1

    # 최종 성공 메시지
    print("\n" + "=" * 60)
    print("✓ VERIFICATION SUCCESSFUL")
    print("=" * 60)
    print("\nArgosTranslatorAdapter is working correctly!")
    print("- Language package (en -> ko) is installed")
    print("- Adapter instantiation works")
    print("- Translation functionality is operational")
    print("- SRT format parsing and reassembly works")
    print("- Domain objects (Subtitle, VideoId) integration works")

    return 0


if __name__ == "__main__":
    sys.exit(main())
