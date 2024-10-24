import mysql.connector
from database import create_tables

def setup_database():
    try:
        # Root 계정으로 연결
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()

        # 데이터베이스 생성
        cursor.execute("CREATE DATABASE IF NOT EXISTS project_management")
        print("데이터베이스 생성 완료")

        # 연결 종료
        cursor.close()
        conn.close()

        # 테이블 생성
        create_tables()
        print("테이블 생성 완료")

        print("데이터베이스 설정이 완료되었습니다.")
        print("이제 'streamlit run app.py'를 실행하여 애플리케이션을 시작할 수 있습니다.")

    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")
        print("\n데이터베이스 설정 체크리스트:")
        print("1. MySQL이 실행 중인지 확인")
        print("2. Root 계정 비밀번호가 올바른지 확인")
        print("3. MySQL 서버에 접근 권한이 있는지 확인")

if __name__ == "__main__":
    setup_database()