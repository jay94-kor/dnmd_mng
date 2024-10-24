import streamlit as st
from database import create_tables, reset_database
import pages.basic_info as basic_info
import pages.po_issue as po_issue
import pages.dashboard as dashboard
from auth import check_session, log_edit, login_page

# 페이지 설정
st.set_page_config(
    page_title="프로젝트 관리 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사이드바
with st.sidebar:
    st.title("프로젝트 관리")
    
    # 메뉴 선택
    menu_options = {
        "대시보드": "📊 대시보드",
        "프로젝트 추가": "➕ 프로젝트 추가",
        "PO 발행": "📝 PO 발행"
    }
    
    selected_page = st.radio(
        "메뉴 선택",
        list(menu_options.keys()),
        format_func=lambda x: menu_options[x]
    )
    
    # 새로고침 버튼
    if st.button("🔄 새로고침"):
        st.rerun()
    
    # 버전 정보
    st.divider()
    st.caption("프로젝트 관리 시스템 v1.0")

# 페이지 네비게이션
if selected_page == "대시보드":
    dashboard.show_dashboard()
elif selected_page == "프로젝트 추가":
    basic_info.basic_info()
elif selected_page == "PO 발행":
    po_issue.po_issue()
