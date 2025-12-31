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
from version_info import VERSION

# ---------------------------------------------------------
# [설정 영역]
# ---------------------------------------------------------
TARGET_APP_FILE = "streamlit_app.py"
CURRENT_VERSION = VERSION
WINDOW_TITLE = f"ConsolLab (v{CURRENT_VERSION})"
VERSION_JSON_URL = "https://raw.githubusercontent.com/bbconsulting-lab/consollab/refs/heads/main/version.json"

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
        "--server.headless=true",     # 브라우저 팝업 차단
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
            latest_ver = data.get("latest_version", "0.0.2")
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
    
    # 서버가 켜질 때까지 잠시 대기 (7초)
    time.sleep(7)
    
    # 스플래시 창을 닫습니다. (메인 스레드가 풀려나게 됨)
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
    # 루프가 끝나면 창을 메모리에서 완전히 삭제합니다! ★★★
    try:
        root.destroy()
    except tk.TclError:
        pass

# ---------------------------------------------------------
# [메인 실행부]
# [추가] 창이 닫길 때 실행될 강력한 종료 함수
# ---------------------------------------------------------
def on_closed():
    print("앱이 종료됩니다. 프로세스를 정리합니다.")
    # sys.exit() 대신 os._exit(0)을 써야 남아있는 스레드(Streamlit 등)를 무시하고 즉시 완전히 꺼집니다.
    os._exit(0)

if __name__ == '__main__':
    show_splash()
    
    # 2. 스플래시가 닫히면 바로 네이티브 창 실행
    try:
        # 1) 창 객체를 변수(window)에 담습니다.
        window = webview.create_window(
            title=WINDOW_TITLE, 
            url="http://127.0.0.1:8501",
            width=1280, 
            height=800,
            resizable=True
        )
        
        # 2) [핵심] 창이 닫힐 때 on_closed 함수가 실행되도록 연결합니다.
        window.events.closed += on_closed
        
        # 3) 앱 시작 (아이콘 설정 포함)
        webview.start(icon=resource_path("logo.ico"))
        
    except Exception as e:
        print(f"Error: {e}")
        # 혹시 모를 에러 상황에서도 확실히 끄기 위해
        os._exit(0)