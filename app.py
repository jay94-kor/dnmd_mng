import streamlit as st
from database import create_tables, reset_database
import pages.basic_info as basic_info
import pages.po_issue as po_issue
import pages.dashboard as dashboard

# 페이지 설정
st.set_page_config(
    page_title="프로젝트 관리 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 적용
st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
        }
        .stTextInput>div>div>input {
            border-radius: 5px;
        }
        .stSelectbox>div>div>select {
            border-radius: 5px;
        }
        .stDateInput>div>div>input {
            border-radius: 5px;
        }
        .stNumberInput>div>div>input {
            border-radius: 5px;
        }
        div.block-container {
            padding-top: 2rem;
        }
        div.sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
        .big-font {
            font-size: 24px !important;
        }
        .medium-font {
            font-size: 18px !important;
        }
        .small-font {
            font-size: 14px !important;
        }
        .info-box {
            padding: 1rem;
            border-radius: 5px;
            background-color: #e8f4f9;
            border-left: 5px solid #2196f3;
            margin: 1rem 0;
        }
        .warning-box {
            padding: 1rem;
            border-radius: 5px;
            background-color: #fff3e0;
            border-left: 5px solid #ff9800;
            margin: 1rem 0;
        }
        .success-box {
            padding: 1rem;
            border-radius: 5px;
            background-color: #e8f5e9;
            border-left: 5px solid #4caf50;
            margin: 1rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.title("프로젝트 관리")
    
    # 메뉴 선택
    menu_options = {
        "대시보드": {"icon": "📊", "label": "대시보드"},
        "프로젝트 추가": {"icon": "➕", "label": "프로젝트 추가"},
        "PO 발행": {"icon": "📝", "label": "PO 발행"}
    }
    
    selected_page = st.radio(
        "메뉴 선택",
        list(menu_options.keys()),
        format_func=lambda x: f"{menu_options[x]['icon']} {menu_options[x]['label']}"
    )
    
    st.divider()
    
    # 새로고침 버튼
    if st.button("🔄 새로고침", use_container_width=True):
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
