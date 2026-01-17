#!/usr/bin/env python3
"""
YouTube 영상 다운로드 스크립트 (개선된 버전)
영상과 자막 다운로드를 분리하여, 자막 실패(429 등) 시에도 영상은 확보하도록 변경.
재시도 및 지연 옵션 추가로 차단 회피.
"""

import subprocess
import sys
import re
from pathlib import Path

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"


def get_video_id(url: str) -> str | None:
    """YouTube URL에서 video_id 추출"""
    import hashlib
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # ID 추출 실패 시 해시 사용 (fallback)
    return hashlib.md5(url.encode()).hexdigest()[:11]


def download_video(url: str) -> Path:
    """
    YouTube 영상과 자막을 다운로드합니다 (분리 실행).
    1. 영상 다운로드 (필수, 실패 시 에러)
    2. 자막 다운로드 (선택, 실패 시 경고만 출력하고 진행)
    """
    video_id = get_video_id(url)
    output_dir = DOWNLOADS_DIR / video_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_template = str(output_dir / "video.%(ext)s")
    
    # 공통 옵션 (재시도 및 차단 회피)
    COMMON_OPTS = [
        "--retries", "10",
        "--fragment-retries", "10",
        "--retry-sleep", "5",         # 재시도 대기 시간 5초
        "--sleep-interval", "2",      # 요청 간 최소 2초 대기
        "--max-sleep-interval", "5",  # 최대 5초 대기
        "--no-check-certificates",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ]

    # 1. 영상 다운로드 명령
    video_cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        url
    ] + COMMON_OPTS
    
    print(f"[다운로드 시작] {video_id} (영상)")
    print(f"[출력 경로] {output_dir}")
    
    try:
        # 영상은 필수항목이므로 check=True
        subprocess.run(video_cmd, check=True, capture_output=True, text=True)
        print("✅ 영상 다운로드 완료")
    except subprocess.CalledProcessError as e:
        print(f"[오류] 영상 다운로드 실패:", file=sys.stderr)
        print(f"  stderr: {e.stderr}", file=sys.stderr)
        raise

    # 2. 자막 다운로드 명령
    sub_cmd = [
        "yt-dlp",
        "--skip-download",        # 영상 다운로드 생략
        "--write-subs",           # 자막 다운로드
        "--write-auto-subs",      # 자동 생성 자막도 포함
        "--sub-langs", "en,ko",   # 영어, 한국어 자막
        "--convert-subs", "srt",  # SRT 형식으로 변환
        "-o", output_template,
        url
    ] + COMMON_OPTS
    
    print(f"[다운로드 시도] {video_id} (자막)")
    
    try:
        # 자막은 실패해도 진행하므로 check=False
        result = subprocess.run(sub_cmd, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[주의] 자막 다운로드 실패 (무시하고 진행): {result.stderr.splitlines()[-1]}")
            # 전체 로그가 아닌 마지막 한 줄만 출력하여 혼란 방지
        else:
            print("✅ 자막 다운로드 완료")
            
    except Exception as e:
        print(f"[주의] 자막 다운로드 중 예외 발생 (무시하고 진행): {e}")
    
    return output_dir


def main():
    if len(sys.argv) < 2:
        print("사용법: python download.py <YouTube_URL> [URL2] [URL3] ...")
        sys.exit(1)
    
    urls = sys.argv[1:]
    
    for url in urls:
        try:
            output_path = download_video(url)
            print(f"🎉 전체 작업 완료: {output_path}")
        except Exception as e:
            print(f"❌ 실패: {url} - {e}")
            sys.exit(1) # 영상 다운 실패 시 1 리턴


if __name__ == "__main__":
    main()
