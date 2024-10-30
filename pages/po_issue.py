import streamlit as st
import pandas as pd
from database import get_connection
from utils import calculate_po_amounts, calculate_project_performance

def format_currency(value):
    """숫자를 통화 형식으로 변환"""
    return f"₩{value:,.0f}"

def format_percentage(value):
    """숫자를 백분율 형식으로 변환"""
    return f"{value:.1%}"

def load_project_budget(project_id):
    """프로젝트 예산 정보 로드"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            pi.project_name,
            pi.advance_budget,
            pi.balance_budget,
            pi.total_budget,
            COALESCE(SUM(po.advance_amount), 0) as used_advance,
            COALESCE(SUM(po.balance_amount), 0) as used_balance
        FROM project_info pi
        LEFT JOIN po_issue po ON pi.project_id = po.project_id
        WHERE pi.project_id = %s
        GROUP BY pi.project_id, pi.project_name, pi.advance_budget, pi.balance_budget, pi.total_budget
    """, (project_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result

def generate_po_number(project_id, cursor):
    """
    프로젝트별 다음 PO 번호 생성
    예: 0010-2401-001, 0010-2401-002, ...
    """
    # 프로젝트 코드 가져오기
    cursor.execute("SELECT project_code FROM project_info WHERE project_id = %s", (project_id,))
    project_code = cursor.fetchone()[0]
    
    # 해당 프로젝트의 마지막 PO 번호 확인
    cursor.execute("""
        SELECT po_number 
        FROM po_issue 
        WHERE project_id = %s 
        ORDER BY po_number DESC 
        LIMIT 1
    """, (project_id,))
    
    last_po = cursor.fetchone()
    
    if last_po:
        # 마지막 PO 번호에서 순번 추출하여 1 증가
        last_sequence = int(last_po[0].split('-')[-1])
        new_sequence = last_sequence + 1
    else:
        # 첫 PO인 경우 1부터 시작
        new_sequence = 1
    
    # 새 PO 번호 생성 (예: PRJ2024001-001)
    new_po_number = f"{project_code}-{new_sequence:03d}"
    return new_po_number

def po_issue():
    if 'showed_po_warning' not in st.session_state:
        st.markdown("""
            <div class="warning-box">
                <h3>⚠️ PO 발행 시 주의사항</h3>
                <ol>
                    <li>모든 정보는 신중하게 입력해주세요. 한번 발행된 PO는 수정이 어렵습니다.</li>
                    <li>금액은 부가세가 별도로 계산됩니다.</li>
                    <li>적요는 최소 10글자 이상 상세하게 작성해주세요. (띄어쓰기 제외)</li>
                    <li>계약서와 견적서는 필수 첨부사항입니다.</li>
                    <li>견적서는 상세하게 작성되어야 하며, 미흡할 경우 반려될 수 있습니다.</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("확인", type="primary", use_container_width=True):
            st.session_state.showed_po_warning = True
            st.rerun()
        return

    st.title("PO 발행 관리")

    # 세션 상태 초기화
    if 'last_po_time' not in st.session_state:
        st.session_state.last_po_time = None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 프로젝트 목록 가져오기
        cursor.execute("""
            SELECT 
                pi.project_id,
                pi.project_name,
                pi.advance_budget,
                pi.balance_budget,
                pi.total_budget,
                COALESCE(SUM(po.advance_amount), 0) as used_advance,
                COALESCE(SUM(po.balance_amount), 0) as used_balance
            FROM project_info pi
            LEFT JOIN po_issue po ON pi.project_id = po.project_id
            GROUP BY pi.project_id
        """)
        projects = cursor.fetchall()

        if not projects:
            st.warning("등록된 프로젝트가 없습니다. 먼저 프로젝트를 등록해주세요.")
            return

        # 프로젝트 선택 후 자동으로 다음 PO 번호 생성
        project_dict = {
            proj[1]: proj[0]  # 잔여예산 표시 제거
            for proj in projects  # 'proj' 변수를 정의하는 부분 추가
        }
        selected_project_name = st.selectbox(
            "프로젝트 선택",
            list(project_dict.keys()),
            help="프로젝트를 선택하면 PO 번호가 자동으로 생성됩니다"
        )
        project_id = project_dict[selected_project_name]
        
        # 자동 생성된 PO 번호 표시
        next_po_number = generate_po_number(project_id, cursor)
        st.info(f"📝 다음 PO 번호: {next_po_number}")

        # 선택된 프로젝트의 예산 정보 로드
        budget_info = load_project_budget(project_id)
        project_name = budget_info[0]
        advance_budget = budget_info[1]
        balance_budget = budget_info[2]
        total_budget = budget_info[3]
        used_advance = budget_info[4]
        used_balance = budget_info[5]

        # 예산 현황 표시
        st.subheader("실시간 예산 현황")
        
        budget_cols = st.columns(3)
        with budget_cols[0]:
            remain_advance = advance_budget - used_advance
            advance_percent = (used_advance / advance_budget * 100) if advance_budget > 0 else 0
            st.metric(
                "선금 예산",
                format_currency(remain_advance),
                f"사용률: {advance_percent:.1f}%",
                delta_color="inverse"
            )

        with budget_cols[1]:
            remain_balance = balance_budget - used_balance
            balance_percent = (used_balance / balance_budget * 100) if balance_budget > 0 else 0
            st.metric(
                "잔금 예산",
                format_currency(remain_balance),
                f"사용률: {balance_percent:.1f}%",
                delta_color="inverse"
            )

        with budget_cols[2]:
            total_remain = total_budget - (used_advance + used_balance)
            total_percent = ((used_advance + used_balance) / total_budget * 100) if total_budget > 0 else 0
            st.metric(
                "총 잔여 예산",
                format_currency(total_remain),
                f"사용률: {total_percent:.1f}%",
                delta_color="inverse"
            )

        st.divider()

        # PO 입력 폼
        st.subheader("신규 PO 발행")
        
        col1, col2 = st.columns(2)
        
        with col1:
            supplier_name = st.text_input(
                "거래처명",
                help="거래처의 정확한 상호명을 입력하세요"
            )
            total_amount = st.number_input(
                "총액",
                min_value=0,
                step=10000,
                help="계약 총액을 입력하세요"
            )
            
            # 적요 입력 (필수)
            description = st.text_area(
                "적요 (필수)", 
                help="발주 내용을 상세하게 작성해주세요. (최소 10글자, 띄어쓰기 제외)",
                max_chars=500
            )
        
        with col2:
            advance_rate = st.slider(
                "선금 비율",
                min_value=0,
                max_value=100,
                value=50,
                help="선금 비율을 설정하세요 (%)"
            )
            category = st.selectbox(
                "거래 분류",
                ["부가세 10%", "원천세 3.3%", "강사 인건비 8.8%"],
                help="적절한 거래 분류를 선택하세요"
            )
            
            # 상세메모 입력 (선택)
            detailed_memo = st.text_area(
                "상세메모 (선택)", 
                help="규격, 상세 사항 등을 자유롭게 입력하세요.",
                max_chars=1000
            )
        
        # 파일 업로드 섹션
        st.subheader("필수 첨부 파일")
        file_col1, file_col2 = st.columns(2)
        
        with file_col1:
            contract_file = st.file_uploader(
                "계약서 첨부 (필수)", 
                type=['pdf', 'doc', 'docx'],
                help="계약서를 PDF 또는 Word 형식으로 첨부해주세요."
            )
            estimate_file = st.file_uploader(
                "견적서 첨부 (필수)", 
                type=['pdf', 'doc', 'docx'],
                help="견적서를 PDF 또는 Word 형식으로 첨부해주세요."
            )
        
        with file_col2:
            business_cert_file = st.file_uploader(
                "사업자등록증 첨부 (필수)", 
                type=['pdf', 'jpg', 'jpeg', 'png'],
                help="사업자등록증을 PDF 또는 이미지 형식으로 첨부해주세요."
            )
            bank_file = st.file_uploader(
                "통장사본 첨부 (필수)", 
                type=['pdf', 'jpg', 'jpeg', 'png'],
                help="통장사본을 PDF 또는 이미지 형식으로 첨부해주세요."
            )
        
        # 입력값 검증
        input_valid = True
        input_errors = []
        
        if not supplier_name:
            input_valid = False
            input_errors.append("거래처명을 입력해주세요.")
        
        if total_amount <= 0:
            input_valid = False
            input_errors.append("총액을 입력해주세요.")
        
        # 적요 글자 수 검사 (띄어쓰기 제외)
        if not description:
            input_valid = False
            input_errors.append("적요를 입력해주세요.")
        else:
            desc_length = len(description.replace(" ", ""))
            if desc_length < 10:
                input_valid = False
                input_errors.append(f"적요는 최소 10글자 이상 작성해주세요. (현재 {desc_length}글자)")
        
        if not contract_file:
            input_valid = False
            input_errors.append("계약서를 첨부해주세요.")
        
        if not estimate_file:
            input_valid = False
            input_errors.append("견적서를 첨부해주세요.")
        
        if not business_cert_file:
            input_valid = False
            input_errors.append("사업자등록증을 첨부해주세요.")
        
        if not bank_file:
            input_valid = False
            input_errors.append("통장사본을 첨부해주세요.")
        
        # 에러 메시지 표시
        for error in input_errors:
            st.error(error)

        if input_valid and total_amount > 0:
            # PO 금액 계산
            po_amounts = calculate_po_amounts(total_amount, advance_rate / 100, category)
            
            st.subheader("자동 계산 결과")
            
            # 계산 결과를 테이블로 표시
            calc_data = {
                '구분': [
                    '공급가액 (예산 차감 금액)', 
                    f'{"부가세" if category=="부가세 10%" else "원천세"} (예산 미차감)', 
                    '선금 총액', 
                    '잔금 총액', 
                    '총액'
                ],
                '금액': [
                    format_currency(po_amounts['supply_amount']),
                    format_currency(po_amounts['tax_or_withholding']),
                    format_currency(po_amounts['advance_amount']),
                    format_currency(po_amounts['balance_amount']),
                    format_currency(total_amount)
                ]
            }
            st.table(pd.DataFrame(calc_data))
            
            # 예산 차감 설명 추가
            st.info("""
            ℹ️ 예산 차감 안내
            - 공급가액만 예산에서 차감됩니다.
            - 세금(부가세/원천세)은 예산에서 차감되지 않습니다.
            """)

            # 예산 영향 미리보기
            st.write("### 예산 영향 미리보기")
            new_advance_remain = remain_advance - po_amounts['advance_amount']
            new_balance_remain = remain_balance - po_amounts['balance_amount']
            new_total_remain = total_remain - (po_amounts['advance_amount'] + po_amounts['balance_amount'])
            
            # 예산 초과 체크
            total_exceeded = new_total_remain < 0
            advance_exceeded = new_advance_remain < 0
            balance_exceeded = new_balance_remain < 0
            
            # 컬러 코딩된 예산 잔액 표시
            st.write("예상 잔여 예산:")
            if not total_exceeded:
                if advance_exceeded:
                    st.markdown(f"- 선금 예산 잔액: 🔴 {format_currency(new_advance_remain)}")
                else:
                    st.markdown(f"- 선금 예산 잔액: 🟢 {format_currency(new_advance_remain)}")
                
                if balance_exceeded:
                    st.markdown(f"- 잔금 예산 잔액: 🔴 {format_currency(new_balance_remain)}")
                else:
                    st.markdown(f"- 잔금 예산 잔액: 🟢 {format_currency(new_balance_remain)}")
                
                st.markdown(f"- 총 예산 잔액: 🟢 {format_currency(new_total_remain)}")
            
            # 경고 메시지 표시
            if total_exceeded:
                st.error("""
                ⚠️ 전체 예산 초과!
                
                이 PO를 발행하면 전체 예산을 초과합니다.
                프로젝트 관리자와 상담이 필요합니다.
                """)
                can_issue = False
            elif advance_exceeded and balance_exceeded:
                st.error("""
                ⚠️ 선금과 잔금 예산 모두 초과!
                
                이 PO를 발행하면:
                - 선금 예산을 초과합니다.
                - 잔금 예산을 초과합니다.
                """)
                can_issue = False
            elif advance_exceeded:
                st.error("""
                ⚠️ 선금 예산 초과!
                
                이 PO를 발행하면 선금 예산을 초과합니다.
                선금 비율을 조정하거나 프로젝트 관리자와 상담하세요.
                """)
                can_issue = False
            elif balance_exceeded:
                st.error("""
                ⚠️ 잔금 예산 초과!
                
                이 PO를 발행하면 잔금 예산을 초과합니다.
                선금 비율을 조정하거나 프로젝트 관리자와 상담하세요.
                """)
                can_issue = False
            else:
                st.success("""
                ✅ 예산 확인 완료
                
                모든 예산이 충분합니다.
                PO를 발행할 수 있습니다.
                """)
                can_issue = True

            # PO 발행 버튼 섹션
            st.divider()
            button_col1, button_col2 = st.columns([1, 4])
            with button_col1:
                if can_issue:
                    if st.button("📝 PO 발행", type="primary", use_container_width=True):
                        try:
                            # 파일 데이터 읽기
                            contract_data = contract_file.read()
                            estimate_data = estimate_file.read()
                            business_cert_data = business_cert_file.read()
                            bank_data = bank_file.read()
                            
                            cursor.execute("""
                                INSERT INTO po_issue (
                                    po_number, project_id, supplier_name, description, detailed_memo,
                                    total_amount, supply_amount, tax_or_withholding, advance_rate,
                                    balance_rate, advance_amount, balance_amount, category,
                                    contract_file, contract_filename, 
                                    estimate_file, estimate_filename,
                                    business_cert_file, business_cert_filename,
                                    bank_file, bank_filename
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                    %s, %s, %s, %s, %s, %s, %s, %s
                                )
                            """, (
                                next_po_number, project_id, supplier_name, description, detailed_memo,
                                total_amount, po_amounts['supply_amount'], po_amounts['tax_or_withholding'],
                                advance_rate/100, po_amounts['balance_rate']/100, po_amounts['advance_amount'],
                                po_amounts['balance_amount'], category,
                                contract_data, contract_file.name,
                                estimate_data, estimate_file.name,
                                business_cert_data, business_cert_file.name,
                                bank_data, bank_file.name
                            ))
                            
                            conn.commit()
                            
                            # 프로젝트 성과 재계산
                            calculate_project_performance(project_id)
                            
                            st.session_state.last_po_time = pd.Timestamp.now()
                            st.success(f"PO번호 '{next_po_number}'가 성공적으로 발행되었습니다!")
                            
                            # 페이지 새로고침
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"PO 발행 중 오류가 발생했습니다: {str(e)}")
                            conn.rollback()
                else:
                    st.button("📝 PO 발행", disabled=True, use_container_width=True)
                    with button_col2:
                        st.error("예산 초과로 인해 PO 발행이 불가능합니다!")

        # 기존 PO 목록
        st.divider()
        st.subheader("발행된 PO 목록")
        
        cursor.execute("""
            SELECT 
                po_number, supplier_name, total_amount, 
                advance_rate, category, supply_amount, 
                tax_or_withholding, advance_amount, balance_amount,
                created_at, description, detailed_memo,
                contract_file, contract_filename,
                estimate_file, estimate_filename,
                business_cert_file, business_cert_filename,
                bank_file, bank_filename
            FROM po_issue
            WHERE project_id = %s
            ORDER BY created_at DESC
        """, (project_id,))
        
        po_list = cursor.fetchall()
        
        if po_list:
            for po in po_list:
                with st.expander(f"PO번호: {po[0]} | 거래처: {po[1]} | 발행일: {po[9].strftime('%Y-%m-%d %H:%M')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("💰 금액 정보")
                        st.write(f"총액: {format_currency(po[2])}")
                        st.write(f"공급가액: {format_currency(po[5])}")
                        st.write(f"세금: {format_currency(po[6])}")
                        st.write(f"선금: {format_currency(po[7])}")
                        st.write(f"잔금: {format_currency(po[8])}")
                        st.write(f"선금비율: {po[3]*100:.1f}%")
                        st.write(f"거래분류: {po[4]}")
                    
                    with col2:
                        st.write("📝 상세 정보")
                        st.write("적요:")
                        st.info(po[10])
                        if po[11]:  # detailed_memo가 있는 경우
                            st.write("상세메모:")
                            st.info(po[11])
                    
                    # 파일 다운로드 버튼들
                    st.write("📎 첨부파일 다운로드")
                    file_cols = st.columns(4)
                    
                    with file_cols[0]:
                        if po[12]:  # contract_file
                            st.download_button(
                                label="📄 계약서",
                                data=po[12],
                                file_name=po[13],
                                mime="application/octet-stream",
                                use_container_width=True
                            )
                    
                    with file_cols[1]:
                        if po[14]:  # estimate_file
                            st.download_button(
                                label="📑 견적서",
                                data=po[14],
                                file_name=po[15],
                                mime="application/octet-stream",
                                use_container_width=True
                            )
                    
                    with file_cols[2]:
                        if po[16]:  # business_cert_file
                            st.download_button(
                                label="🏢 사업자등록증",
                                data=po[16],
                                file_name=po[17],
                                mime="application/octet-stream",
                                use_container_width=True
                            )
                    
                    with file_cols[3]:
                        if po[18]:  # bank_file
                            st.download_button(
                                label="🏦 통장사본",
                                data=po[18],
                                file_name=po[19],
                                mime="application/octet-stream",
                                use_container_width=True
                            )
        else:
            st.info("아직 발행된 PO가 없습니다.")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
    
    finally:
        cursor.close()
        conn.close()
