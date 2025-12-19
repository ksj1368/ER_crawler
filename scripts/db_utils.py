import os
from sqlalchemy import create_engine, text, select, update
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.dialects.mysql import insert
import pandas as pd
import logging
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from scripts.config import DATABASE_URL
from scripts.models import User, Base, MatchInfo

logger = logging.getLogger(__name__)
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

def get_uids_by_nicknames(engine: Engine, nicknames: List[str]) -> Dict[str, str]:
    """
    닉네임 리스트를 받아 DB에 존재하는 유저의 {nickname: uid} 맵을 반환합니다.
    """
    if not nicknames:
        return {}
    
    with engine.connect() as conn:
        stmt = text("SELECT nickname, uid FROM user WHERE nickname IN :nicknames")
        result = conn.execute(stmt, {"nicknames": tuple(nicknames)})
        return {row[0]: row[1] for row in result}

def _save_single_dataframe(engine: Engine, table_name: str, df: pd.DataFrame):
    """단일 데이터프레임을 DB에 저장하는 함수(Bulk Insert 최적화)"""
    if df.empty:
        return
    
    try:
        # DB NULL 처리를 위해 NaN을 None으로 변환 
        df_obj = df.astype(object).where(pd.notnull(df), None)
        
        data_to_insert = df_obj.to_dict(orient='records')
        if not data_to_insert:
            return

        with engine.begin() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
            logger.info(f"Inserting {len(data_to_insert)} rows into '{table_name}'")

            if table_name in Base.metadata.tables:
                table = Base.metadata.tables[table_name]
                stmt = insert(table).values(data_to_insert)
                conn.execute(stmt)
            else:
                logger.warning(f"Table '{table_name}' not found in metadata. Using raw SQL.")
                keys = data_to_insert[0].keys()
                columns = ', '.join(keys)
                placeholders = ', '.join([f":{key}" for key in keys])
                
                stmt = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})")
                conn.execute(stmt, data_to_insert)
            
    except Exception as e:
        logger.error(f"Failed to save table '{table_name}': {e}")
        raise

def save_dataframes_to_db(engine: Engine, parsed_data: dict[str, pd.DataFrame]):
    """
    파싱된 데이터프레임 딕셔너리를 DB의 각 테이블에 저장합니다.
    """
    # 저장할 모든 테이블 목록
    all_tables = list(parsed_data.keys())
    
    if not all_tables:
        return

    # HDD: 워커 수를 1로 설정하여 순차 쓰기로 디스크 thrashing 방지
    # SSD: 4~8 권장
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {
            executor.submit(_save_single_dataframe, engine, table_name, parsed_data[table_name]): table_name
            for table_name in all_tables
        }
        
        for future in as_completed(futures):
            table_name = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Parallel insertion failed for {table_name}: {e}")
                raise e

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

    now = datetime.utcnow()
    
    # Prepare list of dictionaries for bulk insert
    values_list = [
        {
            'uid': user['uid'],
            'nickname': user['nickname'],
            'last_match_id': 0, # Default for new users
            'is_active': True,
            'last_updated_at': now
        }
        for user in users_data
    ]

    insert_stmt = insert(User).values(values_list)

    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
        nickname=insert_stmt.inserted.nickname,
        is_active=True,
        last_updated_at=insert_stmt.inserted.last_updated_at
    )
    
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(on_duplicate_key_stmt)
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

def update_user_last_match_bulk(engine: Engine, user_updates: List[Dict[str, Any]]):
    """
    여러 유저의 마지막 매치 ID를 일괄 갱신합니다. (Batch Update)
    :param user_updates: [{'uid': str, 'last_match_id': int}, ...]
    """
    if not user_updates:
        return

    stmt = text("""
        UPDATE user
        SET last_match_id = :last_match_id, last_updated_at = :last_updated_at
        WHERE uid = :uid
    """)
    
    now = datetime.utcnow()
    # Add timestamp to all updates
    for update in user_updates:
        update['last_updated_at'] = now
        
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(stmt, user_updates)
    logger.info(f"Bulk updated last_match_id for {len(user_updates)} users.")