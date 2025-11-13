import subprocess
import time
import pygetwindow as gw
import pyautogui
import psutil

class ChromeManager:
    def __init__(self):
        self.launched_pids = []  # 내가 실행한 Chrome PID만 종료하기 위함

    def launch_profile(self, shortcut_path, delay, log_callback):
        """ 단일 Chrome 프로필 실행 """
        try:
            proc = subprocess.Popen(
                ["cmd", "/c", "start", "", shortcut_path],
                shell=True
            )
            self.launched_pids.append(proc.pid)
            log_callback(f"▶ 실행: {shortcut_path}")
            time.sleep(delay)
            return proc.pid
        except Exception as e:
            log_callback(f"❌ 실행 실패: {e}")
            return None

    def find_new_window(self, existing_windows):
        """ 실행 후 새로운 Chrome 창을 찾음 """
        for _ in range(10):
            time.sleep(0.3)
            now = gw.getWindowsWithTitle("Chrome")
            for win in now:
                if win not in existing_windows:
                    return win
        return None

    def move_and_resize(self, win, x, y, w, h):
        """ 창 배치 """
        try:
            win.resizeTo(w, h)
            win.moveTo(x, y)
        except:
            pass

    def kill_launched(self, log_callback):
        killed = 0

        # 부모 PID → chrome.exe 자식 프로세스 종료
        for parent_pid in self.launched_pids:
            try:
                parent_proc = psutil.Process(parent_pid)
                children = parent_proc.children(recursive=True)

                for child in children:
                    if child.name().lower().startswith("chrome"):
                        try:
                            child.terminate()
                            killed += 1
                        except:
                            pass
            except:
                pass

        log_callback(f"🧹 내가 실행한 Chrome {killed}개 종료 완료")
        self.launched_pids.clear()

