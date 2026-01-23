# YouTube Subtitle Translator

> YouTube 영상을 자동으로 다운로드하고, 자막을 추출/번역하여 최종 영상을 생성하는 도구
> **✨ Built-in Offline Translation (Argos Translate) 지원**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![Argos](https://img.shields.io/badge/Translation-Argos_Translate-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ⚠️ DISCLAIMER / 주의사항

**ENGLISH:**
> This project is intended for **educational and development testing purposes only**, not for distribution.  
> Due to copyright considerations, users are solely responsible for downloading and using this software.  
> The author assumes no liability for any misuse or legal issues arising from its use.

**한국어:**
> 본 프로젝트는 **코드 학습 및 개발 테스트 목적**으로만 제작되었으며, 배포용이 아닙니다.  
> 저작권 관계로 인해 다운로드 및 사용에 관한 모든 책임은 사용자에게 있습니다.  
> 저자는 오용이나 법적 문제에 대해 어떠한 책임도 지지 않습니다.

---

## ✨ 주요 기능

- 🎬 **YouTube 영상 다운로드** - yt-dlp를 사용한 고품질 영상 다운로드
- 📝 **자막 추출** - 기존 자막 다운로드 또는 Whisper STT로 음성 인식
- 🌏 **자막 번역** - **내장 로컬 번역엔진 (Argos Translate)** 또는 AI 도구 활용
  - **Argos Translate**: 완전 오프라인, API 키 불필요, 무료
  - **Gemini/AI 도구**: 수동 번역 (더 높은 품질)
- 🎥 **자막 삽입** - 소프트섭/하드섭 선택 가능

---

## � 워크플로 설명

이 프로젝트는 **자동 + 선택적 수동 워크플로**를 제공합니다.

| 단계 | 방식 | 설명 |
|------|------|------|
| 1. 영상 다운로드 | 🤖 자동 | yt-dlp로 자동 다운로드 |
| 2. 자막 추출 | 🤖 자동 | 기존 자막 또는 Whisper STT |
| 3. **자막 번역** | 🤖/👤 **선택** | **Argos (자동, 로컬)** 또는 **AI 도구 (수동, 고품질)** |
| 4. 영상 생성 | 🤖 자동 | ffmpeg로 자막 삽입 |

> **두 가지 번역 옵션:**
> - **Argos Translate (기본)**: 완전 오프라인, API 키 불필요, 무료. 기술 문서/일반 콘텐츠에 적합.
> - **AI 도구 (선택)**: ChatGPT, Claude, Gemini 등 직접 요청. 문맥 이해가 중요한 콘텐츠에 적합.

---

## �🚀 빠른 시작

### 1. 요구사항

- Python 3.10 이상
- ffmpeg (시스템 설치 필요)
- **API 키 불필요** (Argos Translate 내장)

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
pip install yt-dlp openai-whisper PyQt6 argostranslate
```

### 4. 실행

```bash
# Linux/Mac - GUI 실행
./run_gui.sh

# Windows / 직접 실행
python scripts/gui_app.py
```

---

## 📖 사용 방법 (GUI)

### Step 1: 시작 및 옵션 선택
1. GUI 실행 후 **YouTube URL** 입력
2. **번역 엔진 선택**:
   - **🔘 Argos (로컬, 무료)**: 완전 오프라인, API 키 불필요, 기술 문서/일반 콘텐츠 적합
   - **🔘 Gemini (API, 수동)**: AI 도구 활용, 문맥 이해가 중요한 콘텐츠 적합
3. **Whisper AI 모델 선택**:
   - **base (기본)**: 가장 빠름, 저사양 PC 권장
   - **medium/large**: 느리지만 품질이 매우 높음 (고사양 GPU/VRAM 권장)
4. **시작 버튼** 클릭
4. 영상 다운로드 + 자막 추출 자동 진행

### Step 2-A: 자동 번역 (Argos 선택 시)
1. 자막 추출 완료 후 **🌐 번역하기 (Argos)** 버튼 클릭
2. Argos 번역 엔진이 자동으로 번역 수행
3. **💡 편의 기능**: 번역 완료 시 자막이 영상 폴더(`downloads/{ID}/video.srt`)로 **자동 복사**됩니다. 
   - 이제 별도의 영상 생성 단계 없이도 VLC 등에서 원본 영상을 즉시 감상할 수 있습니다.
4. 번역 완료 후 자동으로 다음 단계로 진행

### Step 2-B: 수동 번역 (Gemini 선택 시)
추출 완료 후 화면에 안내 메시지가 표시됩니다:

```
📁 원본 자막 파일: input_subs/VIDEO_ID.srt

📝 AI 도구에게 다음과 같이 요청하세요:
"input_subs/VIDEO_ID.srt 파일을 한국어로 번역해서
translated_subs/VIDEO_ID.srt 파일로 저장해주세요.
SRT 형식을 유지하고, 타임코드는 절대 수정하지 마세요."
```

**사용 가능한 AI 도구:**
- ChatGPT
- Claude
- Gemini Web
- 기타 AI 어시스턴트

### Step 3: 완료
1. (Gemini 모드) 번역이 완료되면 **번역완료 버튼** 클릭
2. 최종 영상 자동 생성
3. 결과: `final_videos/VIDEO_ID_translated.mp4`

---

## 💻 CLI 사용법

```bash
# 1. 영상 다운로드
python scripts/download.py "https://youtube.com/watch?v=VIDEO_ID"

# 2. 자막 추출 (기존 자막 또는 Whisper STT)
python scripts/extract_subs.py VIDEO_ID

# 3. 자막 번역 (수동)
# AI 도구에 요청하여 번역:
# input_subs/VIDEO_ID.srt → translated_subs/VIDEO_ID.srt

# 4. 최종 영상 생성
python scripts/embed_subs.py VIDEO_ID        # 소프트섭 (기본)
python scripts/embed_subs.py VIDEO_ID --hard # 하드섭 (영상에 굽기)
```

---

## 📁 프로젝트 구조

```
youtube-subtitle-translator/
├── src/                           # Clean Architecture (v2.0)
│   ├── domain/                    # 도메인 계층 (비즈니스 로직)
│   │   ├── entities/              # 엔티티 (Video, Subtitle)
│   │   └── value_objects/         # 값 객체 (VideoID 등)
│   ├── application/               # 애플리케이션 계층
│   │   ├── use_cases/             # 유스케이스 (다운로드, 추출, 번역, 삽입)
│   │   └── ports/                 # 인터페이스 정의 (Ports)
│   ├── infrastructure/            # 인프라 계층 (Adapters)
│   │   ├── downloaders/           # YtDlpDownloader
│   │   ├── extractors/            # WhisperExtractor
│   │   ├── translators/           # ArgosTranslatorAdapter
│   │   └── embedders/             # FFmpegEmbedder
│   └── presentation/              # 프레젠테이션 계층
│       └── gui/                   # PyQt6 GUI
├── scripts/
│   ├── download.py                # CLI: 영상 다운로드 (yt-dlp)
│   ├── extract_subs.py            # CLI: 자막 추출/STT (Whisper)
│   ├── translate_argos.py         # CLI: Argos 번역
│   ├── translate.py               # [미사용] 자막 번역 (Gemini API)
│   ├── embed_subs.py              # CLI: 자막 삽입 (ffmpeg)
│   └── gui_app.py                 # PyQt6 GUI 애플리케이션
├── tests/                         # 단위 테스트 및 통합 테스트
├── downloads/                     # 다운로드된 원본 영상
├── input_subs/                    # 추출된 원본 자막 (.srt)
├── translated_subs/               # 번역된 자막 (.srt)
├── final_videos/                  # 최종 출력 영상 (.mp4)
├── rules.md                       # 번역 가이드라인
├── CHANGELOG.md                   # 변경 이력
└── run_gui.sh                     # GUI 실행 스크립트 (Linux/Mac)
```

> **아키텍처**: v2.0부터 **Clean Architecture (Port/Adapter 패턴)** 적용
> - **Domain**: 비즈니스 로직과 엔티티 (의존성 없음)
> - **Application**: 유스케이스와 포트 인터페이스
> - **Infrastructure**: 외부 도구 어댑터 (YtDlp, Whisper, Argos, FFmpeg)
> - **Presentation**: GUI 레이어

---

## ⚙️ 설정

### 자막 옵션 (소프트섭 vs 하드섭)

| 구분 | 소프트섭 (Soft Sub) - **권장** | 하드섭 (Hard Sub) |
|------|------|------|
| **방식** | 영상 파일 내부에 자막 트랙 포함 | 영상 위에 자막을 직접 그림 (인코딩) |
| **특징** | 자막 On/Off 가능, 다국어 지원 | 자막 제거 불가 (항상 표시) |
| **장점** | **화질 저하 없음, 생성 속도 매우 빠름** | 모든 기기/플레이어에서 표시 보장 |
| **단점** | 일부 구형 플레이어에서 인식 불가 | **생성 속도 매우 느림**, 화질 저하 가능 |
| **사용법** | "자막 영상에 굽기" 체크 해제 | "자막 영상에 굽기" 체크 선택 |

> **Tip**: 영상 재생 시 자막이 안 나온다면, 플레이어의 자막 설정에서 'Track 1' 또는 'Korean'을 선택해 주세요.

### Whisper 모델 설정 (STT 품질)

GUI의 드롭다운 메뉴에서 원하는 모델을 선택할 수 있습니다:

`scripts/extract_subs.py`에서 모델 크기를 변경할 수 있습니다:

| 모델 | VRAM | 품질 | 속도 |
|------|------|------|------|
| `tiny` | ~1GB | ★☆☆☆☆ | 빠름 |
| `base` (기본) | ~1GB | ★★☆☆☆ | 빠름 |
| `small` | ~2GB | ★★★☆☆ | 보통 |
| `medium` | ~5GB | ★★★★☆ | 느림 |
| `large` | ~10GB | ★★★★★ | 매우 느림 |

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
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg
```

### ModuleNotFoundError
```bash
# 가상환경 활성화 확인
which python  # venv 경로가 나와야 함

# 의존성 재설치
pip install yt-dlp openai-whisper PyQt6
```

---

## 📜 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 크레딧

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube 다운로드
- [OpenAI Whisper](https://github.com/openai/whisper) - 음성 인식
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI 프레임워크

---

## 📝 변경 이력

자세한 변경 이력은 [CHANGELOG.md](CHANGELOG.md)를 참고하세요.

**주요 변경:**
- **v2.0 (2026-01-17)**: Clean Architecture 리팩토링
  - Domain-Driven Design 적용 (Entities, Value Objects)
  - Application Layer (Use Cases, Ports)
  - Infrastructure Layer (Adapters: YtDlp, Whisper, FFmpeg)
  - 테스트 가능성 향상 (Mock 기반 통합 테스트)
  - 코드 품질 개선 (Rule of Three 검증 프로세스)
- v1.1: **반자동 모드 전환** - API 토큰 제한으로 인해 번역 단계를 수동으로 변경
- v1.0: 자동 번역 (Gemini API)

---

## 🤖 문서 검증

이 README는 다음 AI들의 크로스 검증을 거쳤습니다:
- **Codex** (OpenAI)
- **Claude Code** (Anthropic)
- **Antigravity** (Google)
