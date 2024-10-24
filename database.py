import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="project_management"
    )
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 사용자 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
    ''')

    # 프로젝트 기본정보 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_info (
            project_id INT AUTO_INCREMENT PRIMARY KEY,
            project_code VARCHAR(100) NOT NULL UNIQUE,
            project_name VARCHAR(255) NOT NULL,
            project_manager VARCHAR(50) NOT NULL,  -- 담당자 필드 추가
            contract_amount BIGINT NOT NULL,
            supply_amount BIGINT NOT NULL,
            tax_amount BIGINT NOT NULL,
            advance_rate FLOAT NOT NULL,
            balance_rate FLOAT NOT NULL,
            contract_start_date DATE NOT NULL,
            contract_end_date DATE NOT NULL,
            company_margin_rate FLOAT DEFAULT 0.1,
            management_fee_rate FLOAT DEFAULT 0.08,
            min_internal_labor_rate FLOAT NOT NULL,
            min_internal_labor BIGINT NOT NULL,
            advance_budget BIGINT NOT NULL,
            balance_budget BIGINT NOT NULL,
            total_budget BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        );
    ''')

    # PO 발행 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS po_issue (
            po_id INT AUTO_INCREMENT PRIMARY KEY,
            po_number VARCHAR(100) NOT NULL UNIQUE,
            project_id INT NOT NULL,
            supplier_name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,  -- 적요 필드 추가
            detailed_memo TEXT,  -- 상세메모 필드 추가
            total_amount BIGINT NOT NULL,
            supply_amount BIGINT NOT NULL,
            tax_or_withholding BIGINT NOT NULL,
            advance_rate FLOAT NOT NULL,
            balance_rate FLOAT NOT NULL,
            advance_amount BIGINT NOT NULL,
            balance_amount BIGINT NOT NULL,
            category VARCHAR(100) NOT NULL,
            contract_file LONGBLOB NOT NULL,  -- 계약 파일 필드 추가
            contract_filename VARCHAR(255) NOT NULL,  -- 계약 파일명 필드 추가
            estimate_file LONGBLOB NOT NULL,  -- 견적 파일 필드 추가
            estimate_filename VARCHAR(255) NOT NULL,  -- 견적 파일명 필드 추가
            business_cert_file LONGBLOB NOT NULL,  -- 사업자 등록증 파일 필드 추가
            business_cert_filename VARCHAR(255) NOT NULL,  -- 사업자 등록증 파일명 필드 추가
            bank_file LONGBLOB NOT NULL,  -- 통장 사본 파일 필드 추가
            bank_filename VARCHAR(255) NOT NULL,  -- 통장 사본 파일명 필드 추가
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES project_info(project_id)
        );
    ''')

    # 프로젝트 운영 성적 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_performance (
            performance_id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            project_savings BIGINT NOT NULL,
            project_savings_rate FLOAT NOT NULL,
            project_profit BIGINT NOT NULL,
            project_profit_rate FLOAT NOT NULL,
            internal_profit BIGINT NOT NULL,
            internal_profit_rate FLOAT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES project_info(project_id)
        );
    ''')

    # 수정 이력 테이블 (프로젝트) 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_edit_history (
            history_id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            user_id INT NOT NULL,
            edit_type ENUM('CREATE', 'UPDATE', 'DELETE') NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            old_value TEXT,
            new_value TEXT,
            edit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES project_info(project_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    ''')

    # 수정 이력 테이블 (PO) 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS po_edit_history (
            history_id INT AUTO_INCREMENT PRIMARY KEY,
            po_id INT NOT NULL,
            user_id INT NOT NULL,
            edit_type ENUM('CREATE', 'UPDATE', 'DELETE') NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            old_value TEXT,
            new_value TEXT,
            edit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (po_id) REFERENCES po_issue(po_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    ''')

    # 세션 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id VARCHAR(100) PRIMARY KEY,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    ''')

    conn.commit()
    cursor.close()
    conn.close()

def reset_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DROP TABLE IF EXISTS project_performance")
    cursor.execute("DROP TABLE IF EXISTS po_issue")
    cursor.execute("DROP TABLE IF EXISTS project_info")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    create_tables()
    
    conn.commit()
    conn.close()