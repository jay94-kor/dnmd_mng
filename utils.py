from database import get_connection
from decimal import Decimal, ROUND_HALF_UP

def calculate_budget(contract_amount, advance_rate, contract_start_date, contract_end_date):
    """
    예산 계산 함수 - 엑셀 수식과 동일하게 구현
    contract_amount: 계약 총액 (부가세 포함)
    advance_rate: 선금 비율 (0.0 ~ 1.0)
    """
    try:
        # 공급가액, 부가세 계산
        supply_amount = int(Decimal(str(contract_amount)) / Decimal('1.1'))
        tax_amount = contract_amount - supply_amount
        balance_rate = Decimal('1.0') - Decimal(str(advance_rate))
        
        # 고정 비율
        company_margin_rate = Decimal('0.1')  # 10%
        management_fee_rate = Decimal('0.08')  # 8%
        
        # 최소 내부 인건비율 계산
        days_between = (contract_end_date - contract_start_date).days
        min_internal_labor_rate = max(Decimal('0.05'), Decimal(str(days_between)) * Decimal('0.00075'))
        
        # 최소 내부인건비
        min_internal_labor = int(Decimal(str(contract_amount)) * min_internal_labor_rate)
        
        # 예산 계산
        advance_budget = int(
            supply_amount * Decimal(str(advance_rate)) - 
            (supply_amount * Decimal(str(advance_rate)) * 
             (company_margin_rate + management_fee_rate + min_internal_labor_rate))
        )
        
        balance_budget = int(
            supply_amount * balance_rate - 
            (supply_amount * balance_rate * 
             (company_margin_rate + management_fee_rate + min_internal_labor_rate))
        )
        
        total_budget = int(
            supply_amount - 
            (supply_amount * (company_margin_rate + management_fee_rate + min_internal_labor_rate))
        )
        
        return {
            "supply_amount": supply_amount,
            "tax_amount": tax_amount,
            "balance_rate": float(balance_rate),
            "company_margin_rate": float(company_margin_rate),
            "management_fee_rate": float(management_fee_rate),
            "min_internal_labor_rate": float(min_internal_labor_rate),
            "min_internal_labor": min_internal_labor,
            "advance_budget": advance_budget,
            "balance_budget": balance_budget,
            "total_budget": total_budget
        }
    except Exception as e:
        raise Exception(f"예산 계산 중 오류 발생: {str(e)}")

def calculate_po_amounts(total_amount, advance_rate, category):
    """
    PO 금액 계산 함수
    total_amount: PO 총액
    advance_rate: 선금 비율 (0 ~ 100)
    category: 거래 분류 ("부가세 10%", "원천세 3.3%", "강사 인건비 8.8%")
    """
    try:
        # 선금 비율을 소수점으로 변환 (50% -> 0.5)
        advance_rate = Decimal(str(advance_rate)) / Decimal('100')
        balance_rate = Decimal('1.0') - advance_rate
        
        if category == "부가세 10%":
            supply_amount = int(Decimal(str(total_amount)) / Decimal('1.1'))
            tax_or_withholding = total_amount - supply_amount
        elif category == "원천세 3.3%":
            tax_or_withholding = int(Decimal(str(total_amount)) * Decimal('0.033'))
            supply_amount = total_amount - tax_or_withholding
        elif category == "강사 인건비 8.8%":
            tax_or_withholding = int(Decimal(str(total_amount)) * Decimal('0.088'))
            supply_amount = total_amount - tax_or_withholding
        else:
            raise ValueError("잘못된 거래 분류입니다.")

        advance_amount = int(Decimal(str(supply_amount)) * advance_rate)
        balance_amount = supply_amount - advance_amount

        return {
            "supply_amount": supply_amount,
            "tax_or_withholding": tax_or_withholding,
            "advance_amount": advance_amount,
            "balance_rate": float(balance_rate * 100),  # 퍼센트로 변환
            "balance_amount": balance_amount
        }
    except Exception as e:
        raise Exception(f"PO 금액 계산 중 오류 발생: {str(e)}")

def calculate_project_performance(project_id):
    """
    프로젝트 성과 계산 함수
    
    Project Savings (잔여 예산) = 총 예산 - PO 공급가액 합계
    Project Profit = Project Savings + 기업이윤 + 일반관리비
    Internal Profit = Project Profit + 내부인건비 총액
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 프로젝트 정보와 사용된 예산 가져오기
        cursor.execute('''
            SELECT 
                pi.contract_amount,
                pi.supply_amount,
                pi.company_margin_rate,
                pi.management_fee_rate,
                pi.min_internal_labor_rate,
                pi.total_budget,
                COALESCE(SUM(po.supply_amount), 0) as used_supply_amount,
                pi.min_internal_labor
            FROM project_info pi
            LEFT JOIN po_issue po ON pi.project_id = po.project_id
            WHERE pi.project_id = %s
            GROUP BY 
                pi.project_id, pi.contract_amount, pi.supply_amount, pi.company_margin_rate,
                pi.management_fee_rate, pi.min_internal_labor_rate,
                pi.total_budget, pi.min_internal_labor
        ''', (project_id,))
        
        project_data = cursor.fetchone()
        
        contract_amount = Decimal(str(project_data[0]))
        supply_amount = Decimal(str(project_data[1]))
        company_margin_rate = Decimal(str(project_data[2]))
        management_fee_rate = Decimal(str(project_data[3]))
        min_internal_labor_rate = Decimal(str(project_data[4]))
        total_budget = Decimal(str(project_data[5]))
        used_supply_amount = Decimal(str(project_data[6]))
        min_internal_labor = Decimal(str(project_data[7]))

        # Project Savings (잔여 예산) 계산
        project_savings = total_budget - used_supply_amount
        project_savings_rate = project_savings / total_budget if total_budget else Decimal('0')

        # 기업이윤과 일반관리비 계산
        company_margin = supply_amount * company_margin_rate
        management_fee = supply_amount * management_fee_rate

        # Project Profit 계산
        project_profit = project_savings + company_margin + management_fee
        project_profit_rate = project_profit / contract_amount if contract_amount else Decimal('0')

        # Internal Profit 계산
        internal_profit = project_profit + min_internal_labor
        internal_profit_rate = internal_profit / contract_amount if contract_amount else Decimal('0')

        # 성과 저장
        cursor.execute('''
            INSERT INTO project_performance 
            (project_id, project_savings, project_savings_rate, 
             project_profit, project_profit_rate, 
             internal_profit, internal_profit_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            project_savings = VALUES(project_savings),
            project_savings_rate = VALUES(project_savings_rate),
            project_profit = VALUES(project_profit),
            project_profit_rate = VALUES(project_profit_rate),
            internal_profit = VALUES(internal_profit),
            internal_profit_rate = VALUES(internal_profit_rate)
        ''', (
            project_id,
            int(project_savings),
            float(project_savings_rate),
            int(project_profit),
            float(project_profit_rate),
            int(internal_profit),
            float(internal_profit_rate)
        ))

        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"프로젝트 성과 계산 중 오류 발생: {str(e)}")
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()