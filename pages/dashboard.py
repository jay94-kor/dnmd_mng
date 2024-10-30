import streamlit as st
import pandas as pd
from database import get_connection
import plotly.express as px
import plotly.graph_objects as go

def format_currency(value):
    """숫자를 통화 형식으로 변환"""
    return f"₩{value:,.0f}"

def format_percentage(value):
    """숫자를 백분율 형식으로 변환"""
    return f"{value:.1%}"

def show_dashboard():
    st.markdown("<h1 class='big-font'>프로젝트 대시보드</h1>", unsafe_allow_html=True)

    # 용어 설명 추가
    with st.expander("💡 용어 설명"):
        st.markdown("""
            <div class="info-box">
                <ul>
                    <li><strong>PS (비용 대비 절감)</strong>: 프로젝트에서 절감된 비용</li>
                    <li><strong>PM (일반관리비+기업마진)</strong>: 프로젝트의 일반 관리비와 기업 마진의 합</li>
                    <li><strong>IC (내부 인건비)</strong>: 프로젝트에 투입된 내부 인건비</li>
                    <li><strong>PP (PS+PM)</strong>: 비용 대비 절감과 일반관리비 및 기업마진의 합</li>
                    <li><strong>IP (PS+PM+IC)</strong>: 비용 대비 절감, 일반관리비 및 기업마진, 내부 인건비의 총합</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    conn = get_connection()
    cursor = conn.cursor()

    # SQL 쿼리에 project_manager 추가
    cursor.execute('''
        SELECT 
            pi.project_id, pi.project_code, pi.project_name, pi.project_manager,
            pi.contract_amount, pi.supply_amount, pi.total_budget,
            COALESCE(SUM(po.supply_amount), 0) as used_supply_amount,
            COUNT(po.po_id) as po_count,
            COALESCE(SUM(po.total_amount), 0) as total_po_amount
        FROM project_info pi
        LEFT JOIN po_issue po ON pi.project_id = po.project_id
        GROUP BY 
            pi.project_id, pi.project_code, pi.project_name, pi.project_manager,
            pi.contract_amount, pi.supply_amount, pi.total_budget
    ''')
    
    projects = cursor.fetchall()
    
    # 데이터프레임 생성
    df = pd.DataFrame(projects, columns=[
        'project_id', 'project_code', 'project_name', 'project_manager',
        'contract_amount', 'supply_amount', 'total_budget', 'used_supply_amount',
        'po_count', 'total_po_amount'
    ])
    
    # Project Savings 계산 (총 예산 - 사용된 공급가액)
    df['project_savings'] = df['total_budget'] - df['used_supply_amount']
    
    # 사용률 계산 (사용된 공급가액 / 총 예산)
    df['usage_rate'] = (df['used_supply_amount'] / df['total_budget'])
    
    # 요약 지표 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 프로젝트 수", len(df))
    
    with col2:
        total_contract = df['contract_amount'].sum()
        st.metric("총 계약액", format_currency(total_contract))
    
    with col3:
        total_savings = df['project_savings'].sum()
        total_budget = df['total_budget'].sum()
        
        # 0으로 나누는 것 방지
        if total_budget > 0:
            total_usage_rate = (df['used_supply_amount'].sum() / total_budget) * 100
        else:
            total_usage_rate = 0
            
        st.metric(
            "총 Project Savings",
            format_currency(total_savings),
            f"사용률: {total_usage_rate:.1f}%",
            delta_color="inverse"
        )
    
    with col4:
        # 0으로 나누는 것 방지
        if total_budget > 0:
            avg_profit_rate = (total_savings / total_budget) * 100
        else:
            avg_profit_rate = 0
            
        st.metric("평균 수익률", f"{avg_profit_rate:.1f}%")

    # 요약 지표 표시 이후
    st.divider()

    # 보기 방식 선택
    view_option = st.radio("보기 방식", ["요약 보기", "상세 보기", "차트 보기"], horizontal=True)

    # 프로젝트 검색
    search = st.text_input("프로젝트 검색", 
                          help="프로젝트 코드, 이름, 또는 담당자 이름으로 검색")
    if search:
        df = df[
            df['project_name'].str.contains(search, case=False) |
            df['project_code'].str.contains(search, case=False) |
            df['project_manager'].str.contains(search, case=False)
        ]

    if view_option == "요약 보기":
        # 프로젝트 카드 표시
        for _, row in df.iterrows():
            with st.expander(f"{row['project_name']} ({row['project_code']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("📊 기본 정보")
                    st.write(f"계약액: {format_currency(row['contract_amount'])}")
                    st.write(f"공급가액: {format_currency(row['supply_amount'])}")
                    st.write(f"PO 발행 건수: {row['po_count']}건")
                
                with col2:
                    st.write("💰 성과 지표")
                    project_savings = row['total_budget'] - row['used_supply_amount']
                    
                    # 0으로 나누는 것 방지
                    if row['total_budget'] > 0:
                        usage_rate = (row['used_supply_amount'] / row['total_budget']) * 100
                    else:
                        usage_rate = 0
                        
                    st.write(f"Project Savings: {format_currency(project_savings)}")
                    st.write(f"사용률: {usage_rate:.1f}%")
                    st.write(f"발행된 PO: {format_currency(row['total_po_amount'])}")

    elif view_option == "상세 보기":
        display_df = df[[
            'project_code', 'project_name', 'contract_amount', 'total_budget',
            'used_supply_amount', 'po_count'
        ]].copy()
        
        # Project Savings 계산 및 추가
        display_df['project_savings'] = display_df['total_budget'] - display_df['used_supply_amount']
        
        # 0으로 나누는 것 방지
        display_df['usage_rate'] = 0.0  # 기본값 설정
        mask = display_df['total_budget'] > 0
        display_df.loc[mask, 'usage_rate'] = (
            display_df.loc[mask, 'used_supply_amount'] / 
            display_df.loc[mask, 'total_budget']
        ).astype(float) * 100
        
        # 컬럼 이름 한글화
        display_df.columns = [
            '프로젝트 코드', '프로젝트명', '계약액', '총 예산',
            '사용된 공급가액', 'PO 건수', 'Project Savings', '사용률(%)'
        ]
        
        # 금액 포맷팅
        for col in ['계약액', '총 예산', '사용된 공급가액', 'Project Savings']:
            display_df[col] = display_df[col].apply(format_currency)
        
        # 사용률 포맷팅
        display_df['사용률(%)'] = display_df['사용률(%)'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    else:  # 차트 보기
        # 수익률 차트
        fig_savings = px.bar(
            df,
            x='project_name',
            y='project_savings',
            title='프로젝트별 Project Savings',
            labels={'project_name': '프로젝트', 'project_savings': 'Project Savings'},
            text=df['project_savings'].apply(lambda x: format_currency(x))
        )
        fig_savings.update_traces(textposition='outside')
        st.plotly_chart(fig_savings, use_container_width=True)

        # 금액 비교 차트
        fig_amounts = go.Figure()
        fig_amounts.add_trace(go.Bar(
            name='계약액',
            x=df['project_name'],
            y=df['contract_amount'],
            text=df['contract_amount'].apply(format_currency)
        ))
        fig_amounts.add_trace(go.Bar(
            name='Project Savings',
            x=df['project_name'],
            y=df['project_savings'],
            text=df['project_savings'].apply(format_currency)
        ))
        fig_amounts.update_layout(
            title='프로젝트별 계약액 및 Project Savings',
            barmode='group'
        )
        st.plotly_chart(fig_amounts, use_container_width=True)

    conn.close()