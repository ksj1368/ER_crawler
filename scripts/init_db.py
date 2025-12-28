from sqlalchemy import create_engine, text
from scripts.config import DATABASE_URL, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from scripts.models import Base

def init_db():
    """데이터베이스를 초기화하고 테이블을 생성하는 함수"""
    root_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
    root_engine = create_engine(root_url)
    
    with root_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME}"))
        conn.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        print(f"Database '{DB_NAME}' dropped and recreated.")

    # 2. SQLAlchemy로 생성한 스키마 기반 DB 테이블 생성
    db_engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(db_engine)
    print("Tables created based on models.py successfully.")

if __name__ == "__main__":
    init_db()