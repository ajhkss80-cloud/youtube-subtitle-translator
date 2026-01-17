#!/usr/bin/env python3
"""
YouTube 번역 워크플로 GUI 애플리케이션 (PyQt6)
반자동화 버전: 다운로드/자막추출 → 수동 번역 요청 → 영상 생성
"""

import sys
import os
import subprocess
import re
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QMessageBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
INPUT_SUBS_DIR = PROJECT_ROOT / "input_subs"
TRANSLATED_SUBS_DIR = PROJECT_ROOT / "translated_subs"

class WorkerThread(QThread):
    """단계별 작업을 실행하는 워커 스레드"""
    progress_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, steps, video_id="", hard_sub=False):
        super().__init__()
        self.steps = steps  # [(step_name, script_name, args), ...]
        self.video_id = video_id
        self.hard_sub = hard_sub
        self.process = None
        self.is_cancelled = False

    def get_python_cmd(self):
        return sys.executable

    def stop(self):
        self.is_cancelled = True
        if self.process:
            try:
                # 프로세스 그룹 전체 종료 (Codex 지적)
                import signal
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

    def run_step(self, step_name, script_name, args):
        if self.is_cancelled:
            return False

        self.status_signal.emit(f"현재 단계: {step_name}")
        self.progress_signal.emit(f"\n===== [ {step_name} 시작 ] =====")
        
        cmd = [self.get_python_cmd(), str(SCRIPTS_DIR / script_name)] + args
        self.progress_signal.emit(f"명령어: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                start_new_session=True
            )

            for line in self.process.stdout:
                if self.is_cancelled:
                    break
                self.progress_signal.emit(line.strip())

            self.process.wait()

            if self.is_cancelled:
                self.progress_signal.emit("🚫 작업이 취소되었습니다.")
                return False

            if self.process.returncode != 0:
                self.progress_signal.emit(f"❌ {step_name} 실패 (코드: {self.process.returncode})")
                return False
            
            self.progress_signal.emit(f"✅ {step_name} 완료")
            return True

        except Exception as e:
            self.progress_signal.emit(f"❌ 예외 발생: {str(e)}")
            return False
        finally:
            self.process = None

    def run(self):
        for step_name, script_name, args in self.steps:
            if not self.run_step(step_name, script_name, args):
                # 취소/실패 구분 (Codex 지적)
                if self.is_cancelled:
                    self.finished_signal.emit(False, "작업이 취소되었습니다.")
                else:
                    self.finished_signal.emit(False, f"{step_name} 단계 실패")
                return
        
        self.finished_signal.emit(True, "작업 완료!")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube 번역기 (반자동 모드)")
        self.setGeometry(100, 100, 700, 800)
        
        self.video_id = ""
        self.worker = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. 헤더
        header = QLabel("YouTube 자동 번역기")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # 2. 입력 폼
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)

        # URL
        url_layout = QVBoxLayout()
        url_label = QLabel("YouTube URL")
        url_label.setStyleSheet("font-weight: bold;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        form_layout.addLayout(url_layout)

        # Option
        self.hard_sub_check = QCheckBox("자막을 영상에 굽기 (하드섭)")
        self.hard_sub_check.setChecked(False)
        form_layout.addWidget(self.hard_sub_check)

        layout.addLayout(form_layout)

        # 3. 버튼 영역 (3개 버튼)
        btn_layout = QHBoxLayout()
        
        # 시작 버튼
        self.btn_start = QPushButton("🚀 시작 (다운로드+자막추출)")
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
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.btn_start.clicked.connect(self.start_phase1)

        # 번역완료 버튼
        self.btn_translate_done = QPushButton("✅ 번역완료 (영상생성)")
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
            ("2. 자막 추출/STT", "extract_subs.py", [self.video_id]),
        ]

        # 새 작업 시작 시 번역완료 버튼 비활성화 (Codex 지적: 상태 충돌 방지)
        self.btn_translate_done.setEnabled(False)
        self.set_running_state(True, phase=1)
        self.worker = WorkerThread(steps, self.video_id)
        self.worker.progress_signal.connect(self.log)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_phase1_finished)
        self.worker.start()

    def on_phase1_finished(self, success, message):
        self.set_running_state(False, phase=1)
        self.worker = None

        if success:
            # 번역 안내 메시지 출력
            input_srt = INPUT_SUBS_DIR / f"{self.video_id}.srt"
            translated_srt = TRANSLATED_SUBS_DIR / f"{self.video_id}.srt"
            
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

✅ 번역이 완료되면 [번역완료] 버튼을 클릭하세요!
═══════════════════════════════════════════════════════════════
"""
            self.log(guide_msg)
            self.update_status("자막 추출 완료 - 번역 대기 중...")
            self.btn_translate_done.setEnabled(True)
        else:
            QMessageBox.critical(self, "실패", message)
            self.update_status("작업 실패 ❌")

    def start_phase2(self):
        """2단계: 영상 생성"""
        if not self.video_id:
            QMessageBox.warning(self, "경고", "먼저 시작 버튼으로 자막을 추출해주세요.")
            return

        # 번역된 자막 파일 존재 확인
        translated_srt = TRANSLATED_SUBS_DIR / f"{self.video_id}.srt"
        if not translated_srt.exists():
            QMessageBox.warning(self, "경고", 
                f"번역된 자막 파일이 없습니다.\n\n{translated_srt}\n\n"
                "Antigravity에게 번역을 요청한 후 다시 시도해주세요.")
            return

        self.log(f"\n🎬 2단계 시작: 영상 생성")

        embed_args = [self.video_id]
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
