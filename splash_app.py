import tkinter as tk
from tkinter import ttk
from tkinter import messagebox # 팝업창용
import threading
import sys
import os
import time
import signal
import requests # 통신용
import webbrowser # 업데이트 링크 열기용
from packaging import version
from streamlit.web import cli as stcli

# ---------------------------------------------------------
# [설정 영역]
# ---------------------------------------------------------
TARGET_APP_FILE = "streamlit_app.py"
CURRENT_VERSION = "0.0.0"
VERSION_JSON_URL = "https://github.com/bbconsulting-lab/consollab/blob/main/version.json"

# 화면 텍스트 설정
TEXT_INIT = "Initializing..."
TEXT_CHECK = "Checking for updates..."
TEXT_START = "Starting Application..."

BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#333333"
ACCENT_COLOR = "#FF4B4B"
FONT_STYLE = ("Segoe UI", 12) # 폰트 크기 살짝 조정

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
# [함수] 업데이트 체크 로직
# ---------------------------------------------------------
def check_update_and_run(root, status_label):
    """
    버전을 체크하고, 결과에 따라 앱을 실행하거나 업데이트 팝업을 띄웁니다.
    이 함수는 별도 스레드에서 실행됩니다.
    """
    
    # 1. 상태 텍스트 변경 (GUI 업데이트는 메인 스레드에서 해야 안전하므로 after 사용 안함... 
    # 하지만 텍스트 변경 정도는 보통 괜찮으나, 안전하게 config 사용)
    status_label.config(text=TEXT_CHECK)
    
    update_found = False
    download_url = ""
    latest_ver = ""

    try:
        # 타임아웃 3초 설정 (인터넷 느리면 앱 실행 늦어지는 것 방지)
        response = requests.get(VERSION_JSON_URL, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            latest_ver = data.get("latest_version", "0.0.0")
            download_url = data.get("download_url", "")
            
            if version.parse(latest_ver) > version.parse(CURRENT_VERSION):
                update_found = True

    except Exception as e:
        print(f"Update check failed: {e}")
        # 인터넷 에러 시 그냥 조용히 넘어갑니다.

    # 2. 업데이트가 있다면 팝업 띄우기
    if update_found:
        # Tkinter 메시지박스는 메인 스레드 블로킹을 유발할 수 있으므로 주의해야 하지만,
        # 사용자 응답을 받아야 하므로 여기선 유효합니다.
        msg = f"새로운 버전(v{latest_ver})이 있습니다.\n지금 업데이트 하시겠습니까?"
        response = messagebox.askyesno("업데이트 알림", msg, parent=root)
        
        if response: # '예' 선택 시
            if download_url:
                webbrowser.open(download_url)
            root.destroy() # 앱 종료
            sys.exit()     # 프로세스 종료
            return

    # 3. 업데이트가 없거나 '아니오' 선택 시 -> Streamlit 실행
    status_label.config(text=TEXT_START)
    run_streamlit()

# ---------------------------------------------------------
# [함수] Streamlit 실행
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
        "--server.headless=false",
        "--server.address=127.0.0.1",
        "--theme.base=light"
    ]
    
    print("Streamlit 로딩 시작...")
    try:
        stcli.main()
    except SystemExit:
        pass
    except Exception as e:
        print(e)

# ---------------------------------------------------------
# [GUI] 스플래시 스크린
# ---------------------------------------------------------
def show_splash():
    root = tk.Tk()
    root.overrideredirect(True)
    
    width, height = 400, 250
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg=BG_COLOR)
    
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    # 상태 텍스트 라벨 (나중에 내용을 바꾸기 위해 변수에 담음)
    status_label = tk.Label(
        main_frame, 
        text=TEXT_INIT, 
        font=FONT_STYLE, 
        bg=BG_COLOR, 
        fg=TEXT_COLOR
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

    # -----------------------------------------------------
    # [실행 로직] 스레드 시작
    # -----------------------------------------------------
    def start_process():
        # 인자로 root와 label을 넘겨서 함수 안에서 제어하게 함
        t = threading.Thread(target=check_update_and_run, args=(root, status_label))
        t.daemon = True
        t.start()
        
        # Streamlit 로딩 완료 시점을 정확히 알기 어려우므로
        # 넉넉하게 시간을 잡아 스플래시를 닫습니다. (예: 5초)
        # 만약 업데이트 팝업이 뜨면 이 타이머 전에 처리되거나 사용자가 닫게 됨
        root.after(5000, root.destroy) 

    # 0.2초 뒤 프로세스 시작
    root.after(200, start_process)
    
    root.mainloop()

# ---------------------------------------------------------
# [메인]
# ---------------------------------------------------------
if __name__ == '__main__':
    show_splash()

    # 프로그램 유지
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass