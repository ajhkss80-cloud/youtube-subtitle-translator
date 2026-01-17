#!/bin/bash
# YouTube 번역기 GUI 실행 스크립트

# 프로젝트 디렉토리로 이동
cd /home/thepy/Desktop/Test

# API 키 환경변수 로드
if [ -f "set_env.sh" ]; then
    source set_env.sh
fi

# 가상환경 활성화
source venv/bin/activate

# GUI 앱 실행
python scripts/gui_app.py
