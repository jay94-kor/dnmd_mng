import streamlit as st
from database import get_connection
from auth import log_edit
from utils import calculate_budget

def edit_project(project_id: int, user: dict):
    """프로젝트 수정 기능"""
    if not user['is_admin']:
        st.error("관리자만 프로젝트를 수정할 수 있습니다.")
        return
    
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
            # 변경된 필드 확인 및 기록
            if new_name != project[2]:
                log_edit('project', project_id, 'project_name', project[2], new_name, 'UPDATE')
            if new_manager != project[3]:
                log_edit('project', project_id, 'project_manager', project[3], new_manager, 'UPDATE')
            if new_contract_amount != project[4]:
                log_edit('project', project_id, 'contract_amount', str(project[4]), str(new_contract_amount), 'UPDATE')
            if new_advance_rate != project[7]:
                log_edit('project', project_id, 'advance_rate', str(project[7]), str(new_advance_rate), 'UPDATE')
            
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
        
        # 수정 이력 표시
        st.write("### 수정 이력")
        cursor.execute("""
            SELECT h.edit_time, u.full_name, h.field_name, h.old_value, h.new_value
            FROM project_edit_history h
            JOIN users u ON h.user_id = u.user_id
            WHERE h.project_id = %s
            ORDER BY h.edit_time DESC
        """, (project_id,))
        
        history = cursor.fetchall()
        if history:
            for edit in history:
                st.write(f"""
                {edit[0].strftime('%Y-%m-%d %H:%M:%S')} - {edit[1]}
                - {edit[2]}: {edit[3]} → {edit[4]}
                """)
        else:
            st.info("아직 수정 이력이 없습니다.")
    
    finally:
        conn.close()