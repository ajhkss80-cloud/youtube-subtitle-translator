"""ArgosTranslatorAdapter - Argos Translate 기반 자막 번역 어댑터."""
from __future__ import annotations

import re
from typing import List, Optional

try:
    import argostranslate.package
    import argostranslate.translate
except ImportError:
    raise ImportError(
        "argostranslate is not installed. "
        "Install it with: pip install argostranslate"
    )

from src.application.ports.subtitle_translator import (
    ProgressCallback,
    SubtitleTranslatorPort,
)
from src.domain.entities.subtitle import Subtitle


class ArgosTranslatorAdapter(SubtitleTranslatorPort):
    """Argos Translate 로컬 번역엔진 어댑터"""

    def __init__(self) -> None:
        """Argos Translate 초기화"""
        # 설치된 패키지 업데이트 (초기화 시 한 번만)
        try:
            argostranslate.package.update_package_index()
        except Exception as e:
            # 패키지 인덱스 업데이트 실패 시 경고만 출력하고 계속 진행
            print(f"Warning: Failed to update package index: {e}")

    def translate(
        self,
        subtitle: Subtitle,
        target_language: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Subtitle:
        """자막을 대상 언어로 번역

        SRT 형식 파싱:
        1. SRT 큐 단위로 분리 (번호, 타임스탬프, 텍스트)
        2. 텍스트만 추출하여 번역
        3. 번역된 텍스트로 SRT 재조립

        Args:
            subtitle: 원본 자막 객체
            target_language: 목표 언어 코드
            progress_callback: 진행 상황 콜백

        Returns:
            번역된 Subtitle 객체

        Raises:
            ValueError: 지원하지 않는 언어 쌍
            RuntimeError: 번역 엔진 오류
        """
        if progress_callback:
            progress_callback("번역 준비 중...", 0.0)

        # 자막 텍스트 확인
        if subtitle.text is None:
            if subtitle.file_path is None:
                raise ValueError("Subtitle must have either text or file_path")
            # 파일에서 텍스트 읽기
            subtitle_text = subtitle.file_path.read_text(encoding="utf-8")
        else:
            subtitle_text = subtitle.text

        # subtitle_text가 비어있거나 공백만 있는지 검증
        if not subtitle_text or not subtitle_text.strip():
            raise ValueError("Subtitle text cannot be empty or whitespace only")

        # 언어 쌍 지원 확인
        source_lang = subtitle.language
        if not self.is_language_pair_supported(source_lang, target_language):
            raise ValueError(
                f"Translation from {source_lang} to {target_language} is not supported. "
                f"You may need to install the language package."
            )

        if progress_callback:
            progress_callback("번역 모델 로딩 중...", 10.0)

        # Argos 번역 객체 가져오기
        installed_languages = argostranslate.translate.get_installed_languages()
        source_lang_obj = None
        target_lang_obj = None

        for lang in installed_languages:
            if lang.code == source_lang:
                source_lang_obj = lang
            if lang.code == target_language:
                target_lang_obj = lang

        if source_lang_obj is None:
            raise RuntimeError(
                f"Source language {source_lang} is not installed"
            )

        if target_lang_obj is None:
            raise RuntimeError(
                f"Target language {target_language} is not installed"
            )

        translator = source_lang_obj.get_translation(target_lang_obj)
        if translator is None:
            raise RuntimeError(
                f"Failed to get translator for {source_lang} -> {target_language}"
            )

        if progress_callback:
            progress_callback("자막 파싱 중...", 20.0)

        # SRT 큐 파싱
        cues = self._parse_srt_cues(subtitle_text)

        # 파싱된 큐가 비어있는지 검증
        if not cues:
            raise ValueError("No valid subtitle cues found after parsing")

        if progress_callback:
            progress_callback(f"번역 중... ({len(cues)}개 큐)", 30.0)

        # 각 큐의 텍스트 번역
        translated_cues = []
        for i, cue in enumerate(cues):
            translated_text = translator.translate(cue["text"])
            translated_cues.append({
                "number": cue["number"],
                "timestamp": cue["timestamp"],
                "text": translated_text,
            })

            # 진행 상황 업데이트 (30% ~ 90%)
            if progress_callback and i % 10 == 0:
                percent = 30.0 + (60.0 * (i + 1) / len(cues))
                progress_callback(f"번역 중... ({i + 1}/{len(cues)})", percent)

        if progress_callback:
            progress_callback("번역 완료, 재조립 중...", 90.0)

        # SRT 재조립
        translated_srt = self._reassemble_srt(translated_cues)

        if progress_callback:
            progress_callback("번역 완료!", 100.0)

        # 번역된 Subtitle 객체 반환
        return subtitle.with_translation(translated_srt, target_language)

    def list_supported_languages(self) -> List[str]:
        """설치된 언어 패키지 목록 반환

        Returns:
            언어 코드 리스트
        """
        installed_languages = argostranslate.translate.get_installed_languages()
        return sorted([lang.code for lang in installed_languages])

    def is_language_pair_supported(
        self, source_language: str, target_language: str
    ) -> bool:
        """언어 쌍 지원 여부 확인

        Args:
            source_language: 원본 언어 코드
            target_language: 목표 언어 코드

        Returns:
            지원 여부
        """
        installed_languages = argostranslate.translate.get_installed_languages()
        source_lang_obj = None
        target_lang_obj = None

        for lang in installed_languages:
            if lang.code == source_language:
                source_lang_obj = lang
            if lang.code == target_language:
                target_lang_obj = lang

        if source_lang_obj is None or target_lang_obj is None:
            return False

        translator = source_lang_obj.get_translation(target_lang_obj)
        return translator is not None

    def _parse_srt_cues(self, srt_text: str) -> List[dict]:
        """SRT 텍스트를 큐 단위로 파싱

        SRT 형식:
        1
        00:00:00,000 --> 00:00:02,000
        First subtitle text

        2
        00:00:02,500 --> 00:00:05,000
        Second subtitle text

        Args:
            srt_text: SRT 형식 텍스트

        Returns:
            큐 리스트 [{"number": str, "timestamp": str, "text": str}, ...]
        """
        cues = []
        # SRT 큐는 빈 줄로 구분됨
        blocks = re.split(r"\n\n+", srt_text.strip())

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue  # 유효하지 않은 큐 건너뛰기

            number = lines[0].strip()
            timestamp = lines[1].strip()
            text = "\n".join(lines[2:]).strip()

            cues.append({
                "number": number,
                "timestamp": timestamp,
                "text": text,
            })

        return cues

    def _reassemble_srt(self, cues: List[dict]) -> str:
        """큐 리스트를 SRT 형식으로 재조립

        Args:
            cues: 큐 리스트

        Returns:
            SRT 형식 텍스트
        """
        srt_blocks = []
        for cue in cues:
            block = f"{cue['number']}\n{cue['timestamp']}\n{cue['text']}"
            srt_blocks.append(block)

        return "\n\n".join(srt_blocks) + "\n"
