# 안티그래비티 대행자(Agent) - MCP & SKILL 목록

이 문서는 안티그래비티 에이전트가 현재 시점에서 사용 가능한 기능(Skill)과 MCP(Model Context Protocol) 관련 능력을 정리한 것입니다.

## 1. MCP (Model Context Protocol) 기능
MCP는 외부 모델이나 리소스와 문맥을 공유하기 위한 프로토콜입니다.

*   **list_resources**: 연결된 MCP 서버에서 사용 가능한 리소스 목록을 조회합니다.
*   **read_resource**: 특정 URI를 가진 MCP 리소스의 실제 내용을 읽어옵니다.
*   *(현재 활성화된 외부 MCP 서버는 동적으로 연결될 수 있습니다.)*

## 2. SKILL (사용 가능한 도구 목록)

### 🌐 브라우저 및 웹 탐색 (Browser & Web)
*   **browser_subagent**: 브라우저를 직접 제어하는 강력한 서브 에이전트를 호출합니다. 클릭, 입력, 스크롤, 탐색 등 실제 사용자와 동일한 웹 상호작용이 가능합니다. (외부 LLM 연결 시 사용)S
*   **search_web**: 구글 검색 등을 통해 웹상의 최신 정보를 요약하여 가져옵니다.
*   **read_url_content**: 특정 URL의 웹페이지 내용을 텍스트(Markdown) 형태로 빠르게 추출합니다. (시각적 상호작용 없이 데이터만 필요할 때 사용)
*   **view_content_chunk**: 대용량 웹 문서의 특정 부분을 분할하여 조회합니다.

### 💻 시스템 및 터미널 제어 (System & Terminal)
*   **run_command**: 리눅스 터미널 명령어를 실행합니다. (배경 실행, 패키지 설치, 빌드 등)
*   **send_command_input**: 실행 중인 대화형 명령어(REPL 등)에 입력을 전달하거나 종료합니다.
*   **command_status**: 백그라운드에서 실행 중인 명령어의 상태와 출력을 확인합니다.
*   **read_terminal**: 특정 터미널 프로세스의 출력 내용을 읽어옵니다.

### 📂 파일 조작 및 탐색 (File Operations)
*   **write_to_file**: 새로운 파일을 생성하거나 내용을 덮어씁니다.
*   **view_file**: 파일의 내용을 조회합니다. (최대 800줄 단위)
*   **list_dir**: 디렉토리 내의 파일 및 하위 폴더 목록을 조회합니다.
*   **find_by_name**: 파일 이름 패턴(Glob)을 기반으로 파일을 검색합니다.
*   **grep_search**: 파일 내용 중 특정 문자열이나 정규식 패턴을 검색합니다.

### 📝 코드 편집 및 분석 (Code Edit & Analysis)
*   **replace_file_content**: 파일의 특정 구간(연속된 라인)을 새로운 내용으로 정확하게 교체합니다.
*   **multi_replace_file_content**: 파일 내 여러 흩어진 구간을 한 번에 수정합니다.
*   **view_file_outline**: 소스 코드의 클래스, 함수 구조 등 아웃라인을 파악합니다.
*   **view_code_item**: 특정 클래스나 함수의 정의 부분만 핀포인트로 조회합니다.

### 🎨 창작 및 시각화 (Creative)
*   **generate_image**: 텍스트 프롬프트를 기반으로 이미지나 UI 목업을 생성합니다.
