import streamlit.cli
import os
import sys

def get_path(filename):
    """ 실행 파일 내부의 리소스 경로를 올바르게 찾습니다. """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller로 패키징된 경우, _MEIPASS는 임시 폴더를 가리킵니다.
        return os.path.join(sys._MEIPASS, filename)
    # 일반 파이썬 환경에서 실행된 경우
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

if __name__ == "__main__":
    # PyInstaller로 패키징되었을 때 Streamlit이 올바른 경로를 찾도록 설정합니다.
    os.environ["STREAMLIT_RUN_MAIN_SCRIPT_PATH"] = get_path("app.py")
    
    try:
        # Streamlit의 내부 CLI 함수를 직접 호출합니다.
        # sys.argv를 조작하여 'streamlit run app.py'와 동일한 효과를 냅니다.
        sys.argv = ["streamlit", "run", get_path("app.py")]
        streamlit.cli.main()
    except Exception as e:
        # 오류 발생 시 터미널에 메시지를 표시하고 사용자가 확인할 수 있도록 합니다.
        print(f"An error occurred while trying to run the application: {e}")
        input("Press Enter to exit...")