import streamlit as st
import hashlib
import secrets
from datetime import datetime, timedelta
from database import get_connection

def hash_password(password: str) -> str:
    """비밀번호 해시화"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id: int) -> str:
    """세션 생성"""
    session_id = secrets.token_urlsafe(32)
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 기존 세션 삭제
        cursor.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))
        
        # 새 세션 생성 (24시간 유효)
        expires_at = datetime.now() + timedelta(days=1)
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, expires_at)
            VALUES (%s, %s, %s)
        """, (session_id, user_id, expires_at))
        
        # 마지막 로그인 시간 업데이트
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (user_id,))
        
        conn.commit()
        return session_id
    
    finally:
        conn.close()

def check_session():
    """세션 확인"""
    if 'session_id' not in st.session_state:
        st.switch_page("pages/login.py")
        return None
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.user_id, u.username, u.full_name, u.is_admin 
            FROM sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_id = %s AND s.expires_at > CURRENT_TIMESTAMP
        """, (st.session_state.session_id,))
        
        result = cursor.fetchone()
        if not result:
            st.switch_page("pages/login.py")
            return None
            
        return {
            'user_id': result[0],
            'username': result[1],
            'full_name': result[2],
            'is_admin': result[3]
        }
    
    finally:
        conn.close()

def login_page():
    if 'session_id' in st.session_state:
        st.switch_page("app.py")
        return
    
    st.title("로그인")
    
    username = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    
    if st.button("로그인", type="primary"):
        if not username or not password:
            st.error("아이디와 비밀번호를 입력해주세요.")
            return
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT user_id, is_admin 
                FROM users 
                WHERE username = %s AND password = %s
            """, (username, hash_password(password)))
            
            result = cursor.fetchone()
            if result:
                session_id = create_session(result[0])
                st.session_state.session_id = session_id
                st.session_state.is_admin = result[1]
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
        
        finally:
            conn.close()

def log_edit(table_name: str, record_id: int, field_name: str, old_value: str, new_value: str, edit_type: str):
    """수정 이력 기록"""
    user = check_session()
    if not user:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if table_name == 'project':
            cursor.execute("""
                INSERT INTO project_edit_history 
                (project_id, user_id, edit_type, field_name, old_value, new_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (record_id, user['user_id'], edit_type, field_name, old_value, new_value))
        elif table_name == 'po':
            cursor.execute("""
                INSERT INTO po_edit_history 
                (po_id, user_id, edit_type, field_name, old_value, new_value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (record_id, user['user_id'], edit_type, field_name, old_value, new_value))
        
        conn.commit()
    
    finally:
        conn.close()