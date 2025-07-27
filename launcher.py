import sys
import os
from streamlit.web import cli as stcli

# 실행 파일과 동일한 디렉토리에 있는 app.py를 찾습니다.
# cx_Freeze가 실행될 때 __file__ 속성이 올바르게 설정되도록 합니다.
if getattr(sys, 'frozen', False):
    # 실행 파일로 실행될 때
    app_path = os.path.join(os.path.dirname(sys.executable), "app.py")
else:
    # 일반 파이썬 인터프리터로 실행될 때
    app_path = os.path.join(os.path.dirname(__file__), "app.py")

# Streamlit을 실행하기 위한 인자 설정
# 'streamlit run app.py'와 동일한 효과
sys.argv = [
    "streamlit",
    "run",
    app_path,
    "--server.port=8501",
    "--global.developmentMode=false",
]

# Streamlit 실행
sys.exit(stcli.main())
