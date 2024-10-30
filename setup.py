from database import create_tables

def setup_database():
    try:
        # 테이블 생성
        create_tables()
        print("데이터베이스 설정이 완료되었습니다.")
        print("이제 'streamlit run app.py'를 실행하여 애플리케이션을 시작할 수 있습니다.")

    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    setup_database()