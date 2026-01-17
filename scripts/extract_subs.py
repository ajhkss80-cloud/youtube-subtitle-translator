#!/usr/bin/env python3
"""
(수정됨) 자막 추출 및 STT 생성 스크립트
다운로드된 영상에서 자막을 추출하거나, 없으면 Whisper(Python Lib)로 생성합니다.
Subprocess 호출 방식을 제거하고 Python 라이브러리를 직접 사용하여 환경 문제 해결.
"""

import sys
import shutil
import re
from pathlib import Path
import warnings

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
INPUT_SUBS_DIR = PROJECT_ROOT / "input_subs"

# 자막 선택 우선순위 (높은 순)
LANG_PRIORITY = ["ko", "en"]


def extract_lang_code(filename: str) -> str | None:
    """파일명에서 언어 코드 추출"""
    match = re.search(r'\.([a-z]{2})(?:\.auto)?\.(?:srt|vtt)$', filename.lower())
    if match:
        return match.group(1)
    return None


def find_subtitle_file(video_dir: Path) -> Path | None:
    """다운로드 폴더에서 자막 파일 찾기 (기존 로직 유지)"""
    srt_files = list(video_dir.glob("*.srt"))
    vtt_files = list(video_dir.glob("*.vtt"))
    all_subs = srt_files + vtt_files
    
    if not all_subs:
        return None
    
    def get_priority(sub_path: Path) -> tuple:
        filename = sub_path.name.lower()
        lang_code = extract_lang_code(filename)
        lang_score = 99
        if lang_code:
            for i, lang in enumerate(LANG_PRIORITY):
                if lang_code == lang:
                    lang_score = i
                    break
        auto_score = 1 if ".auto." in filename else 0
        format_score = 0 if sub_path.suffix == ".srt" else 1
        return (lang_score, auto_score, format_score)
    
    sorted_subs = sorted(all_subs, key=get_priority)
    selected = sorted_subs[0]
    print(f"[자막 선택] 발견된 자막 {len(all_subs)}개 중 '{selected.name}' 선택")
    return selected


def convert_to_srt(input_file: Path, output_file: Path) -> None:
    """VTT를 SRT로 변환 (ffmpeg 사용 - 단순 변환은 subprocess가 효율적)"""
    import subprocess
    cmd = ["ffmpeg", "-y", "-i", str(input_file), str(output_file)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"[오류] ffmpeg 변환 실패: {e.stderr}", file=sys.stderr)
        raise


def generate_with_whisper(video_path: Path, output_srt: Path) -> None:
    """
    Whisper Python Library를 사용하여 자막 생성
    공식 문서 권장 방식: import whisper -> load_model -> transcribe
    get_writer 대신 직접 SRT 저장 (호환성 보장)
    """
    print(f"[STT 생성] Whisper 라이브러리로 자막 생성 중... (모델: base)")
    
    try:
        import whisper
    except ImportError:
        print("[오류] openai-whisper 패키지가 설치되지 않았습니다.", file=sys.stderr)
        print("pip install openai-whisper 실행이 필요합니다.", file=sys.stderr)
        raise

    # 모델 로드 (첫 실행 시 자동 다운로드됨)
    warnings.filterwarnings("ignore")
    
    try:
        print("[Whisper] 모델 로딩 중... (첫 실행 시 다운로드가 필요할 수 있습니다)")
        model = whisper.load_model("base")
        
        # 트랜스크립션 실행
        print("[Whisper] 음성 인식 중...")
        result = model.transcribe(str(video_path), verbose=False)
        
        # 직접 SRT 포맷으로 저장 (get_writer 의존성 제거)
        # segments 방어 코드 (Codex 지적)
        segments = result.get("segments", [])
        if not segments:
            raise ValueError("Whisper가 음성을 인식하지 못했습니다. (무음 또는 인식 실패)")
        
        srt_content = []
        for i, segment in enumerate(segments, 1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()
            
            # 시간 포맷 변환 (초 -> SRT 타임코드)
            start_tc = format_timestamp(start)
            end_tc = format_timestamp(end)
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_tc} --> {end_tc}")
            srt_content.append(text)
            srt_content.append("")  # 빈 줄
        
        # 파일 저장
        output_srt.parent.mkdir(parents=True, exist_ok=True)
        output_srt.write_text("\n".join(srt_content), encoding="utf-8")
        print(f"[STT 완료] 자막 생성됨: {output_srt}")
        
    except Exception as e:
        print(f"[오류] Whisper 실행 중 예외 발생: {e}", file=sys.stderr)
        raise


def format_timestamp(seconds: float) -> str:
    """초를 SRT 타임코드로 변환 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def process_video(video_id: str) -> Path:
    video_dir = DOWNLOADS_DIR / video_id
    video_file = video_dir / "video.mp4"
    output_srt = INPUT_SUBS_DIR / f"{video_id}.srt"
    
    if not video_file.exists():
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_file}")
    
    INPUT_SUBS_DIR.mkdir(parents=True, exist_ok=True)
    
    existing_sub = find_subtitle_file(video_dir)
    
    if existing_sub:
        print(f"[자막 발견] {existing_sub.name}")
        if existing_sub.suffix == ".srt":
            shutil.copy(existing_sub, output_srt)
        else:
            convert_to_srt(existing_sub, output_srt)
        print(f"[복사 완료] {output_srt}")
    else:
        print(f"[자막 없음] STT로 자막을 생성합니다...")
        generate_with_whisper(video_file, output_srt)
    
    return output_srt


def main():
    if len(sys.argv) < 2:
        print("사용법: python extract_subs.py <video_id>")
        sys.exit(1)
    
    video_id = sys.argv[1]
    try:
        process_video(video_id)
    except Exception as e:
        print(f"❌ 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
