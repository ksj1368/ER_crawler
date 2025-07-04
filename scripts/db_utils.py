import pymysql
from dbutils.pooled_db import PooledDB
from dotenv import load_dotenv
import os
from typing import List
from time import sleep
import logging
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# 최대 커넥션 수 증가 및 커넥션 풀 최적화
def create_pool():
    return PooledDB(
        creator=pymysql,
        maxconnections=24,  
        mincached=8,        
        maxcached=32,       
        maxshared=8,        
        blocking=True,
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        autocommit=True,
        ping=7
    )

def get_db_connection():
    """프로세스마다 독립적인 풀에서 커넥션을 가져옴

    Returns:
        get_db_connection._pool.connection(): 데이터베이스 커넥션 객체
    """
    if not hasattr(get_db_connection, "_pool"):
        get_db_connection._pool = create_pool()
    
    # 커넥션을 얻기 전에 대기 시간 추가 (필요시)
    # 재시도 로직 추가
    for attempt in range(3):
        try:
            return get_db_connection._pool.connection()
        except Exception as e:
            if attempt < 2:  # 마지막 시도가 아니면 대기 후 재시도
                sleep(1.5)
            else:
                raise

def match_exists(conn, match_id):
    """주어진 match_id가 이미 데이터베이스에 존재하는지 확인

    Args:
        conn (_type_): _description_
        match_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    with conn.cursor() as cursor:
        cursor.executemany("SELECT 1 FROM match_info WHERE match_id = %s LIMIT 1;", (match_id,))
        return cursor.fetchone() is not None
        
def insert_dict(conn, table, data):
    """단일 딕셔너리를 테이블에 삽입

    Args:
        conn (Any): 데이터베이스 연결 객체
        table (str): 데이터를 삽입할 테이블 이름
        data (dict): 삽입할 데이터 딕셔너리
    """
    if not data:
        return
    with conn.cursor() as cursor:
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({values});"
        # executemany의 두 번째 인자는 리스트 of 튜플이어야 함
        cursor.executemany(sql, [tuple(data.values())])

def insert_list(conn, table_name: str, data_list: dict):
    """여러 개의 딕셔너리 데이터를 지정한 테이블에 일괄 삽입

    Args:
        conn (Any): 데이터베이스 연결 객체
        table_name (str): 데이터를 삽입할 테이블 이름
        data_list: 삽입할 데이터 딕셔너리의 리스트

    Raises:
        ValueError: 데이터의 컬럼 개수와 값 개수가 일치하지 않을 때 발생
    """
    keys = list(data_list[0].keys())
    keys_str = ', '.join(keys)
    values_placeholder = ', '.join(['%s'] * len(keys))
    sql = f"INSERT INTO {table_name} ({keys_str}) VALUES ({values_placeholder})"
    values = [tuple(data.get(key) for key in keys) for data in data_list]
    # 각 튜플의 길이가 %s 개수와 일치하는지 체크
    for v in values:
        if len(v) != len(keys):
            raise ValueError(f"Value length {len(v)} does not match column count {len(keys)}")
    with conn.cursor() as cursor:
        cursor.executemany(sql, values)

def bulk_check_match_exists(conn, match_ids):
    """여러 match_id가 이미 데이터베이스에 존재하는지 일괄 확인

    Args:
        conn (Any): 데이터베이스 연결 객체
        match_ids (List[Any]): 존재 여부를 확인할 match_id 리스트

    Returns:
        set: 데이터베이스에 이미 존재하는 match_id의 집합
    """
    if not match_ids:
        return set()
    
    with conn.cursor() as cursor:
        placeholders = ', '.join(['%s'] * len(match_ids))
        sql = f"SELECT match_id FROM match_info WHERE match_id IN ({placeholders});"
        cursor.executemany(sql, match_ids)
        
        # 이미 존재하는 match_id 반환
        return {row[0] for row in cursor.fetchall()}
    
def get_column_as_dict(conn, table_name: str, col: List[str]) -> dict:
    """테이블의 특정 칼럼들에 해당하는 값을 컬럼별 리스트로 묶어 딕셔너리로 반환

    Args:
        conn (_type_): 데이터베이스 연결 객체
        table_name (str): 조회할 테이블 이름
        col (List[str]): 조회할 컬럼명 리스트

    Returns:
        dict: 각 컬럼명을 key로 하고, 해당 col의 리스트를 가지는 딕셔너리
    """
    with conn.cursor() as cursor:
        col_str = ', '.join(f"`{c}`" for c in col)  # 컬럼 리스트를 문자열로 변환
        sql = f"SELECT {col_str} FROM `{table_name}`"
        cursor.execute(sql)
        rows = cursor.fetchall()

        result = {c: [] for c in col}
        for row in rows:
            for idx, c in enumerate(col):
                result[c].append(row[idx])
    return result

def is_table_empty(conn, table_name: str) -> bool:
    """
    테이블이 비어있는지 확인하는 함수

    Args:
        conn: 데이터베이스 연결 객체
        table_name: 확인할 테이블 이름

    Returns:
        bool: 테이블이 비어 있으면 True, 그렇지 않으면 False
    """
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1;")
        return cursor.fetchone() is None
    
    
def save_parsed_data_to_db(conn, parsed_data: list) -> None:
    """DB에 파싱한 데이터를 적재

    Args:
        conn (_type_): 데이터베이스 연결 객체
        parsed_data (_type_): 적재할 데이터
        
    """
    logger = logging.getLogger(__name__)
    try:
        with conn.cursor() as cursor:
            sql = f"SHOW TABLES FROM er_dataset;"
            cursor.execute(sql)
            tables = [t_name[0] for t_name in cursor.fetchall()]
            
        for table in tables:
            if table in parsed_data and parsed_data[table]:
                if isinstance(parsed_data[table], dict) and parsed_data[table]:
                    insert_dict(conn, table, parsed_data[table])
                elif isinstance(parsed_data[table], list) and parsed_data[table]:
                    insert_list(conn, table, parsed_data[table])        
    except Exception as e:
        logger.error(f"Error saving data to DB: {e}")
        raise