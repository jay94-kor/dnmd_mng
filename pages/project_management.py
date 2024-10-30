import streamlit as st
from database import get_connection
from utils import calculate_budget

def edit_project(project_id: int):
    """프로젝트 수정 기능"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 프로젝트 정보 가져오기
        cursor.execute("""
            SELECT * FROM project_info WHERE project_id = %s
        """, (project_id,))
        project = cursor.fetchone()
        
        if not project:
            st.error("프로젝트를 찾을 수 없습니다.")
            return
        
        st.write("### 프로젝트 정보 수정")
        
        # 수정 가능한 필드들
        new_name = st.text_input("프로젝트명", value=project[2])
        new_manager = st.text_input("담당자", value=project[3])
        new_contract_amount = st.number_input(
            "계약금액",
            value=float(project[4]),
            step=1000000.0
        )
        new_advance_rate = st.slider(
            "선금 비율",
            min_value=0,
            max_value=100,
            value=int(project[7] * 100)
        ) / 100.0
        
        if st.button("수정 사항 저장", type="primary"):
            # 새로운 예산 계산
            budget = calculate_budget(new_contract_amount, new_advance_rate, project[8], project[9])
            
            # 프로젝트 정보 업데이트
            cursor.execute("""
                UPDATE project_info SET
                project_name = %s,
                project_manager = %s,
                contract_amount = %s,
                supply_amount = %s,
                tax_amount = %s,
                advance_rate = %s,
                balance_rate = %s,
                advance_budget = %s,
                balance_budget = %s,
                total_budget = %s
                WHERE project_id = %s
            """, (
                new_name, new_manager, new_contract_amount,
                budget['supply_amount'], budget['tax_amount'],
                new_advance_rate, budget['balance_rate'],
                budget['advance_budget'], budget['balance_budget'],
                budget['total_budget'], project_id
            ))
            
            conn.commit()
            st.success("프로젝트 정보가 수정되었습니다.")
            st.rerun()
    
    finally:
        conn.close()