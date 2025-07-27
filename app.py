import streamlit as st
from instagrapi import Client
from instagrapi.exceptions import (
    UserNotFound, LoginRequired, TwoFactorRequired, ChallengeRequired, BadPassword,
    FeedbackRequired, PleaseWaitFewMinutes, SentryBlock
)
import time
import os
import random
from session_manager import save_session, load_session, SESSION_FILE
import uuid

st.title("📸 Instagram DM Sender")

# --- 0. 세션 관리 및 상태 초기화 ---
if 'client' not in st.session_state: st.session_state.client = None
if 'two_factor_required' not in st.session_state: st.session_state.two_factor_required = False
if 'challenge_required' not in st.session_state: st.session_state.challenge_required = False
if 'challenge_code_sent' not in st.session_state: st.session_state.challenge_code_sent = False
if 'login_info' not in st.session_state: st.session_state.login_info = {}

if 'user_info' not in st.session_state: st.session_state.user_info = None

# --- 자동 로그인 ---
if st.session_state.client is None and not any([st.session_state.two_factor_required, st.session_state.challenge_required]):
    with st.spinner("저장된 세션 확인 중..."):
        client = load_session()
        if client:
            try:
                # 세션 유효성 검사 및 사용자 정보 가져오기
                user_id = client.user_id
                st.session_state.user_info = client.user_info(user_id)
                st.session_state.client = client
                st.success("✅ 저장된 세션으로 자동 로그인되었습니다!")
            except LoginRequired:
                st.warning(f"세션이 만료되었습니다. 다시 로그인해주세요.")
                # 세션 파일 삭제
                if os.path.exists(SESSION_FILE):
                    os.remove(SESSION_FILE)
            except Exception as e:
                st.warning(f"세션 확인 중 오류가 발생했습니다: {e}")
                # 세션 파일 삭제
                if os.path.exists(SESSION_FILE):
                    os.remove(SESSION_FILE)

# --- 1. 로그인 섹션 ---
if st.session_state.client is None:
    # --- 1a. 2단계 인증 화면 ---
    if st.session_state.get('two_factor_required'):
        st.subheader("1a. 2단계 인증")
        st.info("인증 앱(Google Authenticator 등)에 표시된 6자리 코드를 입력해주세요.")
        verification_code = st.text_input("인증 코드", key="verification_code")
        if st.button("인증 코드 확인"):
            if verification_code:
                client = st.session_state.login_info['client']
                username = st.session_state.login_info['username']
                password = st.session_state.login_info['password']
                try:
                    with st.spinner("인증 코드 확인 중..."):
                        client.login(username, password, verification_code=verification_code)
                    st.session_state.client = client
                    st.session_state.user_info = client.user_info(client.user_id)
                    save_session(client)
                    st.success("✅ 2단계 인증 성공!")
                    # 성공 후 상태 초기화
                    st.session_state.two_factor_required = False
                    st.session_state.login_info = {}
                    st.rerun()
                except ChallengeRequired:
                    st.error("인증 코드가 올바르지 않거나 만료되었습니다. 다시 시도해주세요.")
                except PleaseWaitFewMinutes:
                    st.error("너무 많은 요청을 보냈습니다. 몇 분 후에 다시 시도해주세요.")
                except FeedbackRequired as e:
                    st.error(f"인스타그램의 활동 제한에 걸렸습니다: {client.last_json.get('feedback_message')}")
                except Exception as e:
                    st.error(f"알 수 없는 오류가 발생했습니다: {e}")
            else:
                st.warning("인증 코드를 입력해주세요.")

    # --- 1b. 본인 확인(Challenge) 화면 ---
    elif st.session_state.get('challenge_required'):
        st.subheader("1b. 본인 확인 필요")
        client = st.session_state.login_info['client']
        
        # --- 코드 전송 단계 ---
        if not st.session_state.get('challenge_code_sent'):
            st.info("안전한 로그인을 위해 본인 확인이 필요합니다. 인증 코드를 받을 방법을 선택하세요.")
            try:
                choices = client.challenge_choices
                if not choices:
                    st.error("인증 방법을 가져올 수 없습니다. 인스타그램에 직접 로그인하여 확인해보세요.")
                else:
                    choice_labels = [c.label for c in choices]
                    chosen_label = st.radio("인증 방법 선택:", choice_labels, key="challenge_choice")
                    if st.button("인증 코드 보내기"):
                        chosen_index = choice_labels.index(chosen_label)
                        try:
                            with st.spinner("인증 코드를 보내는 중..."):
                                client.challenge_select_verify_method(choices[chosen_index].value)
                            st.session_state.challenge_code_sent = True
                            st.rerun()
                        except PleaseWaitFewMinutes:
                            st.error("너무 많은 요청을 보냈습니다. 몇 분 후에 다시 시도해주세요.")
                        except FeedbackRequired as e:
                            st.error(f"인스타그램의 활동 제한에 걸렸습니다: {client.last_json.get('feedback_message')}")
                        except Exception as e:
                            st.error(f"코드 전송에 실패했습니다: {e}")
            except Exception as e:
                st.error(f"본인 확인 옵션을 가져오는 중 오류가 발생했습니다: {e}")
                st.info("잠시 후 다시 시도하거나, 인스타그램 공식 앱에서 먼저 로그인해보세요.")

        # --- 코드 입력 단계 ---
        else:
            st.info("받으신 6자리 인증 코드를 입력해주세요.")
            challenge_code = st.text_input("인증 코드", key="challenge_code")
            if st.button("계정 인증"):
                if challenge_code:
                    try:
                        with st.spinner("계정 인증 중..."):
                            client.challenge_code_verify(challenge_code)
                        st.session_state.client = client
                        st.session_state.user_info = client.user_info(client.user_id)
                        save_session(client)
                        st.success("✅ 본인 확인 성공!")
                        # 성공 후 상태 초기화
                        st.session_state.challenge_required = False
                        st.session_state.challenge_code_sent = False
                        st.session_state.login_info = {}
                        st.rerun()
                    except ChallengeRequired:
                        st.error("인증 코드가 올바르지 않거나 만료되었습니다.")
                        st.info("새 코드를 받으려면 페이지를 새로고침하고 다시 시도하세요.")
                        st.session_state.challenge_code_sent = False # 새 코드 요청 가능하도록
                    except PleaseWaitFewMinutes:
                        st.error("너무 많은 요청을 보냈습니다. 몇 분 후에 다시 시도해주세요.")
                    except FeedbackRequired as e:
                        st.error(f"인스타그램의 활동 제한에 걸렸습니다: {client.last_json.get('feedback_message')}")
                    except Exception as e:
                        st.error(f"인증에 실패했습니다: {e}")
                else:
                    st.warning("인증 코드를 입력해주세요.")

    # --- 1c. 초기 로그인 화면 ---
    else:
        st.subheader("1. Instagram 로그인")
        username = st.text_input("사용자 이름")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if username and password:
                client = Client()
                try:
                    with st.spinner("로그인 중..."):
                        client.login(username, password)
                    st.session_state.client = client
                    st.session_state.user_info = client.user_info(client.user_id) # 사용자 정보 가져오기
                    save_session(client)
                    st.success("✅ 로그인 성공!")
                    st.rerun()
                except BadPassword:
                    st.error("비밀번호가 올바르지 않습니다. 다시 확인해주세요.")
                except TwoFactorRequired:
                    st.info("2단계 인증이 필요합니다. 다음 화면으로 이동합니다.")
                    st.session_state.two_factor_required = True
                    st.session_state.login_info = {"client": client, "username": username, "password": password}
                    st.rerun()
                except ChallengeRequired:
                    st.info("본인 확인이 필요합니다. 다음 화면으로 이동합니다.")
                    st.session_state.challenge_required = True
                    st.session_state.login_info = {"client": client, "username": username, "password": password}
                    st.rerun()
                except PleaseWaitFewMinutes:
                    st.error("너무 많은 요청을 보냈습니다. 몇 분 후에 다시 시도해주세요.")
                except FeedbackRequired as e:
                    st.error(f"인스타그램의 활동 제한에 걸렸습니다: {client.last_json.get('feedback_message')}")
                # except AccountDisabled:
                #     st.error("계정이 비활성화되었습니다. 인스타그램에 직접 확인해주세요.")
                except SentryBlock as e:
                    st.error(f"인스타그램의 보안 시스템에 의해 차단되었습니다: {e}")
                except Exception as e:
                    st.error(f"알 수 없는 로그인 오류가 발생했습니다: {e}")
            else:
                st.warning("사용자 이름과 비밀번호를 모두 입력해주세요.")

# --- 2. 사용자 정보 및 DM 발송 ---
if st.session_state.client and st.session_state.user_info:
    # --- 사용자 정보 표시 ---
    st.subheader(f"👤 로그인 계정: {st.session_state.user_info.full_name}")
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(str(st.session_state.user_info.profile_pic_url), width=100)
    with col2:
        st.write(f"**사용자 이름:** {st.session_state.user_info.username}")
        st.write(f"**팔로워:** {st.session_state.user_info.follower_count} | **팔로잉:** {st.session_state.user_info.following_count}")
        if st.button("로그아웃"):
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.info("로그아웃되었습니다.")
            st.rerun()
    st.divider()

    st.subheader("2. DM 내용 작성")
    recipients_str = st.text_area("수신자 사용자 이름 (한 줄에 한 명씩 입력)", height=150, placeholder="예시:\nuser1\nuser2\nuser3")
    
    st.write("아래 3개의 메시지 중 하나가 각 수신자에게 랜덤으로 발송됩니다. 비워진 메시지 칸은 무시됩니다.")
    message1 = st.text_area("메시지 1", height=80)
    message2 = st.text_area("메시지 2", height=80)
    message3 = st.text_area("메시지 3", height=80)

    uploaded_files = st.file_uploader("이미지 첨부 (선택 사항, 여러 개 가능)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    st.subheader("3. 발송 간격 설정 (초)")
    col1, col2 = st.columns(2)
    with col1:
        min_delay = st.number_input("최소 간격", min_value=1, value=2, help="DM을 보낸 후 다음 DM을 보내기까지 대기할 최소 시간(초)입니다.")
    with col2:
        max_delay = st.number_input("최대 간격", min_value=1, value=5, help="DM을 보낸 후 다음 DM을 보내기까지 대기할 최대 시간(초)입니다.")

    if st.button("🚀 DM 발송 시작"):
        messages = [msg.strip() for msg in [message1, message2, message3] if msg.strip()]
        num_messages = len(messages)
        num_images = len(uploaded_files) if uploaded_files else 0
        
        st.info(f"▶️ {num_messages}개의 메시지와 {num_images}개의 이미지를 랜덤으로 조합하여 발송합니다.")

        if max_delay < min_delay:
            st.warning("최대 간격은 최소 간격보다 크거나 같아야 합니다.")
        elif not recipients_str or (not messages and not uploaded_files):
            st.warning("수신자 목록을 입력하고, 메시지나 이미지를 최소 한 개 이상 추가해주세요.")
        else:
            recipients = [name.strip() for name in recipients_str.split('\n') if name.strip()]
            success_list, fail_list = [], []
            total_recipients = len(recipients)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            temp_photo_paths = []
            if uploaded_files:
                temp_dir = "temp_images"
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                for uploaded_file in uploaded_files:
                    ext = os.path.splitext(uploaded_file.name)[1]
                    temp_photo_path = os.path.join(temp_dir, f"{uuid.uuid4()}{ext}")
                    with open(temp_photo_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_photo_paths.append(temp_photo_path)

            # 디버깅을 위해 생성된 임시 이미지 파일 경로를 표시합니다.
            if temp_photo_paths:
                st.write("생성된 임시 이미지 파일:")
                st.write(temp_photo_paths)

            # 매번 다른 랜덤 결과를 얻기 위해 시드를 초기화합니다.
            random.seed()

            with st.spinner(f"총 {total_recipients}명에게 메시지를 보냅니다..."):
                debug_container = st.container()
                debug_container.write("--- 발송 로그 ---")

                for i, recipient_username in enumerate(recipients):
                    status_text.text(f"({i+1}/{total_recipients}) {recipient_username}에게 보내는 중...")
                    try:
                        user_id = st.session_state.client.user_id_from_username(recipient_username)
                        
                        message_to_send = random.choice(messages) if messages else None
                        photo_to_send = random.choice(temp_photo_paths) if temp_photo_paths else None

                        # 디버깅을 위해 선택된 메시지와 이미지를 표시합니다.
                        msg_idx_str = f"메시지 {messages.index(message_to_send) + 1}" if message_to_send else "없음"
                        img_name_str = f"이미지: {os.path.basename(photo_to_send)}" if photo_to_send else "없음"
                        debug_container.write(f"-> `{recipient_username}`: {msg_idx_str}, {img_name_str}")

                        if photo_to_send:
                            st.session_state.client.direct_send_photo(user_ids=[user_id], path=photo_to_send)
                            if message_to_send:
                                time.sleep(random.uniform(1, 3))
                        
                        if message_to_send:
                            st.session_state.client.direct_send(message_to_send, user_ids=[user_id])
                        
                        success_list.append(recipient_username)
                        
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

            # 임시 이미지 파일 및 디렉토리 삭제
            if temp_photo_paths:
                for path in temp_photo_paths:
                    if os.path.exists(path):
                        os.remove(path)
                if os.path.exists("temp_images"):
                    os.rmdir("temp_images")

            status_text.text("발송 완료!")
            st.success("🎉 DM 발송 작업이 모두 완료되었습니다!")
            if success_list: st.subheader("✅ 성공"); st.write(success_list)
            if fail_list: st.subheader("❌ 실패"); st.write(fail_list)