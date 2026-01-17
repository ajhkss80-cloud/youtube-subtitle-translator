# YouTube Subtitle Translator

> YouTube 영상을 자동으로 다운로드하고, 자막을 추출/번역하여 최종 영상을 생성하는 도구

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ 주요 기능

- 🎬 **YouTube 영상 다운로드** - yt-dlp를 사용한 고품질 영상 다운로드
- 📝 **자막 추출** - 기존 자막 다운로드 또는 Whisper STT로 음성 인식
- 🌏 **자막 번역** - AI 기반 한국어 번역 (반자동 워크플로)
- 🎥 **자막 삽입** - 소프트섭/하드섭 선택 가능

---

## 🚀 빠른 시작

### 1. 요구사항

- Python 3.10 이상
- ffmpeg (시스템 설치 필요)
- GOOGLE_API_KEY (Gemini API)

### 2. ffmpeg 설치

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
# 또는 https://www.gyan.dev/ffmpeg/builds/ 에서 다운로드 후 PATH에 추가
```

### 3. Python 의존성 설치

```bash
# 저장소 클론
git clone https://github.com/ajhkss80-cloud/youtube-subtitle-translator.git
cd youtube-subtitle-translator

# 가상환경 생성 및 활성화
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat

# 의존성 설치
pip install yt-dlp openai-whisper PyQt6 google-generativeai
```

### 4. API 키 설정

```bash
# Linux/Mac
export GOOGLE_API_KEY="your-api-key"

# Windows (PowerShell)
$env:GOOGLE_API_KEY="your-api-key"

# Windows (CMD)
set GOOGLE_API_KEY=your-api-key
```

> ⚠️ **보안 주의**: API 키를 파일에 저장할 경우 `.gitignore`에 추가하세요!

### 5. 실행

```bash
# Linux/Mac - GUI 실행
./run_gui.sh

# Windows / 직접 실행
python scripts/gui_app.py
```

---

## 📖 사용 방법

### 반자동 워크플로 (GUI 권장)

이 프로젝트는 **반자동 워크플로**를 사용합니다. 번역 단계에서 AI(Gemini API 토큰 제한)보다 정확한 결과를 위해 사용자가 직접 AI에게 번역을 요청합니다.

1. **시작 버튼** 클릭 → YouTube URL 입력
2. 영상 다운로드 + 자막 추출 자동 진행
3. 화면에 표시된 안내에 따라 **AI 도구에게 번역 요청**
   - `input_subs/VIDEO_ID.srt` → `translated_subs/VIDEO_ID.srt`
4. 번역 완료 후 **번역완료 버튼** 클릭
5. 최종 영상 생성 완료! (`final_videos/VIDEO_ID_translated.mp4`)

### CLI 개별 실행

```bash
# 1. 영상 다운로드
python scripts/download.py "https://youtube.com/watch?v=VIDEO_ID"

# 2. 자막 추출 (기존 자막 또는 Whisper STT)
python scripts/extract_subs.py VIDEO_ID

# 3. 자막 번역 (Gemini API 사용)
python scripts/translate.py VIDEO_ID
# 또는 수동으로 파일 편집: input_subs/VIDEO_ID.srt → translated_subs/VIDEO_ID.srt

# 4. 최종 영상 생성
python scripts/embed_subs.py VIDEO_ID        # 소프트섭 (기본)
python scripts/embed_subs.py VIDEO_ID --hard # 하드섭 (영상에 굽기)
```

---

## 📁 프로젝트 구조

```
youtube-subtitle-translator/
├── scripts/
│   ├── download.py      # 영상 다운로드 (yt-dlp)
│   ├── extract_subs.py  # 자막 추출/STT (Whisper)
│   ├── translate.py     # 자막 번역 (Gemini API) - 토큰 제한으로 긴 자막은 수동 권장
│   ├── embed_subs.py    # 자막 삽입 (ffmpeg)
│   └── gui_app.py       # PyQt6 GUI 애플리케이션
├── downloads/           # 다운로드된 원본 영상
├── input_subs/          # 추출된 원본 자막 (.srt)
├── translated_subs/     # 번역된 자막 (.srt)
├── final_videos/        # 최종 출력 영상 (.mp4)
├── rules.md             # 번역 가이드라인
├── CHANGELOG.md         # 변경 이력
├── run_gui.sh           # GUI 실행 스크립트 (Linux/Mac)
└── set_env.sh           # 환경 변수 설정 (예시, .gitignore 권장)
```

---

## ⚙️ 설정

### 환경 변수

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `GOOGLE_API_KEY` | Gemini API 키 | ✅ |

### 자막 옵션

| 옵션 | 설명 |
|------|------|
| 소프트섭 (기본) | 자막을 별도 트랙으로 삽입, 플레이어에서 on/off 가능 |
| 하드섭 (`--hard`) | 자막을 영상에 직접 굽기, 항상 표시됨 |

### Whisper 모델 설정

`scripts/extract_subs.py`에서 모델 크기를 변경할 수 있습니다:

| 모델 | VRAM | 품질 | 속도 |
|------|------|------|------|
| `tiny` | ~1GB | ★☆☆☆☆ | 빠름 |
| `base` (기본) | ~1GB | ★★☆☆☆ | 빠름 |
| `small` | ~2GB | ★★★☆☆ | 보통 |
| `medium` | ~5GB | ★★★★☆ | 느림 |
| `large` | ~10GB | ★★★★★ | 매우 느림 |

---

## ⚠️ 보안 주의사항

- **GOOGLE_API_KEY**는 절대 Git에 커밋하지 마세요
- `set_env.sh` 파일을 사용할 경우 `.gitignore`에 추가되어 있는지 확인하세요
- 환경 변수는 시스템 환경 설정이나 `.env` 파일(gitignore 처리)로 관리 권장

---

## 📋 번역 가이드라인

자세한 번역 규칙은 [rules.md](rules.md)를 참고하세요.

### 핵심 원칙
- ✅ 타임코드 절대 변경 금지
- ✅ 자연스러운 한국어 표현 사용
- ✅ 용어 일관성 유지
- ✅ 줄당 42자 이내, 최대 2줄

---

## 🔧 트러블슈팅

### 자막 다운로드 실패 (429 오류)
- YouTube 요청 제한으로 인한 오류
- 잠시 후 다시 시도하거나, Whisper STT가 자동으로 대체 실행됩니다

### Whisper 인식 품질 저하
- `base` 모델 대신 `medium` 또는 `large` 모델 사용 권장
- GPU가 없으면 CPU 모드로 실행되어 매우 느릴 수 있음

### ffmpeg 오류
```bash
# 설치 확인
ffmpeg -version

# 설치되지 않은 경우
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### ModuleNotFoundError
```bash
# 가상환경 활성화 확인
which python  # venv 경로가 나와야 함

# 의존성 재설치
pip install yt-dlp openai-whisper PyQt6 google-generativeai
```

---

## 📜 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 크레딧

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube 다운로드
- [OpenAI Whisper](https://github.com/openai/whisper) - 음성 인식
- [Google Gemini](https://ai.google.dev/) - AI 번역
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI 프레임워크

---

## 📝 변경 이력

자세한 변경 이력은 [CHANGELOG.md](CHANGELOG.md)를 참고하세요.

---

## 🤖 문서 검증

이 README는 다음 AI들의 크로스 검증을 거쳤습니다:
- **Codex** (OpenAI) - 구조 및 정확성 검토
- **Claude Code** (Anthropic) - 상세 내용 검토
- **Antigravity** (Google) - 최종 통합 및 작성
