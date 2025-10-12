from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
import pandas as pd
import logging

from scripts.config import DATABASE_URL

logger = logging.getLogger(__name__)

# 엔진은 애플리케이션 전체에서 한 번만 생성하는 것이 효율적입니다.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

def get_engine() -> Engine:
    """SQLAlchemy 엔진 인스턴스를 반환합니다."""
    return engine

def is_table_empty(conn: Connection, table_name: str) -> bool:
    """Checks if a table is empty."""
    query = text(f"SELECT 1 FROM {table_name} LIMIT 1;")
    result = conn.execute(query)
    return result.first() is None

def check_match_exists(engine: Engine, match_ids: list[int]) -> set[int]:
    """DB에 이미 존재하는 매치 ID들을 한번에 조회하여 set으로 반환합니다."""
    if not match_ids:
        return set()
    
    with engine.connect() as conn:
        # IN 절을 사용하여 한번의 쿼리로 모든 ID를 확인
        stmt = text("SELECT match_id FROM match_info WHERE match_id IN :ids")
        result = conn.execute(stmt, {"ids": tuple(match_ids)})
        return {row[0] for row in result}

def save_dataframes_to_db(engine: Engine, parsed_data: dict[str, pd.DataFrame]):
    """
    파싱된 데이터프레임 딕셔너리를 DB의 각 테이블에 저장합니다.
    DataFrame.to_sql을 사용하여 효율적인 Bulk Insert를 수행합니다.
    """
    with engine.connect() as conn:
        with conn.begin(): # 트랜잭션 시작
            try:
                for table_name, df in parsed_data.items():
                    if not df.empty:
                        logger.info(f"Inserting {len(df)} rows into '{table_name}'")
                        df.to_sql(
                            name=table_name,
                            con=conn,
                            if_exists='append', # 기존 데이터에 추가
                            index=False,
                            chunksize=1000 # 대용량 데이터를 위해 chunk 단위로 삽입
                        )
            except Exception as e:
                logger.error(f"Failed to save data to DB: {e}")
                # 트랜잭션이 자동으로 롤백됩니다.
                raise

def execute_sql_file(engine: Engine, file_path: str):
    """SQL 파일을 읽어 실행합니다 (init_db용)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
    
    with engine.connect() as conn:
        with conn.begin():
            for stmt in statements:
                conn.execute(text(stmt))
    logger.info(f"Successfully executed SQL script: {file_path}")