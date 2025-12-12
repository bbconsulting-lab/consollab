import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import time
import signal
import requests
import webbrowser
from packaging import version
from streamlit.web import cli as stcli
import webview

# ---------------------------------------------------------
# [설정 영역]
# ---------------------------------------------------------
TARGET_APP_FILE = "streamlit_app.py"
WINDOW_TITLE = "ConsolLab"
CURRENT_VERSION = "0.0.1"
VERSION_JSON_URL = "https://github.com/bbconsulting-lab/consollab/blob/main/version.json" # 실제 URL로 변경

# 텍스트 설정
TEXT_INIT = "Initializing..."
TEXT_CHECK = "Checking for updates..."
TEXT_START = "Starting Application..."

BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#333333"
ACCENT_COLOR = "#FF4B4B"
FONT_STYLE = ("Segoe UI", 12)

# ---------------------------------------------------------
# [함수] 경로 및 리소스 설정
# ---------------------------------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------------------------------------------------
# [함수] Streamlit 서버 실행 (백그라운드)
# ---------------------------------------------------------
def run_streamlit():
    app_path = resource_path(TARGET_APP_FILE)
    
    # 시그널 핸들러 무력화
    def dummy_signal_handler(signalnum, handler):
        pass
    signal.signal = dummy_signal_handler

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",     # ★ 중요: 브라우저 팝업 차단
        "--server.address=127.0.0.1",
        "--server.port=8501",
        "--theme.base=light"
    ]
    
    try:
        stcli.main()
    except SystemExit:
        pass
    except Exception as e:
        print(e)

# ---------------------------------------------------------
# [함수] 업데이트 체크 및 실행 로직
# ---------------------------------------------------------
def check_update_and_prepare(root, status_label):
    """
    버전 체크 -> (업데이트 없으면) -> Streamlit 시작 -> 스플래시 종료
    """
    # 1. 버전 체크
    status_label.config(text=TEXT_CHECK)
    update_found = False
    download_url = ""
    latest_ver = ""

    try:
        response = requests.get(VERSION_JSON_URL, timeout=3)
        if response.status_code == 200:
            data = response.json()
            latest_ver = data.get("latest_version", "0.0.0")
            download_url = data.get("download_url", "")
            
            if version.parse(latest_ver) > version.parse(CURRENT_VERSION):
                update_found = True
    except Exception:
        pass # 인터넷 에러 시 무시

    # 2. 업데이트 발견 시 팝업
    if update_found:
        msg = f"새로운 버전(v{latest_ver})이 있습니다.\n지금 업데이트 하시겠습니까?"
        if messagebox.askyesno("업데이트 알림", msg, parent=root):
            if download_url:
                webbrowser.open(download_url)
            root.destroy()
            sys.exit() # 프로그램 종료
            return

    # 3. 업데이트 없음 -> 앱 시작 절차 진행
    status_label.config(text=TEXT_START)
    
    # Streamlit 서버 스레드 시작
    t = threading.Thread(target=run_streamlit)
    t.daemon = True
    t.start()
    
    # 서버가 켜질 때까지 잠시 대기 (2초)
    time.sleep(2)
    
    # ★ 중요: 스플래시 창을 닫습니다. (메인 스레드가 풀려나게 됨)
    root.quit()

# ---------------------------------------------------------
# [GUI] 스플래시 스크린
# ---------------------------------------------------------
def show_splash():
    root = tk.Tk()
    root.overrideredirect(True)
    
    # 화면 중앙 배치
    width, height = 400, 250
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg=BG_COLOR)
    
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    status_label = tk.Label(
        main_frame, text=TEXT_INIT, font=FONT_STYLE, bg=BG_COLOR, fg=TEXT_COLOR
    )
    status_label.pack(expand=True, pady=(30, 10))
    
    style = ttk.Style()
    style.theme_use('default')
    style.configure("TProgressbar", thickness=6, background=ACCENT_COLOR)
    progress = ttk.Progressbar(
        main_frame, style="TProgressbar", orient="horizontal", 
        length=250, mode='indeterminate'
    )
    progress.pack(pady=(0, 40))
    progress.start(15)

    # 작업 스레드 시작
    def start_process():
        t = threading.Thread(target=check_update_and_prepare, args=(root, status_label))
        t.daemon = True
        t.start()
    
    root.after(200, start_process)
    root.mainloop() # 여기서 대기하다가 root.quit()이 호출되면 아래로 넘어갑니다.

# ---------------------------------------------------------
# [메인 실행부]
# ---------------------------------------------------------
if __name__ == '__main__':
    # 1. 스플래시 화면 실행 (여기서 버전체크, 서버시작 다 하고 닫힘)
    show_splash()
    
    # 2. 스플래시가 닫히면 바로 네이티브 창 실행
    # (이미 Streamlit 서버는 백그라운드에서 돌아가는 중)
    try:
        webview.create_window(
            WINDOW_TITLE, 
            "http://127.0.0.1:8501",
            width=1280, 
            height=800,
            resizable=True
        )
        webview.start(icon=resource_path("icon.ico"))
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit()