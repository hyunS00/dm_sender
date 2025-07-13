import os
import json
from instagrapi import Client

SESSION_FILE = "session.json"

def save_session(cl: Client):
    """
    인증된 클라이언트의 세션 설정을 JSON 파일에 저장합니다.
    """
    settings = cl.get_settings()
    with open(SESSION_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
    print(f"세션이 '{SESSION_FILE}' 파일에 저장되었습니다.")

def load_session() -> Client:
    """
    저장된 세션 파일이 있으면 불러오고, 없으면 새로 로그인하여 세션을 생성합니다.
    """
    print("저장된 세션을 불러오는 중...")
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                settings = json.load(f)
            
            cl = Client(settings)
            # 세션이 유효한지 확인하기 위해 간단한 요청을 보냅니다.
            cl.get_timeline_feed()
            print("세션 불러오기 성공. 기존 세션을 재사용합니다.")
            return cl
        except Exception as e:
            print(f"세션 불러오기 실패 또는 세션 만료: {e}")
            # 파일이 손상되었거나 세션이 만료된 경우, 파일을 삭제하고 새로 로그인합니다.
            os.remove(SESSION_FILE)
            print(f"'{SESSION_FILE}' 파일을 삭제했습니다.")
            return None
    else:
        print("저장된 세션 파일이 없습니다.")
        return None

def get_client(username, password) -> Client:
    """
    세션을 불러오거나 새로 로그인하여 클라이언트를 반환합니다.
    """
    cl = load_session()
    if cl:
        return cl

    print("새로운 로그인이 필요합니다.")
    cl = Client()
    cl.login(username, password)
    save_session(cl)
    return cl
