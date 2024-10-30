import streamlit as st
from database import get_connection
from utils import calculate_budget, calculate_project_performance
import pandas as pd
from datetime import datetime

def basic_info():
    # 처음 페이지 진입시 주의사항 팝업
    if 'showed_warning' not in st.session_state:
        st.markdown("""
            <div class="warning-box">
                <h3>⚠️ 프로젝트 정보 입력 시 주의사항</h3>
                <ol>
                    <li>모든 정보는 신중하게 입력해주세요. 한번 등록된 정보는 수정이 어렵습니다.</li>
                    <li>계약금액은 부가세가 포함된 금액을 입력해주세요.</li>
                    <li>프로젝트 코드는 고유한 값이어야 합니다.</li>
                    <li>선금 비율 설정 시 계약서의 내용과 일치하는지 확인해주세요.</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("확인", type="primary", use_container_width=True):
            st.session_state.showed_warning = True
            st.rerun()
        return

    st.markdown("<h1 class='big-font'>프로젝트 기본정보 입력</h1>", unsafe_allow_html=True)
    
    # 입력 폼을 카드 형태로 표시
    st.markdown("""
        <div style="padding: 1rem; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 2rem;">
    """, unsafe_allow_html=True)
    
    # 2단 레이아웃
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("필수 입력 정보")
        project_code = st.text_input("프로젝트 코드", 
                                   help="고유한 프로젝트 코드를 입력하세요 (예: 0010-2401)")
        
        project_name = st.text_input("프로젝트 이름", 
                                   help="프로젝트의 공식 명칭을 입력하세요")
        
        project_manager = st.text_input("담당자 이름",
                                      help="프로젝트 담당자의 이름을 입력하세요")
        
        contract_amount = st.number_input("프로젝트 수주액", 
                                        min_value=0, 
                                        step=1000000, 
                                        format="%d",
                                        help="부가세 포함 금액을 입력하세요")
        
        advance_rate = st.slider(
            "선금 비율", 
            min_value=0, 
            max_value=100, 
            value=50,  # 기본값 50%로 변경
            help="계약금 비율을 설정하세요 (%)"
        ) / 100  # 백분율을 소수점으로 변환
    
    with col2:
        st.subheader("계약 기간")
        contract_start_date = st.date_input("계약 시작일",
                                          min_value=datetime(2020, 1, 1),
                                          help="프로젝트 시작일을 선택하세요")
        
        contract_end_date = st.date_input("계약 마감일",
                                         min_value=contract_start_date,
                                         help="프로젝트 종료일을 선택하세요")

    # 유효성 검사
    if contract_start_date >= contract_end_date:
        st.error("계약 종료일은 시작일보다 늦어야 합니다.")
        return

    # 예산 계산
    if contract_amount > 0:
        budget = calculate_budget(contract_amount, advance_rate, contract_start_date, contract_end_date)
        
        # 결과를 데이터프레임으로 표시
        st.subheader("자동 계산 결과")
        
        # 금액 정보
        amount_data = {
            '구분': ['공급가액', '부가세', '계약금액'],
            '금액': [
                format(budget['supply_amount'], ',d'),
                format(budget['tax_amount'], ',d'),
                format(contract_amount, ',d')
            ]
        }
        st.table(pd.DataFrame(amount_data))
        
        # 비율 정보
        rate_data = {
            '구분': ['선금 비율', '잔금 비율', '기업 마진율', '일반관리비율', '최소 내부 인건비율'],
            '비율': [
                f"{advance_rate:.1%}",
                f"{budget['balance_rate']:.1%}",
                f"{budget['company_margin_rate']:.1%}",
                f"{budget['management_fee_rate']:.1%}",
                f"{budget['min_internal_labor_rate']:.1%}"
            ]
        }
        st.table(pd.DataFrame(rate_data))
        
        # 예산 정보
        budget_data = {
            '구분': ['최소 내부 인건비', '선금 예산', '잔금 예산', '총 예산'],
            '금액': [
                format(budget['min_internal_labor'], ',d'),
                format(budget['advance_budget'], ',d'),
                format(budget['balance_budget'], ',d'),
                format(budget['total_budget'], ',d')
            ]
        }
        st.table(pd.DataFrame(budget_data))

        # 저장 버튼
        if st.button("프로젝트 정보 저장", type="primary"):
            if not project_manager:
                st.error("담당자 이름을 입력해주세요.")
                return
            
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                # 프로젝트 정보 저장
                cursor.execute('''
                    INSERT INTO project_info (
                        project_code, project_name, project_manager, contract_amount, supply_amount,
                        tax_amount, advance_rate, balance_rate, contract_start_date,
                        contract_end_date, company_margin_rate, management_fee_rate,
                        min_internal_labor_rate, min_internal_labor, advance_budget,
                        balance_budget, total_budget
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                ''', (
                    project_code, project_name, project_manager, contract_amount, budget['supply_amount'],
                    budget['tax_amount'], advance_rate, budget['balance_rate'],
                    contract_start_date, contract_end_date, budget['company_margin_rate'],
                    budget['management_fee_rate'], budget['min_internal_labor_rate'],
                    budget['min_internal_labor'], budget['advance_budget'],
                    budget['balance_budget'], budget['total_budget']
                ))
                
                conn.commit()
                
                # 프로젝트 ID 가져오기
                cursor.execute("SELECT LAST_INSERT_ID()")
                project_id = cursor.fetchone()[0]
                
                # 초기 성과 계산
                calculate_project_performance(project_id)
                
                st.success(f"프로젝트 '{project_name}'이(가) 성공적으로 저장되었습니다.")
                
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {str(e)}")
                
            finally:
                conn.close()

    # 입력 필드 가이드
    with st.expander("입력 가이드"):
        st.markdown("""
        ### 입력 필드 설명
        1. **프로젝트 코드**: 고유한 프로젝트 식별자 (예: PRJ2024001)
        2. **프로젝트 이름**: 공식 프로젝트명
        3. **수주액**: 부가세 포함 총 계약금액
        4. **선금 비율**: 계약금 비율 (예: 0.3 = 30%)
        5. **계약 기간**: 프로젝트 시작일과 종료일
        
        ### 자동 계산 항목
        - 공급가액: 수주액 ÷ 1.1
        - 부가세: 수주액 - 공급가액
        - 최소 내부 인건비율: max(5%, 계약기간 × 0.075%)
        - 예산: 공급가액 - (마진 + 관리비 + 내부인건비)
        """)