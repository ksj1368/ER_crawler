from sqlalchemy import create_engine, text
from scripts.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, SCHEMA_PATH, DB_NAME
from scripts.db_utils import execute_sql_file

def init_db():
    # 데이터베이스가 없는 상태에서 연결하기 위해 DB_NAME을 제외하고 URL 생성
    temp_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
    engine = create_engine(temp_url, connect_args={'charset': 'utf8mb4'})
    
    with engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {DB_NAME};"))
        conn.execute(text(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
        conn.execute(text(f"USE {DB_NAME};"))

    # DB가 생성된 후 DB_NAME에 연결하는 새 엔진
    db_engine = create_engine(f"{temp_url}/{DB_NAME}")
    execute_sql_file(db_engine, SCHEMA_PATH)
    print(f"Database '{DB_NAME}' initialized successfully.")

if __name__ == "__main__":
    init_db()