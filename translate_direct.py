#!/usr/bin/env python3
"""
직접 번역 스크립트 - Gemini API를 사용하여 SRT 파일을 한국어로 번역
"""

import os
from pathlib import Path

# 입력/출력 파일 경로
input_file = Path("/home/thepy/Desktop/Test/input_subs/IkDWmY3Hx4M.srt")
output_file = Path("/home/thepy/Desktop/Test/translated_subs/IkDWmY3Hx4M.srt")
rules_file = Path("/home/thepy/Desktop/Test/rules.md")

# 파일 읽기
print(f"📖 원본 자막 읽는 중: {input_file}")
srt_content = input_file.read_text(encoding="utf-8")

print(f"📖 번역 규칙 읽는 중: {rules_file}")
rules_content = rules_file.read_text(encoding="utf-8")

# Gemini API 설정
try:
    import google.generativeai as genai
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("💡 API 키를 설정하려면: export GEMINI_API_KEY='your-api-key'")
        exit(1)
    
    genai.configure(api_key=api_key)
    
    # 모델 선택
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("🤖 Gemini API로 번역 중...")
    
    # 번역 프롬프트
    prompt = f"""당신은 전문 영상 번역가입니다. 아래 제공된 원본 SRT 자막을 한국어로 번역하세요.

[번역 규칙]
{rules_content}

[추가 지침]
1. 출력은 오직 번역된 SRT 내용만 포함해야 합니다. (마크다운 코드블록 등 제외)
2. 타임코드와 자막 번호는 원본 그대로 유지하세요.
3. 문체는 '해요체'를 기본으로 하되, 상황에 따라 자연스럽게 처리하세요.
4. 자연스러운 한국어 구어체로 번역하세요.

[원본 SRT]
{srt_content}
"""
    
    # API 호출
    response = model.generate_content(prompt)
    
    # 응답 확인
    if not response.candidates:
        print("❌ Gemini API가 빈 응답을 반환했습니다.")
        exit(1)
    
    translated_text = response.text
    
    # 마크다운 코드블록 제거
    translated_text = translated_text.replace("```srt", "").replace("```", "").strip()
    
    # 출력 디렉토리 생성
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 번역 결과 저장
    output_file.write_text(translated_text, encoding="utf-8")
    
    print(f"✅ 번역 완료!")
    print(f"📁 저장 위치: {output_file}")
    print(f"📊 원본 라인 수: {len(srt_content.splitlines())}")
    print(f"📊 번역 라인 수: {len(translated_text.splitlines())}")
    
except ImportError:
    print("❌ google.generativeai 패키지가 설치되지 않았습니다.")
    print("💡 설치 방법: pip install google-generativeai")
    exit(1)
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
