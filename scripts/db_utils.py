from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
import pandas as pd
import logging
from typing import List, Dict, Any
from datetime import datetime

from scripts.config import DATABASE_URL

logger = logging.getLogger(__name__)

# 엔진은 애플리케이션 전체에서 한 번만 생성하는 것이 효율적입니다.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

def get_engine() -> Engine:
    """SQLAlchemy 엔진 인스턴스를 반환합니다."""
    return engine

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

def get_active_users(engine: Engine) -> List[Dict[str, Any]]:
    """is_active가 True인 모든 유저의 uid, nickname, last_match_id를 조회합니다."""
    with engine.connect() as conn:
        stmt = text("SELECT uid, nickname, last_match_id FROM user WHERE is_active = TRUE")
        result = conn.execute(stmt)
        return [{'uid': row[0], 'nickname': row[1], 'last_match_id': row[2]} for row in result]

def upsert_users(engine: Engine, users_data: List[Dict[str, str]]):
    """
    여러 유저 정보를 Upsert합니다.
    - DB에 없는 uid는 새로 추가합니다.
    - DB에 이미 있는 uid는 nickname과 last_updated_at을 갱신하고 is_active를 True로 설정합니다.
    """
    if not users_data:
        return

    stmt = text("""
        INSERT INTO user (uid, nickname, last_match_id, is_active, last_updated_at)
        VALUES (:uid, :nickname, 0, TRUE, :last_updated_at)
        ON DUPLICATE KEY UPDATE
        nickname = VALUES(nickname),
        is_active = TRUE,
        last_updated_at = VALUES(last_updated_at)
    """)
    
    now = datetime.utcnow()
    
    params = [
        {
            'uid': user['uid'],
            'nickname': user['nickname'],
            'last_updated_at': now
        }
        for user in users_data
    ]
    
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(stmt, params)
    logger.info(f"Upserted {len(users_data)} users.")
def deactivate_user(engine: Engine, uid: str):
    """특정 uid의 is_active를 False로 설정합니다."""
    stmt = text("""
        UPDATE user
        SET is_active = FALSE, last_updated_at = :last_updated_at
        WHERE uid = :uid
    """)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(stmt, {'uid': uid, 'last_updated_at': datetime.utcnow()})
    logger.warning(f"Deactivated user with uid: {uid}")

def update_user_last_match(engine: Engine, uid: str, last_match_id: int):
    """특정 유저의 마지막 매치 ID를 갱신합니다."""
    stmt = text("""
        UPDATE user
        SET last_match_id = :last_match_id, last_updated_at = :last_updated_at
        WHERE uid = :uid
    """)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(stmt, {'uid': uid, 'last_match_id': last_match_id, 'last_updated_at': datetime.utcnow()})
    logger.info(f"Updated last_match_id for user {uid} to {last_match_id}")