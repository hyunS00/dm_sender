import streamlit as st
from instagrapi import Client
from instagrapi.exceptions import UserNotFound, LoginRequired, TwoFactorRequired, ChallengeRequired
import time
import os
import random
from session_manager import save_session, load_session, SESSION_FILE

st.title("📸 Instagram DM Sender")

# --- 0. 세션 관리 및 상태 초기화 ---
if 'client' not in st.session_state: st.session_state.client = None
if 'two_factor_required' not in st.session_state: st.session_state.two_factor_required = False
if 'challenge_required' not in st.session_state: st.session_state.challenge_required = False
if 'challenge_code_sent' not in st.session_state: st.session_state.challenge_code_sent = False
if 'login_info' not in st.session_state: st.session_state.login_info = {}

# --- 자동 로그인 ---
if st.session_state.client is None and not any([st.session_state.two_factor_required, st.session_state.challenge_required]):
    with st.spinner("저장된 세션 확인 중..."):
        client = load_session()
        if client:
            st.session_state.client = client
            st.success("✅ 저장된 세션으로 자동 로그인되었습니다!")
            st.info(f"'{st.session_state.client.username}' 계정으로 로그인되었습니다.")
            st.rerun()

# --- 1. 로그인 섹션 ---
if st.session_state.client is None:
    # (로그인 로직은 변경되지 않았으므로 생략)
    if st.session_state.two_factor_required:
        st.subheader("1a. 2단계 인증")
        st.info("인증 앱에 표시된 6자리 코드를 입력해주세요.")
        verification_code = st.text_input("인증 코드")
        if st.button("인증 코드 확인"):
            if verification_code:
                client = st.session_state.login_info['client']
                try:
                    with st.spinner("인증 코드 확인 중..."): client.two_factor_login(verification_code)
                    st.session_state.client = client
                    save_session(client)
                    st.success("✅ 2단계 인증 성공!"); st.session_state.two_factor_required = False; st.rerun()
                except Exception as e: st.error(f"인증 실패: {e}")
            else: st.warning("인증 코드를 입력해주세요.")
    elif st.session_state.challenge_required:
        st.subheader("1b. 본인 확인 필요")
        client = st.session_state.login_info['client']
        if not st.session_state.challenge_code_sent:
            st.info("안전한 로그인을 위해 본인 확인이 필요합니다. 인증 코드를 받을 방법을 선택하세요.")
            choices = client.challenge_choices
            if not choices: st.error("인증 방법을 가져올 수 없습니다.")
            else:
                choice_labels = [c.label for c in choices]
                chosen_label = st.radio("인증 방법 선택:", choice_labels)
                if st.button("인증 코드 보내기"):
                    chosen_index = choice_labels.index(chosen_label)
                    try:
                        with st.spinner("인증 코드를 보내는 중..."): client.challenge_select_verify_method(choices[chosen_index].value)
                        st.session_state.challenge_code_sent = True; st.rerun()
                    except Exception as e: st.error(f"코드 전송에 실패했습니다: {e}")
        else:
            st.info("받으신 6자리 인증 코드를 입력해주세요.")
            challenge_code = st.text_input("인증 코드")
            if st.button("계정 인증"):
                if challenge_code:
                    try:
                        with st.spinner("계정 인증 중..."): client.challenge_code_verify(challenge_code)
                        st.session_state.client = client
                        save_session(client)
                        st.success("✅ 본인 확인 성공!")
                        st.session_state.challenge_required = False; st.session_state.challenge_code_sent = False
                        st.rerun()
                    except Exception as e: st.error(f"인증에 실패했습니다: {e}")
                else: st.warning("인증 코드를 입력해주세요.")
    else:
        st.subheader("1. Instagram 로그인")
        username = st.text_input("사용자 이름")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if username and password:
                client = Client()
                try:
                    with st.spinner("로그인 중..."): client.login(username, password)
                    st.session_state.client = client; save_session(client); st.success("✅ 로그인 성공!"); st.rerun()
                except TwoFactorRequired:
                    st.info("2단계 인증이 필요합니다."); st.session_state.two_factor_required = True
                    st.session_state.login_info = {"client": client}; st.rerun()
                except ChallengeRequired:
                    st.info("본인 확인이 필요합니다."); st.session_state.challenge_required = True
                    st.session_state.login_info = {"client": client}; st.rerun()
                except Exception as e: st.error(f"로그인 실패: {e}")
            else: st.warning("사용자 이름과 비밀번호를 모두 입력해주세요.")

# --- 2. DM 발송 및 설정 ---
if st.session_state.client:
    if st.button("로그아웃"):
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.info("로그아웃되었습니다."); st.rerun()

    st.subheader("2. DM 내용 작성")
    recipients_str = st.text_area("수신자 사용자 이름 (한 줄에 한 명씩 입력)", height=150, placeholder="예시:\nuser1\nuser2\nuser3")
    message = st.text_area("보낼 메시지 (선택 사항)", height=100)
    uploaded_file = st.file_uploader("이미지 첨부 (선택 사항)", type=["jpg", "jpeg", "png"])

    st.subheader("3. 발송 간격 설정 (초)")
    col1, col2 = st.columns(2)
    with col1:
        min_delay = st.number_input("최소 간격", min_value=1, value=2, help="DM을 보낸 후 다음 DM을 보내기까지 대기할 최소 시간(초)입니다.")
    with col2:
        max_delay = st.number_input("최대 간격", min_value=1, value=5, help="DM을 보낸 후 다음 DM을 보내기까지 대기할 최대 시간(초)입니다.")

    if st.button("🚀 DM 발송 시작"):
        if max_delay < min_delay:
            st.warning("최대 간격은 최소 간격보다 크거나 같아야 합니다.")
        elif not recipients_str or (not message and not uploaded_file):
            st.warning("수신자 목록을 입력하고, 메시지나 이미지를 최소 한 개 이상 추가해주세요.")
        else:
            recipients = [name.strip() for name in recipients_str.split('\n') if name.strip()]
            success_list, fail_list = [], []
            total_recipients = len(recipients)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            temp_photo_path = None
            if uploaded_file:
                temp_photo_path = f"temp_{uploaded_file.name}"
                with open(temp_photo_path, "wb") as f: f.write(uploaded_file.getbuffer())

            with st.spinner(f"총 {total_recipients}명에게 메시지를 보냅니다..."):
                for i, recipient_username in enumerate(recipients):
                    status_text.text(f"({i+1}/{total_recipients}) {recipient_username}에게 보내는 중...")
                    try:
                        user_id = st.session_state.client.user_id_from_username(recipient_username)
                        
                        if temp_photo_path:
                            st.session_state.client.direct_send_photo(user_ids=[user_id], path=temp_photo_path)
                            if message: time.sleep(random.uniform(1, 3)) # 이미지와 텍스트 사이 짧은 딜레이
                        if message:
                            st.session_state.client.direct_send(message, user_ids=[user_id])
                        
                        success_list.append(recipient_username)
                        
                        # 마지막 사용자가 아니면 랜덤 딜레이 적용
                        if i < total_recipients - 1:
                            delay = random.randint(min_delay, max_delay)
                            status_text.text(f"✅ {recipient_username}에게 전송 완료. 다음까지 {delay}초 대기...")
                            time.sleep(delay)

                    except UserNotFound: fail_list.append(f"{recipient_username} (사용자를 찾을 수 없음)")
                    except LoginRequired:
                        st.error("세션 만료. 다시 로그인해주세요.")
                        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
                        for key in list(st.session_state.keys()): del st.session_state[key]
                        st.rerun(); break
                    except Exception as e: fail_list.append(f"{recipient_username} (오류: {e})")
                    
                    progress_bar.progress((i + 1) / total_recipients)

            if temp_photo_path and os.path.exists(temp_photo_path): os.remove(temp_photo_path)

            status_text.text("발송 완료!")
            st.success("🎉 DM 발송 작업이 모두 완료되었습니다!")
            if success_list: st.subheader("✅ 성공"); st.write(success_list)
            if fail_list: st.subheader("❌ 실패"); st.write(fail_list)