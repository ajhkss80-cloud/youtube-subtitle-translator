#!/usr/bin/env python3
"""
자막 삽입 및 최종 영상 생성 스크립트
ffmpeg을 사용하여 번역된 자막을 영상에 삽입합니다.
"""

import subprocess
import sys
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
TRANSLATED_SUBS_DIR = PROJECT_ROOT / "translated_subs"
FINAL_VIDEOS_DIR = PROJECT_ROOT / "final_videos"

# 하드섭 기본 스타일
HARDSUB_STYLE = {
    "FontName": "Noto Sans CJK KR",
    "FontSize": "24",
    "PrimaryColour": "&HFFFFFF&",
    "OutlineColour": "&H000000&",
    "Outline": "2",
}


def escape_ffmpeg_path(path: Path) -> str:
    """
    ffmpeg 필터용 경로 이스케이프
    특수문자(:, ', \, ,)를 이스케이프 처리합니다.
    """
    path_str = str(path)
    # ffmpeg filter 문법에서 이스케이프 필요한 문자들
    escape_chars = ["\\", ":", "'", ",", "[", "]"]
    for char in escape_chars:
        path_str = path_str.replace(char, f"\\{char}")
    return path_str


def build_force_style() -> str:
    """하드섭용 스타일 문자열 생성"""
    return ",".join(f"{k}={v}" for k, v in HARDSUB_STYLE.items())


def embed_subtitles(video_id: str, hard_sub: bool = False) -> Path:
    """
    번역된 자막을 영상에 삽입합니다.
    
    Args:
        video_id: 영상 ID
        hard_sub: True면 영상에 굽기(하드섭), False면 별도 트랙(소프트섭)
        
    Returns:
        생성된 최종 영상 경로
    """
    video_file = DOWNLOADS_DIR / video_id / "video.mp4"
    subtitle_file = TRANSLATED_SUBS_DIR / f"{video_id}.srt"
    output_file = FINAL_VIDEOS_DIR / f"{video_id}_translated.mp4"
    
    if not video_file.exists():
        raise FileNotFoundError(f"영상 파일을 찾을 수 없습니다: {video_file}")
    
    if not subtitle_file.exists():
        raise FileNotFoundError(f"번역 자막을 찾을 수 없습니다: {subtitle_file}")
    
    FINAL_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    if hard_sub:
        # 하드섭: 영상에 자막을 직접 굽기
        # 경로 이스케이프 처리
        escaped_sub_path = escape_ffmpeg_path(subtitle_file)
        force_style = build_force_style()
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-vf", f"subtitles={escaped_sub_path}:force_style='{force_style}'",
            "-c:a", "copy",
            str(output_file)
        ]
    else:
        # 소프트섭: 자막 트랙으로 추가
        # -map으로 명시적 스트림 선택 (원본의 다른 자막 제외)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-i", str(subtitle_file),
            "-map", "0:v",          # 첫 번째 입력의 비디오
            "-map", "0:a",          # 첫 번째 입력의 오디오
            "-map", "1:0",          # 두 번째 입력(자막 파일)
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", "mov_text",
            "-metadata:s:s:0", "language=kor",
            str(output_file)
        ]
    
    print(f"[자막 삽입] {'하드섭' if hard_sub else '소프트섭'} 모드")
    print(f"[입력] {video_file}")
    print(f"[자막] {subtitle_file}")
    print(f"[출력] {output_file}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[오류] ffmpeg 실행 실패:", file=sys.stderr)
        print(f"  명령어: {' '.join(cmd)}", file=sys.stderr)
        print(f"  stderr: {e.stderr}", file=sys.stderr)
        raise
    
    print(f"[완료] {output_file}")
    return output_file


def main():
    hard_sub = "--hard" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    
    if len(args) < 1:
        print("사용법: python embed_subs.py <video_id> [--hard]")
        print("  --hard: 자막을 영상에 굽기 (하드섭)")
        print("  기본값: 소프트섭 (별도 자막 트랙)")
        print("\n예시: python embed_subs.py dQw4w9WgXcQ --hard")
        print("\ntranslated_subs/ 폴더의 자막 목록:")
        
        if TRANSLATED_SUBS_DIR.exists():
            for f in TRANSLATED_SUBS_DIR.glob("*.srt"):
                print(f"  - {f.stem}")
        sys.exit(1)
    
    video_ids = args
    
    for video_id in video_ids:
        try:
            output_path = embed_subtitles(video_id, hard_sub=hard_sub)
            print(f"✅ 완료: {output_path}")
        except Exception as e:
            print(f"❌ 실패: {video_id} - {e}")


if __name__ == "__main__":
    main()
