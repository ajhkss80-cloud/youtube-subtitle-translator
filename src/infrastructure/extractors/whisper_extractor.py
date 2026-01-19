"""WhisperExtractor - Whisper 기반 자막 추출 어댑터."""
from __future__ import annotations

import re
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import List, Optional

from src.application.ports.subtitle_extractor import ProgressCallback, SubtitleExtractorPort
from src.domain.entities.subtitle import Subtitle
from src.domain.entities.video import Video


class WhisperExtractor(SubtitleExtractorPort):
    """Whisper 라이브러리 기반 자막 추출기."""

    _LANG_PRIORITY = ("ko", "en")

    def __init__(self, model_name: str = "base") -> None:
        self._model_name = model_name
        self._model = None

    def extract(
        self,
        video: Video,
        output_path: Path,
        language: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> Subtitle:
        if video.file_path is None:
            raise ValueError("video.file_path is required to extract subtitles")
        
        # 1. 기존 자막 파일 확인 (우선순위에 따라)
        existing_sub = self._find_subtitle_file(video.file_path.parent, language)
        if existing_sub:
            if progress_callback:
                progress_callback(f"Found existing subtitle: {existing_sub.name}", 100.0)
            
            self._copy_or_convert(existing_sub, output_path)
            
            return Subtitle(
                video_id=video.video_id,
                language=language,
                format="srt",
                file_path=output_path,
                source="manual" # 기존 파일은 manual로 간주
            )

        # 2. Whisper 실행
        if progress_callback:
            progress_callback(f"Generating subtitles with Whisper ({self._model_name})...", 0.0)
        
        self._generate_with_whisper(video.file_path, output_path, language, progress_callback)
        
        return Subtitle(
            video_id=video.video_id,
            language=language,
            format="srt",
            file_path=output_path,
            source="whisper"
        )

    def list_available_languages(self, video: Video) -> List[str]:
        if not video.file_path:
            return []
        
        video_dir = video.file_path.parent
        subtitles = list(video_dir.glob("*.srt")) + list(video_dir.glob("*.vtt"))
        languages = {
            lang for lang in (self._extract_lang_code(p.name) for p in subtitles) if lang
        }
        return sorted(list(languages))

    @staticmethod
    def _extract_lang_code(filename: str) -> Optional[str]:
        match = re.search(r"\.([a-z]{2})(?:\.auto)?\.(?:srt|vtt)$", filename.lower())
        if match:
            return match.group(1)
        return None

    def _find_subtitle_file(self, video_dir: Path, preferred_language: Optional[str]) -> Optional[Path]:
        srt_files = list(video_dir.glob("*.srt"))
        vtt_files = list(video_dir.glob("*.vtt"))
        all_subs = srt_files + vtt_files
        if not all_subs:
            return None

        # If no preferred language, use default priority order
        if preferred_language:
            priority_langs = [preferred_language] + [
                lang for lang in self._LANG_PRIORITY if lang != preferred_language
            ]
        else:
            priority_langs = list(self._LANG_PRIORITY)

        def get_priority(sub_path: Path) -> tuple:
            filename = sub_path.name.lower()
            lang_code = self._extract_lang_code(filename)
            lang_score = 99
            if lang_code:
                for i, lang in enumerate(priority_langs):
                    if lang_code == lang:
                        lang_score = i
                        break
            auto_score = 1 if ".auto." in filename else 0
            format_score = 0 if sub_path.suffix.lower() == ".srt" else 1
            return (lang_score, auto_score, format_score)

        return sorted(all_subs, key=get_priority)[0]

    @staticmethod
    def _copy_or_convert(input_file: Path, output_file: Path) -> None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if input_file.suffix.lower() == ".srt":
            shutil.copy(input_file, output_file)
            return
        WhisperExtractor._convert_to_srt(input_file, output_file)

    @staticmethod
    def _convert_to_srt(input_file: Path, output_file: Path) -> None:
        cmd = ["ffmpeg", "-y", "-i", str(input_file), str(output_file)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RuntimeError("ffmpeg subtitle conversion failed") from exc

    def _generate_with_whisper(
        self,
        video_path: Path,
        output_srt: Path,
        language: Optional[str],
        progress_callback: Optional[ProgressCallback],
    ) -> None:
        try:
            import whisper
        except ImportError as exc:
            raise ImportError(
                "openai-whisper package is required. Install via: pip install openai-whisper"
            ) from exc

        warnings.filterwarnings("ignore")
        if progress_callback:
            progress_callback("Loading Whisper model", 20.0)

        if self._model is None:
            try:
                self._model = whisper.load_model(self._model_name)
            except Exception as exc:
                raise RuntimeError("Failed to load Whisper model") from exc

        if progress_callback:
            progress_callback("Transcribing audio", 60.0)
        
        # 언어 설정 (auto일 경우 None으로 전달하여 whisper가 감지하게 함)
        transcribe_args = {"verbose": False}
        if language and language.lower() != "auto":
            transcribe_args["language"] = language

        try:
            result = self._model.transcribe(str(video_path), **transcribe_args)
        except Exception as exc:
            raise RuntimeError("Whisper transcription failed") from exc

        segments = result.get("segments", [])
        if not segments:
            # throw error or generate empty file? Throwing error is safer.
            raise ValueError("Whisper did not return any segments")

        output_srt.parent.mkdir(parents=True, exist_ok=True)
        srt_content = []
        for i, segment in enumerate(segments, 1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            start_tc = self._format_timestamp(start)
            end_tc = self._format_timestamp(end)
            srt_content.append(f"{i}")
            srt_content.append(f"{start_tc} --> {end_tc}")
            srt_content.append(text)
            srt_content.append("")

        output_srt.write_text("\n".join(srt_content), encoding="utf-8")
        
        if progress_callback:
            progress_callback("Subtitle ready", 100.0)

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
