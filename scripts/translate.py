#!/usr/bin/env python3
"""
(수정됨) Gemini API를 사용한 자막 번역 스크립트
input_subs/의 SRT 파일을 읽어 rules.md 규칙에 따라 번역 후 translated_subs/에 저장합니다.
사용 가능한 모델을 자동 감지하여 404 오류 방지.
"""

import os
import sys
from pathlib import Path
import google.generativeai as genai

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_SUBS_DIR = PROJECT_ROOT / "input_subs"
TRANSLATED_SUBS_DIR = PROJECT_ROOT / "translated_subs"
RULES_PATH = PROJECT_ROOT / "rules.md"

def load_rules():
    """rules.md 파일 내용을 읽어 프롬프트에 사용할 규칙 텍스트를 반환"""
    if not RULES_PATH.exists():
        return "번역 원칙: 자연스러운 한국어 구어체(해요체)로 번역. 타임코드 유지."
    return RULES_PATH.read_text(encoding="utf-8")

def pick_model_name():
    """사용 가능한 Gemini 모델 중 generateContent를 지원하는 모델을 자동 선택"""
    # 1. 환경변수 지정이 있으면 최우선 사용
    env_model = os.getenv("GEMINI_MODEL")
    if env_model:
        return env_model
        
    try:
        # 2. 모델 목록 조회
        print("[모델 탐색] 사용 가능한 모델 검색 중...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name.replace('models/', '')
                available_models.append(name)
        
        # 3. 우선순위대로 선택
        # flash (빠름/저렴) -> pro (똑똑함) -> 아무거나
        priority_keywords = ['flash', '1.5-pro', 'gemini-pro']
        
        for keyword in priority_keywords:
            for model in available_models:
                if keyword in model:
                    return model
                    
        # 4. 우선순위 키워드가 없으면 첫 번째 사용 가능한 모델 반환
        if available_models:
            return available_models[0]
            
    except Exception as e:
        print(f"[경고] 모델 목록 조회 실패 ({e}). 기본값 사용.")
        
    # 5. 최후의 수단 (Fallback) - 최신 모델명 사용
    return "gemini-1.5-flash"


def translate_subtitle(video_id: str):
    """
    SRT 파일을 읽어 Gemini API로 번역
    """
    input_path = INPUT_SUBS_DIR / f"{video_id}.srt"
    output_path = TRANSLATED_SUBS_DIR / f"{video_id}.srt"
    
    if not input_path.exists():
        raise FileNotFoundError(f"입력 자막을 찾을 수 없습니다: {input_path}")
    
    # API 키 확인
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    
    genai.configure(api_key=api_key)
    
    # 모델 자동 선택
    model_name = pick_model_name()
    print(f"[번역 시작] {input_path.name} -> {model_name}")
    
    model = genai.GenerativeModel(model_name)
    
    srt_content = input_path.read_text(encoding="utf-8")
    rules_content = load_rules()
    
    # 프롬프트 구성
    prompt = f"""
    당신은 전문 영상 번역가입니다. 아래 제공된 원본 SRT 자막을 한국어로 번역하세요.
    
    [번역 규칙]
    {rules_content}
    
    [추가 지침]
    1. 출력은 오직 번역된 SRT 내용만 포함해야 합니다. (마크다운 코드블록 등 제외)
    2. 타임코드와 자막 번호는 원본 그대로 유지하세요.
    3. 문체는 '해요체'를 기본으로 하되, 상황에 따라 자연스럽게 처리하세요.
    
    [원본 SRT]
    {srt_content}
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Safety Filter 체크 (Claude/Codex 공통 지적)
        if not response.candidates:
            raise ValueError("Gemini API가 빈 응답을 반환했습니다. (Safety Filter 차단 가능성)")
        
        # finish_reason 체크 (안전한 방식 - SDK 버전별 호환)
        candidate = response.candidates[0]
        finish_reason = getattr(candidate, 'finish_reason', None)
        if finish_reason:
            # Enum일 수도 있고 문자열/정수일 수도 있음
            reason_str = getattr(finish_reason, 'name', str(finish_reason))
            if reason_str.upper() == 'SAFETY':
                raise ValueError(f"Gemini API가 안전 필터로 응답을 차단했습니다.")
        
        # 텍스트 추출
        if not hasattr(response, 'text') or not response.text:
            raise ValueError("Gemini API 응답에 텍스트가 없습니다.")
            
        translated_text = response.text
        
        # 마크다운 코드블록 제거 (혹시 포함될 경우)
        translated_text = translated_text.replace("```srt", "").replace("```", "").strip()
        
        # 빈 결과 체크
        if not translated_text:
            raise ValueError("번역 결과가 비어 있습니다.")
        
        TRANSLATED_SUBS_DIR.mkdir(parents=True, exist_ok=True)
        output_path.write_text(translated_text, encoding="utf-8")
        print(f"[번역 완료] {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[오류] 번역 중 에러 발생: {e}", file=sys.stderr)
        raise

def main():
    if len(sys.argv) < 2:
        print("사용법: python scripts/translate.py <video_id>")
        sys.exit(1)
        
    video_id = sys.argv[1]
    
    try:
        translate_subtitle(video_id)
    except Exception as e:
        print(f"❌ 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
