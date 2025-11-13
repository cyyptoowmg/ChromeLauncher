import os
import sys
import json
import math
import time
import pygetwindow as gw
import pyautogui

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTextEdit, QSpinBox,
    QFileDialog, QMessageBox, QScrollArea, QLineEdit
)
from PyQt5.QtCore import Qt

from profile_scanner import scan_profiles
from layout_manager import auto_layout
from chrome_manager import ChromeManager

CONFIG_FILE = "config.json"


class ChromeLauncherUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chrome Multi Profile Launcher - Advanced")
        self.setGeometry(200, 100, 900, 600)

        self.manager = ChromeManager()
        self.profile_folder = ""
        self.profile_widgets = []
        self.config = {}

        self.load_config()
        self.build_ui()

        if self.profile_folder:
            self.load_profiles()

    # ========================================
    # UI 구성
    # ========================================
    def build_ui(self):
        layout = QHBoxLayout(self)

        # 좌측 프로필 목록
        left = QVBoxLayout()
        layout.addLayout(left, 4)

        btn_folder = QPushButton("📂 프로필 폴더 선택")
        btn_folder.clicked.connect(self.select_folder)
        left.addWidget(btn_folder)

        # 프로필 스크롤
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.profile_area = QWidget()
        self.profile_layout = QVBoxLayout(self.profile_area)
        scroll.setWidget(self.profile_area)
        left.addWidget(scroll)

        # 전체 선택/해제
        hl = QHBoxLayout()
        btn_all = QPushButton("전체 선택")
        btn_all.clicked.connect(self.select_all)
        hl.addWidget(btn_all)

        btn_none = QPushButton("선택 해제")
        btn_none.clicked.connect(self.select_none)
        hl.addWidget(btn_none)
        left.addLayout(hl)

        # ----------------------------------------
        # 오른쪽 설정 패널
        # ----------------------------------------
        right = QVBoxLayout()
        layout.addLayout(right, 3)

        right.addWidget(QLabel("⚙ 실행 딜레이(초):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 3)
        self.delay_spin.setValue(self.config.get("delay", 1))
        right.addWidget(self.delay_spin)

        right.addWidget(QLabel("⚙ 작업표시줄 높이 보정(px):"))
        self.taskbar_spin = QSpinBox()
        self.taskbar_spin.setRange(0, 200)
        self.taskbar_spin.setValue(self.config.get("taskbar", 100))
        right.addWidget(self.taskbar_spin)

        # 실행 버튼
        btn_run = QPushButton("🚀 실행하기")
        btn_run.clicked.connect(self.run_selected)
        right.addWidget(btn_run)

        # 종료 버튼
        btn_kill = QPushButton("🧹 내가 실행한 Chrome 종료")
        btn_kill.clicked.connect(self.kill_chrome)
        right.addWidget(btn_kill)

        # 로그창
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        right.addWidget(self.log)

    # ========================================
    # 설정 저장/로드
    # ========================================
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                self.config = json.load(open(CONFIG_FILE, "r"))
                self.profile_folder = self.config.get("folder", "")
            except:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        self.config["delay"] = self.delay_spin.value()
        self.config["taskbar"] = self.taskbar_spin.value()
        self.config["folder"] = self.profile_folder
        json.dump(self.config, open(CONFIG_FILE, "w"), indent=4)

    # ========================================
    # 폴더 선택 및 프로필 로드
    # ========================================
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "프로필 폴더 선택")
        if folder:
            self.profile_folder = folder
            self.save_config()
            self.load_profiles()

    def load_profiles(self):
        for w in self.profile_widgets:
            w.deleteLater()
        self.profile_widgets.clear()

        profiles = scan_profiles(self.profile_folder)

        for p in profiles:
            cb = QCheckBox(p["name"])
            cb.shortcut_path = p["path"]
            self.profile_layout.addWidget(cb)
            self.profile_widgets.append(cb)

        self.log_msg(f"📄 프로필 {len(profiles)}개 로드됨")

    # ========================================
    # 전체 선택/해제
    # ========================================
    def select_all(self):
        for w in self.profile_widgets:
            w.setChecked(True)

    def select_none(self):
        for w in self.profile_widgets:
            w.setChecked(False)

    # ========================================
    # 실행 로직
    # ========================================
    def run_selected(self):
        selected = [w for w in self.profile_widgets if w.isChecked()]
        total = len(selected)

        if total == 0:
            QMessageBox.warning(self, "경고", "실행할 프로필을 선택하세요.")
            return

        delay = self.delay_spin.value()
        taskbar = self.taskbar_spin.value()

        # 창 배치 계산
        screen_w, screen_h = pyautogui.size()
        screen_h -= taskbar

        cols, rows = auto_layout(total)
        window_w = screen_w // cols
        window_h = screen_h // rows

        self.log_msg(f"🔢 자동 배치: {cols} x {rows}")
        existing_windows = gw.getAllWindows()

        # 순서대로 실행
        for idx, widget in enumerate(selected):
            pid = self.manager.launch_profile(widget.shortcut_path, delay, self.log_msg)
            if not pid:
                continue

            # 창 찾아서 배치
            win = self.manager.find_new_window(existing_windows)
            if win:
                try:
                    win.restore()  # 최대화 해제 (중요!!)
                    time.sleep(0.2)
                except:
                    pass

                x = (idx % cols) * window_w
                y = (idx // cols) * window_h
                self.manager.move_and_resize(win, x, y, window_w, window_h)

                self.log_msg(f"🖥 배치 완료: {widget.text()} → {x},{y}")
            else:
                self.log_msg(f"⚠ 창 찾기 실패: {widget.text()}")

        self.save_config()
        self.log_msg("✅ 실행 완료")

    # ========================================
    # Chrome 종료
    # ========================================
    def kill_chrome(self):
        self.manager.kill_launched(self.log_msg)

    # ========================================
    # 로그 출력
    # ========================================
    def log_msg(self, msg):
        self.log.append(msg)
        self.log.ensureCursorVisible()


# ========================================
# 메인
# ========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ChromeLauncherUI()
    ui.show()
    sys.exit(app.exec_())
