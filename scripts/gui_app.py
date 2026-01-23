#!/usr/bin/env python3
"""
GUI Application for YouTube Subtitle Translator
"""
import sys
import re
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QCheckBox, QRadioButton, QButtonGroup, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# 프로젝트 루트 경로 추가 (모듈 import 위해)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ArgosTranslatorAdapter import
from src.infrastructure.translators.argos_translator import ArgosTranslatorAdapter
from src.domain.entities.subtitle import Subtitle
from src.domain.value_objects.video_id import VideoId

# 경로 상수
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
INPUT_SUBS_DIR = PROJECT_ROOT / "input_subs"
TRANSLATED_SUBS_DIR = PROJECT_ROOT / "translated_subs"
FINAL_VIDEOS_DIR = PROJECT_ROOT / "final_videos"


class TranslationWorkerThread(QThread):
    """Argos 번역 전용 워커 스레드"""
    progress_signal = pyqtSignal(str, float)  # message, percentage
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, video_id):
        super().__init__()
        self.video_id = video_id
        self._is_running = True
        self.translator = None

    def run(self):
        try:
            input_srt = INPUT_SUBS_DIR / f"{self.video_id}.srt"
            output_srt = TRANSLATED_SUBS_DIR / f"{self.video_id}.srt"

            if not input_srt.exists():
                self.finished_signal.emit(False, f"원본 자막 파일을 찾을 수 없습니다: {input_srt}")
                return

            # Lazy initialization: 번역 시작 시점에만 Argos 초기화
            self.progress_signal.emit("Argos 번역 엔진 초기화 중...", 0.0)
            self.translator = ArgosTranslatorAdapter()

            self.progress_signal.emit("자막 파일 로딩 중...", 5.0)

            # Subtitle 객체 생성
            subtitle = Subtitle(
                video_id=VideoId(self.video_id),
                file_path=input_srt,
                language="en",  # 원본 언어 (영어 가정)
                format="srt",
            )

            # 번역 실행
            def progress_callback(message: str, percent: float):
                if self._is_running:
                    self.progress_signal.emit(message, percent)

            translated_subtitle = self.translator.translate(
                subtitle=subtitle,
                target_language="ko",
                progress_callback=progress_callback
            )

            if not self._is_running:
                self.finished_signal.emit(False, "번역이 취소되었습니다.")
                return

            # 번역된 자막 저장
            self.progress_signal.emit("번역된 자막 저장 중...", 95.0)
            output_srt.parent.mkdir(parents=True, exist_ok=True)
            output_srt.write_text(translated_subtitle.text, encoding="utf-8")

            # [Added] 소프트섭 편의를 위해 원본 영상 폴더로 자막 자동 복사 (VLC/플레이어 호환용)
            try:
                video_dir = DOWNLOADS_DIR / str(self.video_id)
                if video_dir.exists():
                    # 플레이어 자동 인식을 위해 'video.srt' 및 'video.ko.srt'로 복사
                    shutil.copy2(output_srt, video_dir / "video.srt")
                    shutil.copy2(output_srt, video_dir / "video.ko.srt")
                    self.progress_signal.emit(f"💡 소프트섭 자막이 영상 폴더에 복사되었습니다.", 97.0)
            except Exception as e:
                # 자막 복사 실패는 비치명적 오류이므로 로그만 출력
                self.progress_signal.emit(f"⚠️ 소프트섭 복사 중 오류 (무시됨): {e}", 97.0)

            self.progress_signal.emit("번역 완료!", 100.0)
            self.finished_signal.emit(True, f"번역 완료: {output_srt}")

        except Exception as e:
            import traceback
            error_msg = f"번역 중 오류 발생:\n{str(e)}\n\n{traceback.format_exc()}"
            self.finished_signal.emit(False, error_msg)

    def stop(self):
        self._is_running = False


class WorkerThread(QThread):
    progress_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, steps, video_id, is_hard_sub=False, translator_mode="argos"):
        super().__init__()
        self.steps = steps
        self.video_id = video_id
        self.is_hard_sub = is_hard_sub
        self.translator_mode = translator_mode
        self._is_running = True
        self.process_output = []  # 실행 결과 저장용

    def run(self):
        import subprocess

        for step_name, script_name, args in self.steps:
            if not self._is_running:
                break

            self.progress_signal.emit(f"\n--- {step_name} 진행 중 ---")
            self.status_signal.emit(f"{step_name}...")

            script_path = PROJECT_ROOT / "scripts" / script_name
            cmd = [sys.executable, str(script_path)] + args

            try:
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
                )

                for line in process.stdout:
                    if not self._is_running:
                        process.terminate()
                        break
                    output_line = line.strip()
                    self.process_output.append(output_line)
                    self.progress_signal.emit(output_line)

                return_code = process.wait()
                if return_code != 0 and self._is_running:
                    # 에러 분석: 메모리 부족 여부 확인
                    output_text = "\n".join(self.process_output[-50:]).lower()
                    oom_patterns = [
                        'outofmemory', 'out of memory', 'cuda out of memory',
                        'cuda error', 'cudnn error', 'vram', 'allocation failed',
                        'memory allocation', 'torch.cuda.outofmemoryerror'
                    ]
                    is_oom = any(pattern in output_text for pattern in oom_patterns)
                    
                    error_msg = f"{step_name} 실패 (Code: {return_code})"
                    if is_oom:
                        error_msg += " [메모리 부족]"
                    
                    self.finished_signal.emit(False, error_msg)
                    return

            except Exception as e:
                self.finished_signal.emit(False, f"에러 발생: {str(e)}")
                return

        if self._is_running:
            self.finished_signal.emit(True, "모든 작업 완료")

    def stop(self):
        self._is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Subtitle Translator (Clean Arch)")
        self.setGeometry(100, 100, 700, 600)
        self.video_id = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. URL 입력
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtu.be/...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # 2. 번역 엔진 선택
        translator_layout = QHBoxLayout()
        translator_label = QLabel("번역 엔진:")

        self.translator_group = QButtonGroup()
        self.radio_argos = QRadioButton("Argos (로컬, 무료)")
        self.radio_gemini = QRadioButton("Gemini (API, 수동)")

        self.radio_argos.setChecked(True)  # 기본값: Argos

        self.translator_group.addButton(self.radio_argos)
        self.translator_group.addButton(self.radio_gemini)

        translator_layout.addWidget(translator_label)
        translator_layout.addWidget(self.radio_argos)
        translator_layout.addWidget(self.radio_gemini)
        translator_layout.addStretch()
        layout.addLayout(translator_layout)

        # 3. Whisper 모델 선택
        whisper_layout = QHBoxLayout()
        whisper_label = QLabel("Whisper AI 모델:")
        self.whisper_combo = QComboBox()
        self.whisper_combo.addItems(["base", "small", "medium", "large"])
        self.whisper_combo.setToolTip(
            "base: 매우 빠름, 정확도 낮음 (VRAM 1GB)\n"
            "small: 빠름, 정확도 보통 (VRAM 2GB)\n"
            "medium: 느림, 정확도 높음 (VRAM 5GB)\n"
            "large: 매우 느림, 최고 품질 (VRAM 10GB)"
        )
        whisper_layout.addWidget(whisper_label)
        whisper_layout.addWidget(self.whisper_combo)
        whisper_layout.addStretch()
        layout.addLayout(whisper_layout)

        # 4. 옵션 (하드섭)
        self.hard_sub_check = QCheckBox("자막 영상에 굽기 (Hard Sub)")
        layout.addWidget(self.hard_sub_check)

        # 5. 버튼 영역
        btn_layout = QHBoxLayout()

        # 시작 버튼 (1단계)
        self.btn_start = QPushButton("🚀 시작 (다운로드+추출)")
        self.btn_start.setMinimumHeight(50)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.btn_start.clicked.connect(self.start_phase1)

        # 번역 시작 버튼 (1.5단계 - Argos 전용)
        self.btn_translate = QPushButton("🌐 번역하기 (Argos)")
        self.btn_translate.setMinimumHeight(50)
        self.btn_translate.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #117a8b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.btn_translate.setEnabled(False)
        self.btn_translate.clicked.connect(self.start_translation)

        # 번역 완료 확인 버튼 (2단계)
        self.btn_translate_done = QPushButton("✅ 영상생성")
        self.btn_translate_done.setMinimumHeight(50)
        self.btn_translate_done.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1e7e34; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.btn_translate_done.setEnabled(False)
        self.btn_translate_done.clicked.connect(self.start_phase2)

        # 중단 버튼
        self.btn_cancel = QPushButton("🛑 중단")
        self.btn_cancel.setMinimumHeight(50)
        self.btn_cancel.setStyleSheet("""
            background-color: #dc3545; color: white; font-weight: bold; border-radius: 5px;
        """)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_work)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_translate)
        btn_layout.addWidget(self.btn_translate_done)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # 4. 상태 표시
        self.progress_label = QLabel("대기 중...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #666; font-size: 14px; margin-top: 10px;")
        layout.addWidget(self.progress_label)

        # 5. 로그 영역
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            background-color: #f8f9fa; 
            font-family: monospace; 
            font-size: 12px; 
            border: 1px solid #ddd;
        """)
        layout.addWidget(self.log_area)

    def log(self, message):
        self.log_area.append(message)
        sb = self.log_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def update_status(self, message):
        self.progress_label.setText(message)

    def extract_video_id(self, url):
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
        return hashlib.md5(url.encode()).hexdigest()[:11]

    def start_phase1(self):
        """1단계: 다운로드 + 자막추출"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "경고", "YouTube URL을 입력해주세요.")
            return

        self.video_id = self.extract_video_id(url)
        self.log_area.clear()
        self.log(f"🚀 1단계 시작: 다운로드 + 자막추출")
        self.log(f"Video ID: {self.video_id}")

        steps = [
            ("1. 영상 다운로드", "download.py", [url]),
            # FIXED: 명시적으로 --video_id 및 --model 전달
            ("2. 자막 추출/STT", "extract_subs.py", [
                "--video_id", self.video_id,
                "--model", self.whisper_combo.currentText()
            ]),
        ]

        self.btn_translate_done.setEnabled(False)
        self.set_running_state(True, phase=1)
        self.worker = WorkerThread(steps, self.video_id)
        self.worker.progress_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_phase1_finished)
        self.worker.start()

    def start_translation(self):
        """번역 시작 (Argos 전용)"""
        if not self.video_id:
            QMessageBox.warning(self, "경고", "먼저 시작 버튼으로 자막을 추출해주세요.")
            return

        input_srt = INPUT_SUBS_DIR / f"{self.video_id}.srt"
        if not input_srt.exists():
            QMessageBox.warning(self, "경고",
                f"원본 자막 파일을 찾을 수 없습니다.\n\n{input_srt}")
            return

        self.log(f"\n🌐 Argos 번역 시작")
        self.log(f"원본 파일: {input_srt}")

        # TranslationWorkerThread 사용
        self.btn_translate.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.btn_start.setEnabled(False)
        self.update_status("Argos 번역 중...")

        self.worker = TranslationWorkerThread(self.video_id)
        self.worker.progress_signal.connect(self.on_translation_progress)
        self.worker.finished_signal.connect(self.on_translation_finished)
        self.worker.start()

    def on_translation_progress(self, message, percent):
        """번역 진행 상황 업데이트"""
        self.log(f"[{percent:.1f}%] {message}")
        self.update_status(f"{message} ({percent:.1f}%)")

    def on_translation_finished(self, success, message):
        """번역 완료 콜백"""
        self.worker = None
        self.btn_cancel.setEnabled(False)
        self.btn_start.setEnabled(True)
        self.btn_translate.setEnabled(True)

        if success:
            translated_srt = TRANSLATED_SUBS_DIR / f"{self.video_id}.srt"
            self.log(f"\n✅ 번역 완료!")
            self.log(f"번역된 자막: {translated_srt}")
            self.log("\n다음 단계: [영상생성] 버튼을 클릭하세요!")
            self.update_status("번역 완료 - 영상생성 대기 중...")
            self.btn_translate_done.setEnabled(True)
            QMessageBox.information(self, "완료", f"번역 완료!\n\n{translated_srt}")
        else:
            self.log(f"\n❌ 번역 실패: {message}")
            self.update_status("번역 실패 ❌")
            QMessageBox.critical(self, "번역 실패", message)

    def on_phase1_finished(self, success, message):
        self.set_running_state(False, phase=1)
        self.worker = None

        if success:
            input_srt = INPUT_SUBS_DIR / f"{self.video_id}.srt"
            translated_srt = TRANSLATED_SUBS_DIR / f"{self.video_id}.srt"

            # Argos 모드인 경우 자동 번역 버튼 활성화
            if self.radio_argos.isChecked():
                guide_msg = f"""
═══════════════════════════════════════════════════════════════
📋 자막 추출 완료!

📁 원본 자막 파일: {input_srt}

🌐 Argos 로컬 번역 엔진 선택됨
─────────────────────────────────────────────────────────────
✅ [번역하기 (Argos)] 버튼을 클릭하여 자동 번역을 시작하세요!
   (API 키 불필요, 로컬에서 즉시 실행)
═══════════════════════════════════════════════════════════════
"""
                self.log(guide_msg)
                self.update_status("자막 추출 완료 - Argos 번역 대기 중...")
                self.btn_translate.setEnabled(True)
            else:
                # Gemini 모드인 경우 수동 번역 안내
                guide_msg = f"""
═══════════════════════════════════════════════════════════════
📋 자막 추출 완료! 이제 번역을 진행해주세요.

📁 원본 자막 파일: {input_srt}

📝 Antigravity에게 다음과 같이 요청하세요:
─────────────────────────────────────────────────────────────
"{input_srt} 파일을 한국어로 번역해서
{translated_srt} 파일로 저장해주세요.
SRT 형식을 유지하고, 타임코드는 절대 수정하지 마세요."
─────────────────────────────────────────────────────────────

✅ 번역이 완료되면 [영상생성] 버튼을 클릭하세요!
═══════════════════════════════════════════════════════════════
"""
                self.log(guide_msg)
                self.update_status("자막 추출 완료 - 번역 대기 중...")
                self.btn_translate_done.setEnabled(True)
        else:
            if "[메모리 부족]" in message:
                QMessageBox.warning(
                    self, "메모리 부족",
                    "컴퓨터의 메모리(VRAM)가 부족하여 작업을 중단했습니다.\n\n"
                    "더 낮은 품질의 모델(예: base, small)을 선택한 후 다시 시도해 주세요."
                )
            else:
                QMessageBox.critical(self, "실패", message)
            self.update_status("작업 실패 ❌")

    def start_phase2(self):
        """2단계: 영상 생성"""
        if not self.video_id:
            QMessageBox.warning(self, "경고", "먼저 시작 버튼으로 자막을 추출해주세요.")
            return

        translated_srt = TRANSLATED_SUBS_DIR / f"{self.video_id}.srt"
        if not translated_srt.exists():
            QMessageBox.warning(self, "경고", 
                f"번역된 자막 파일이 없습니다.\n\n{translated_srt}\n\n"
                "Antigravity에게 번역을 요청한 후 다시 시도해주세요.")
            return

        self.log(f"\n🎬 2단계 시작: 영상 생성")

        embed_args = ["--video_id", self.video_id]
        if self.hard_sub_check.isChecked():
            embed_args.append("--hard")

        steps = [
            ("3. 최종 영상 생성", "embed_subs.py", embed_args),
        ]

        self.set_running_state(True, phase=2)
        self.worker = WorkerThread(steps, self.video_id, self.hard_sub_check.isChecked())
        self.worker.progress_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_phase2_finished)
        self.worker.start()

    def on_phase2_finished(self, success, message):
        self.set_running_state(False, phase=2)
        self.worker = None

        if success:
            final_video = PROJECT_ROOT / "final_videos" / f"{self.video_id}_translated.mp4"
            self.log(f"\n🎉 완료! 최종 영상: {final_video}")
            QMessageBox.information(self, "완료", f"영상 생성 완료!\n\n{final_video}")
            self.update_status("작업 완료 🎉")
            self.btn_translate_done.setEnabled(False)
        else:
            QMessageBox.critical(self, "실패", message)
            self.update_status("영상 생성 실패 ❌")

    def cancel_work(self):
        if self.worker and self.worker.isRunning():
            self.log("🛑 작업 취소 요청 중...")
            self.worker.stop()

    def set_running_state(self, is_running, phase=1):
        self.btn_start.setEnabled(not is_running)
        self.btn_cancel.setEnabled(is_running)
        self.url_input.setEnabled(not is_running)
        self.hard_sub_check.setEnabled(not is_running)
        
        if phase == 2:
            self.btn_translate_done.setEnabled(not is_running)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
