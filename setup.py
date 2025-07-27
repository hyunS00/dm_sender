import sys
from cx_Freeze import setup, Executable

# requirements.txt에서 패키지 목록을 가져올 수 있지만,
# 여기서는 명시적으로 지정합니다.
# cx_Freeze가 자동으로 모든 의존성을 찾지 못할 수 있으므로,
# 주요 패키지를 명시해주는 것이 안정적입니다.
packages_to_include = [
    "streamlit",
    "instagrapi",
    "pandas",
    "numpy",
    "watchdog" # Streamlit이 내부적으로 사용하는 패키지
]

# 빌드 옵션 설정
build_exe_options = {
    "packages": packages_to_include,
    "include_files": [
        "app.py",             # 메인 애플리케이션 스크립트
        "session_manager.py",
        "requirements.txt"    # 참조용으로 포함
    ],
    "excludes": ["tkinter"] # GUI 라이브러리 제외 (필요 시)
}

# 실행 파일 설정
# Windows에서 콘솔 창을 숨기려면 base="Win32GUI"
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="dm_sender_app",
    version="0.1",
    description="Instagram DM Sender Application",
    options={"build_exe": build_exe_options},
    executables=[Executable("launcher.py", base=base)]
)
