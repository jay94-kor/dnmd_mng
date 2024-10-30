import sqlite3
from datetime import datetime
import os

DB_PATH = "project_management.db"

def get_connection():
    """SQLite 데이터베이스 연결 생성"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하도록 설정
    return conn

def create_tables():
    """데이터베이스 테이블 생성"""
    conn = get_connection()
    cursor = conn.cursor()

    # 프로젝트 기본정보 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_info (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT NOT NULL UNIQUE,
            project_name TEXT NOT NULL,
            project_manager TEXT NOT NULL,
            contract_amount INTEGER NOT NULL,
            supply_amount INTEGER NOT NULL,
            tax_amount INTEGER NOT NULL,
            advance_rate REAL NOT NULL,
            balance_rate REAL NOT NULL,
            contract_start_date DATE NOT NULL,
            contract_end_date DATE NOT NULL,
            company_margin_rate REAL NOT NULL,
            management_fee_rate REAL NOT NULL,
            min_internal_labor_rate REAL NOT NULL,
            min_internal_labor INTEGER NOT NULL,
            advance_budget INTEGER NOT NULL,
            balance_budget INTEGER NOT NULL,
            total_budget INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # PO 발행 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS po_issue (
            po_id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT NOT NULL UNIQUE,
            project_id INTEGER NOT NULL,
            supplier_name TEXT NOT NULL,
            description TEXT NOT NULL,
            detailed_memo TEXT,
            total_amount INTEGER NOT NULL,
            supply_amount INTEGER NOT NULL,
            tax_or_withholding INTEGER NOT NULL,
            advance_rate REAL NOT NULL,
            balance_rate REAL NOT NULL,
            advance_amount INTEGER NOT NULL,
            balance_amount INTEGER NOT NULL,
            category TEXT NOT NULL,
            contract_file BLOB NOT NULL,
            contract_filename TEXT NOT NULL,
            estimate_file BLOB NOT NULL,
            estimate_filename TEXT NOT NULL,
            business_cert_file BLOB NOT NULL,
            business_cert_filename TEXT NOT NULL,
            bank_file BLOB NOT NULL,
            bank_filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES project_info(project_id)
        );
    ''')

    # 프로젝트 운영 성적 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_performance (
            performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            project_savings INTEGER NOT NULL,
            project_savings_rate REAL NOT NULL,
            project_profit INTEGER NOT NULL,
            project_profit_rate REAL NOT NULL,
            internal_profit INTEGER NOT NULL,
            internal_profit_rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES project_info(project_id)
        );
    ''')

    conn.commit()
    cursor.close()
    conn.close()

def reset_database():
    """데이터베이스 초기화"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    create_tables()