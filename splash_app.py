# splash_app.py
import tkinter as tk
from tkinter import ttk
import threading
import sys
import os
import time
import signal
from streamlit.web import cli as stcli

# ---------------------------------------------------------
# [설정 영역]
# ---------------------------------------------------------
TARGET_APP_FILE = "streamlit_app.py"
SPLASH_TEXT = "Starting Application..."
BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#333333"
ACCENT_COLOR = "#FF4B4B"
FONT_STYLE = ("Segoe UI", 14, "bold")
SPLASH_TIMEOUT = 3000  # 3초

# ---------------------------------------------------------
# [함수 1] 경로 설정 (PyInstaller 대응)
# ---------------------------------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------------------------------------------------
# [함수 2] Streamlit 서버 실행 (스레드용)
# ---------------------------------------------------------
def run_streamlit():
    app_path = resource_path(TARGET_APP_FILE)
    
    # [시그널 에러 방지] 
    def dummy_signal_handler(signalnum, handler):
        pass
    signal.signal = dummy_signal_handler

    # Streamlit 실행 옵션 설정
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=false",    # 브라우저 자동 실행
        "--server.address=127.0.0.1", # 방화벽 팝업 차단
        "--theme.base=light"
    ]
    
    print("Streamlit 서버를 시작합니다...") # 디버깅용 로그
    try:
        stcli.main()
    except SystemExit:
        pass # 정상 종료 시 무시
    except Exception as e:
        print(f"Error: {e}") # 에러 발생 시 출력

# ---------------------------------------------------------
# [GUI] 스플래시 스크린
# ---------------------------------------------------------
def show_splash():
    root = tk.Tk()
    root.overrideredirect(True) # 타이틀바 제거
    
    # 화면 중앙 배치
    width, height = 400, 250
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg=BG_COLOR)
    
    # UI 구성
    main_frame = tk.Frame(root, bg=BG_COLOR)
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)
    
    label = tk.Label(
        main_frame, 
        text=SPLASH_TEXT, 
        font=FONT_STYLE, 
        bg=BG_COLOR, 
        fg=TEXT_COLOR
    )
    label.pack(expand=True, pady=(30, 10))
    
    # 로딩바
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
    # [★ 핵심 수정] 스레드 실행 타이밍 변경
    # -----------------------------------------------------
    def start_streamlit_thread():
        t = threading.Thread(target=run_streamlit)
        t.daemon = True # 메인 프로세스 종료 시 같이 종료됨 (하지만 아래 while True로 방어함)
        t.start()
    
    # 창이 뜨고 난 뒤(200ms 후)에 무거운 작업을 시작함 -> 스플래시가 확실히 보임
    root.after(200, start_streamlit_thread)

    # 지정된 시간 후 스플래시 창 종료
    root.after(SPLASH_TIMEOUT, root.destroy)
    
    root.mainloop()

# ---------------------------------------------------------
# [메인 실행부]
# ---------------------------------------------------------
if __name__ == '__main__':
    # 1. 스플래시 화면 실행 (여기서 3초간 머뭄)
    show_splash() 

    # 2. 스플래시가 닫힌 후에도 프로그램이 죽지 않도록 유지
    # (백그라운드의 Streamlit 스레드를 살려둠)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass