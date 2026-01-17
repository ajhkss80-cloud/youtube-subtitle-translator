# 변경 이력 (Changelog)

> YouTube 번역 워크플로 프로젝트 변경 기록

---

## 2026-01-16

### 문서 수정

#### `rules.md` - 번역 기준 문서 전면 개정
- **변경 사유**: Codex 문서 리뷰 피드백 반영
- **주요 변경 내용**:
  1. 문체 규칙 추가 (해요체/합쇼체 구분, 금칙어 대체 가이드)
  2. SRT 품질 기준 추가 (줄 수, 글자 수, 표시 시간, 읽기 속도)
  3. 용어 통일표 확장 (기술 용어, 고유명사 처리 규칙)
  4. 숫자/단위 표기 규칙 추가
  5. 비언어 표현 규칙 추가
  6. 다중 화자 규칙 추가
  7. 예외 처리 규칙 추가
  8. 검수 체크리스트 추가

---

### 코드 수정

#### `scripts/download.py`

| 버전 | 변경 내용 | 사유 |
|------|----------|------|
| v1.0 | 초기 작성 | 기본 yt-dlp 다운로드 기능 |
| v1.1 | shorts URL 지원 추가 | Codex 피드백: URL 정규식이 shorts/ 미지원 |
| v1.1 | video_id 추출 실패 시 해시 fallback | yt-dlp가 처리 가능한 URL은 예외 발생 없이 진행 |
| v1.1 | 에러 메시지 상세화 | 디버깅 용이성 향상 |

---

#### `scripts/extract_subs.py`

| 버전 | 변경 내용 | 사유 |
|------|----------|------|
| v1.0 | 초기 작성 | 자막 추출 및 Whisper STT 기능 |
| v1.1 | 자막 선택 우선순위 로직 추가 | Codex 피드백: 첫 파일만 선택하면 잘못된 언어 선택 가능 |
| v1.1 | 에러 메시지 상세화 | ffmpeg/whisper 실패 시 디버깅 용이 |
| v1.1 | 미사용 `os` 모듈 제거 | Codex 피드백 |
| v1.2 | 언어 감지 정규식으로 변경 | Codex 2차 피드백: `tokyo`가 `ko` 포함해서 오판 |
| v1.2 | 미사용 `PREFER_MANUAL` 변수 제거 | Codex 2차 피드백 |

**언어 감지 로직 변경 상세**:
```diff
- # before: substring 매칭
- if lang in name:

+ # after: 정규식 기반
+ match = re.search(r'\.([a-z]{2})(?:\.auto)?\.(?:srt|vtt)$', filename)
```

---

#### `scripts/embed_subs.py`

| 버전 | 변경 내용 | 사유 |
|------|----------|------|
| v1.0 | 초기 작성 | 자막 삽입 및 최종 영상 생성 |
| v1.1 | `escape_ffmpeg_path()` 함수 추가 | Codex 피드백: 경로에 특수문자 있으면 ffmpeg 오류 |
| v1.1 | 하드섭 스타일 설정 분리 | 유지보수성 향상 |
| v1.1 | 에러 메시지 상세화 | 디버깅 용이성 향상 |
| v1.2 | 소프트섭에 `-map` 옵션 추가 | Codex 2차 피드백: PGS 자막 있으면 mov_text 변환 실패 |

**ffmpeg 매핑 변경 상세**:
```diff
- # before: 모든 스트림 자동 포함
- "-c", "copy",

+ # after: 명시적 스트림 선택
+ "-map", "0:v",    # 비디오
+ "-map", "0:a",    # 오디오
+ "-map", "1:0",    # 자막 파일
+ "-c:v", "copy",
+ "-c:a", "copy",
```

---

#### `scripts/translate.py`

| 버전 | 변경 내용 | 사유 |
|------|----------|------|
| v1.0 | 초기 작성 | Gemini API를 사용한 자동 번역 기능 |

---

#### `scripts/gui_app.py` (신규)

| 버전 | 변경 내용 | 사유 |
|------|----------|------|
| v1.0 | 초기 작성 | PyQt6 기반 GUI, 4단계 워크플로 통합 |
| v1.1 | 입력 검증 강화 | Codex 피드백: URL 누락 및 ID 추출 실패 시 크래시 방지 |
| v1.1 | 작업 취소 기능 추가 | Codex 피드백: 장시간 작업 중단 기능 필요 |

---

## Codex 리뷰 이력

### 1차 리뷰 (코드)
- 요청: 버그, 개선점, 보안 이슈
- 결과: 6개 이슈 발견, 2개 질문

### 2차 리뷰 (문서)
- 요청: 번역 가이드라인 검토
- 결과: 12개 개선점 발견

### 3차 리뷰 (수정 코드, 근거 요청)
- 요청: 수정된 코드 재검토, 이슈에 근거 제시
- 결과: 4개 신규 이슈 발견

### 4차 리뷰 (GUI 앱)
- 요청: GUI 안정성 및 보안 검토
- 결과: 입력 검증 및 취소 기능 안전성 확보 확인 (잔여 리스크: SIGKILL 부재로 인한 낮은 가능성의 프리징)

### 5차 긴급 수정 (다운로드 오류 해결)
- **증상**: 자막 다운로드 시 429 오류 발생하여 영상 다운로드까지 실패
- **조치 (`download.py`)**: 
  - 영상/자막 다운로드 분리
  - 자막 다운로드 실패는 무시하고 진행(Best Effort)
  - 재시도 옵션(`--retries`, `--retry-sleep`) 및 지연 옵션(`--sleep-interval`) 추가
- **조치 (`gui_app.py`)**:
  - 사용자 요청에 따라 **원클릭 통합(One-Click Pipeline)** 형태로 UI 전면 개편
  - 개별 단계 버튼 제거하고 단일 '시작' 버튼으로 4단계 자동 순차 실행

### 6차 호환성 패치
- **증상**: 구형 `yt-dlp`에서 `--retry-sleep` 고급 문법 미지원, `whisper` 명령어 PATH 인식 불가
- **조치 (`download.py`)**: `--retry-sleep` 값을 단순 정수(`5`)로 변경하여 호환성 확보
- **조치 (`extract_subs.py`)**: `whisper` 바이너리 호출 대신 `sys.executable -m whisper`로 변경하여 가상환경 내 모듈 실행 보장
- **Codex 리뷰**: 차단 회피 성능 감소 가능성 있으나 호환성 우선, 모듈 방식이 더 안전하다고 평가

### 7차 번역 오류 패치
- **증상**: `gemini-1.5-flash` 모델 404 오류 (버전 불일치 또는 미지원)
- **조치 (`translate.py`)**: `genai.list_models()`를 사용하여 현재 API 키로 접근 가능한 모델 중 `generateContent`를 지원하는 모델을 자동 탐색하고 선택하는 로직 추가.

### 8차 Whisper 실행 방식 전면 수정
- **증상**: `subprocess`로 `sys.executable -m whisper` 실행 시 `ModuleNotFoundError` 지속 발생 (환경 변수 또는 설치 경로 불일치 추정)
- **조치 (`extract_subs.py`)**: 
  - Subprocess(외부 프로세스) 호출 방식을 폐기하고, **Python 라이브러리 직접 호출 (`import whisper`)** 방식으로 변경.
  - 공식 문서 권장 사용법(`whisper.load_model`, `model.transcribe`) 적용.
  - 같은 프로세스 내에서 실행되므로 환경 변수 문제 원천 차단.

### 9차 GUI 안정성 및 크래시 패치 (3자 논의 기반)
- **증상**: 번역 단계 진입 시 프로그램 강제 종료(Crash) 또는 스레드 중단.
- **원인 분석 (Codex/Claude/Expert)**:
  1. **Thread Unsafe**: `QThread` 내에서 `subprocess.Popen(preexec_fn=os.setsid)` 사용 시 부모 프로세스까지 영향을 주어 크래시 유발 가능성 있음.
  2. **Logic Bug**: `PipelineThread` 워커에서 GUI 위젯(`hard_sub_check`) 스코프에 잘못 접근하여 `AttributeError` 발생.
- **조치 (`gui_app.py`)**:
  - `preexec_fn` 제거 및 `start_new_session=True`로 변경하여 멀티스레드 안전성 확보.
  - 변수명 버그 수정 (`hard_sub_check` -> `hard_sub`).

### 10차 3자 크로스 검증 패치 (Codex + Claude Code + Antigravity)
- **검토 방법**: Codex, Claude Code CLI 독립적 코드 리뷰 후 크로스 체크
- **조치 (`translate.py`)**:
  - 폴백 모델 `gemini-pro` → `gemini-1.5-flash`로 변경 (404 방지)
  - Safety Filter 차단 시 `response.text` 접근 예외 방지
  - 안전한 `getattr()` 사용으로 SDK 버전별 호환성 확보
- **조치 (`extract_subs.py`)**:
  - Whisper `get_writer` 의존 제거, 직접 SRT 포맷 저장
  - `result.get("segments", [])` 방어 코드 추가 (무음/인식 실패 대응)
- **최종 검증**: Codex PASS, Claude Code PASS

### 11차 GUI 반자동 모드 전환 (Codex + Claude Code 검증)
- **배경**: Gemini API 무료 티어의 출력 토큰 한도로 인해 긴 자막이 번역 중 절단됨
- **해결책**: 번역 단계를 사용자 수동 요청으로 분리 (Antigravity에게 직접 요청)
- **조치 (`gui_app.py`)**:
  - 버튼 3개 구조로 변경: 시작(다운로드+자막추출), 번역완료(영상생성), 중단
  - 자막 추출 후 번역 요청 안내 메시지 표시
  - `번역완료` 버튼은 번역 파일 존재 여부 확인 후 진행
  - 프로세스 그룹 전체 종료 (`os.killpg`) 적용 (Codex 지적)
  - 새 작업 시작 시 `번역완료` 버튼 비활성화 (상태 충돌 방지)
  - 취소/실패 메시지 구분 (UX 개선)
- **최종 검증**: Codex PASS, Claude Code PASS
