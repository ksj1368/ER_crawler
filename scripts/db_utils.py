import os
import threading
from sqlalchemy import create_engine, text, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.dialects.mysql import insert
import logging
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from scripts.config import DATABASE_URL, DB_CHUNK_SIZE
from scripts.models import User, Base, MatchInfo, CreditAcquisitionSource, CreditExpenditureSource

logger = logging.getLogger(__name__)
# Connection Pool Tuning
# pool_size: 유지할 커넥션 수 (기본 5)
# max_overflow: pool_size를 초과하여 허용할 최대 커넥션 수
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, pool_size=20, max_overflow=20)

# 전역 변수 설정
_ACQUISITION_SOURCE_ID_CACHE: Dict[str, int] = {}
_EXPENDITURE_SOURCE_ID_CACHE: Dict[str, int] = {}
_CACHE_LOCK = threading.Lock()

def get_engine() -> Engine:
    """SQLAlchemy 엔진 인스턴스를 반환"""
    return engine

def check_match_exists(engine: Engine, match_ids: list[int]) -> set[int]:
    """DB에 이미 존재하는 매치 ID들을 한번에 조회하여 set으로 반환"""
    if not match_ids:
        return set()
    
    with engine.connect() as conn:
        stmt = select(MatchInfo.match_id).where(MatchInfo.match_id.in_(match_ids))
        result = conn.execute(stmt)
        return {row[0] for row in result}

def get_user_num_map_by_uids(engine: Engine, uids: List[str]) -> Dict[str, int]:
    """
    uid 리스트를 받아 {uid: user_num} 매핑을 반환
    데이터 적재 전 uid를 내부 ID(user_num)로 변환할 때 사용
    """
    if not uids:
        return {}
    
    with engine.connect() as conn:
        stmt = select(User.uid, User.user_num).where(User.uid.in_(uids))
        result = conn.execute(stmt)
        return {row[0]: row[1] for row in result}

def get_uids_by_nicknames(engine: Engine, nicknames: List[str]) -> Dict[str, str]:
    """
    닉네임 리스트를 받아 DB에 존재하는 유저의 {nickname: uid} 맵을 반환
    """
    if not nicknames:
        return {}
    
    with engine.connect() as conn:
        stmt = select(User.nickname, User.uid).where(User.nickname.in_(nicknames))
        result = conn.execute(stmt)
        return {row[0]: row[1] for row in result}

def _get_or_create_sources_generic(
    engine: Engine, 
    items: List[str], 
    cache: Dict[str, int], 
    model: Any, 
    table_name: str
) -> Dict[str, int]:
    """
    크레딧 획득, 소모 소스 공통 처리 함수 (최적화된 락 사용)
    :param engine: DB 엔진
    :param items: 소스 이름 리스트
    :param cache: 소스 이름-아이디 매핑 캐시 딕셔너리
    :param model: SQLAlchemy 모델 클래스
    :param table_name: DB 테이블 이름
    :return: {source_name: source_id} 매핑 딕셔너리
    """
    if not items:
        return {}

    # 테이블 검증
    if table_name not in Base.metadata.tables:
        raise ValueError(f"Table '{table_name}' not found in metadata")
        
    item_map = {}
    missing_items = []
    
    # 1. 초기 캐시 확인(Lock 보유)
    with _CACHE_LOCK:
        for item in set(items):
            if item in cache:
                item_map[item] = cache[item]
            else:
                missing_items.append(item)
                
    if not missing_items:
        return item_map
    
    # 2. DB 조회(Lock 미보유 - I/O 병목 방지)
    with engine.connect() as conn:
        stmt = select(model.source_name, model.source_id).where(
            model.source_name.in_(missing_items)
        )
        result = conn.execute(stmt)
        existing = {row[0]: row[1] for row in result}
        
    # 3. 캐시 업데이트 및 진짜 없는 항목 식별(Lock 보유)
    with _CACHE_LOCK:
        cache.update(existing)
        item_map.update(existing)
        
        really_missing = []
        for item in missing_items:
            if item in item_map:
                continue
            # 다른 스레드가 그 사이 캐시에 넣었는지 확인
            if item in cache:
                item_map[item] = cache[item]
            else:
                really_missing.append(item)
            
    # 4. 새로운 항목 INSERT(Lock 미보유)
    if really_missing:
        try:
            with engine.begin() as conn:
                values = [{"source_name": item} for item in really_missing]
                stmt = insert(model.__table__).prefix_with("IGNORE")
                conn.execute(stmt, values)
                
            # 5. 새로 생성된 항목 재조회(Lock 미보유)
            with engine.connect() as conn:
                stmt = select(model.source_name, model.source_id).where(
                    model.source_name.in_(really_missing)
                )
                result = conn.execute(stmt)
                new_mapping = {row[0]: row[1] for row in result}
                
            # 6. 최종 캐시 업데이트(Lock 보유)
            with _CACHE_LOCK:
                cache.update(new_mapping)
                item_map.update(new_mapping)
                
        except Exception as e:
            logger.error(f"Failed to create sources in {table_name}: {e}")
            raise
        
    return item_map

def _get_or_create_acquisition_sources(engine: Engine, sources: List[str]) -> Dict[str, int]:
    """
    크레딧 획득처를 mapping: {source_name: source_id}으로 반환.
    DB에 없는 새로운 source_id은 새로 생성. In-Memory Cache 사용.
    """
    return _get_or_create_sources_generic(
        engine, 
        sources, 
        _ACQUISITION_SOURCE_ID_CACHE, 
        CreditAcquisitionSource, 
        "credit_acquisition_source"
    )

def _get_or_create_expenditure_sources(engine: Engine, items: List[str]) -> Dict[str, int]:
    """
    크레딧 소모처(아이템 등)를 mapping: {expenditure_item: source_id}으로 반환.
    DB에 없는 새로운 source_id은 새로 생성. In-Memory Cache 사용.
    """
    return _get_or_create_sources_generic(
        engine, 
        items, 
        _EXPENDITURE_SOURCE_ID_CACHE, 
        CreditExpenditureSource, 
        "credit_expenditure_source"
    )

def _save_single_list(engine: Engine, table_name: str, data_list: List[Dict[str, Any]]):
    """단일 리스트를 DB에 저장하는 함수"""
    if not data_list:
        return
    
    total_rows = len(data_list)
    
    try:
        # Transaction 시작
        with engine.begin() as conn:
            # 데이터 무결설 보장을 위해 FOREIGN_KEY_CHECKS=0 제거
            logger.info(f"Inserting {total_rows} rows into '{table_name}' (Chunk size: {DB_CHUNK_SIZE})")

            is_raw_sql = table_name not in Base.metadata.tables
            raw_stmt = None
            
            if is_raw_sql:
                # 키를 추출하기 전에 추출 대상 데이터가 실제로 존재하는지 확인
                if total_rows > 0: 
                    logger.warning(f"Table '{table_name}' not found in metadata. Using raw SQL.")
                    keys = data_list[0].keys()
                    # SQL 예약어와 충돌하지 않도록 컬럼 이름을 '`'로 감싸기
                    columns = ', '.join([f"`{key}`" for key in keys])
                    placeholders = ', '.join([f":{key}" for key in keys])
                    # INSERT IGNORE 적용 (Raw SQL)
                    raw_stmt = text(f"INSERT IGNORE INTO `{table_name}` ({columns}) VALUES ({placeholders})")

            # 2. 데이터 삽입 로직
            for start_idx in range(0, total_rows, DB_CHUNK_SIZE):
                end_idx = start_idx + DB_CHUNK_SIZE
                chunk = data_list[start_idx:end_idx]
                
                if not chunk:
                    continue

                if not is_raw_sql:
                    table = Base.metadata.tables[table_name]
                    # INSERT IGNORE 적용 (SQLAlchemy Core)
                    stmt = insert(table).prefix_with("IGNORE").values(chunk)
                    conn.execute(stmt)
                else:
                    if raw_stmt:
                            conn.execute(raw_stmt, chunk)
            
    except Exception as e:
        logger.error(f"Failed to save table '{table_name}': {e}")
        raise

def save_data_to_db(engine: Engine, parsed_data: Dict[str, List[Dict[str, Any]]]) -> None:
    """파싱된 데이터를 DB에 저장
    Args:
        engine (Engine): SQLAlchemy 엔진
        parsed_data (Dict[str, List[Dict[str, Any]]]): 파싱된 데이터
    1. 크레딧 획득 소스 매핑
    2. 크레딧 소모 소스 매핑
    3. match_info 저장 (부모 테이블)
    4. 나머지 테이블 병렬 저장
    5. 예외 처리
    """
    # 크레딧 획득 소스 매핑
    if 'match_user_credit_acquisitions' in parsed_data:
        data_list = parsed_data['match_user_credit_acquisitions']
        if data_list:
            unique_sources = list({item['acquisition_source'] for item in data_list if 'acquisition_source' in item})
            source_map = _get_or_create_acquisition_sources(engine, unique_sources)
            
            valid_list = []
            for item in data_list:
                src = item.pop('acquisition_source', None)
                if src and src in source_map:
                    item['acquisition_source_id'] = source_map[src]
                    valid_list.append(item)
            
            parsed_data['match_user_credit_acquisitions'] = valid_list

    # 크레딧 소모 소스 매핑
    if 'match_user_credit_expenditures' in parsed_data:
        data_list = parsed_data['match_user_credit_expenditures']
        if data_list:
            unique_items = list({
                str(item['expenditure_item']) 
                for item in data_list 
                if item.get('expenditure_item') is not None and str(item['expenditure_item']).strip()
            })
            source_map = _get_or_create_expenditure_sources(engine, unique_items)
            
            valid_list = []
            for item in data_list:
                item_val = item.pop('expenditure_item', None)
                if item_val is not None and str(item_val) in source_map:
                    item['expenditure_source_id'] = source_map[str(item_val)]
                    valid_list.append(item)
            
            parsed_data['match_user_credit_expenditures'] = valid_list
            
    # 저장할 모든 테이블 목록
    all_tables = list(parsed_data.keys())
    
    if not all_tables:
        return

    # 1. Match Info 저장 (Parent Table - Must save first)
    if 'match_info' in parsed_data:
        try:
            _save_single_list(engine, 'match_info', parsed_data['match_info'])
        except Exception as e:
            logger.error(f"Failed to save match_info (Parent). Aborting batch save. Error: {e}")
            raise e
        
        all_tables.remove('match_info')

    # 2. 나머지 테이블 병렬 저장
    # 워커 수를 환경 변수로 제어 (기본값: 2로 상향 조정하여 병렬 처리 활성화)
    max_workers = int(os.getenv("DB_MAX_WORKERS", 2))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_save_single_list, engine, table_name, parsed_data[table_name]): table_name
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
    """is_active가 True인 모든 유저의 uid, user_num, nickname, last_match_id를 조회"""
    with engine.connect() as conn:
        # user_num 추가 조회
        stmt = select(User.uid, User.nickname, User.last_match_id, User.user_num).where(User.is_active == True)
        result = conn.execute(stmt)
        return [{'uid': row[0], 'nickname': row[1], 'last_match_id': row[2], 'user_num': row[3]} for row in result]

def upsert_users(engine: Engine, users_data: List[Dict[str, str]]):
    """
    여러 유저 정보를 Upsert
    - DB에 없는 uid는 새로 추가 (user_num 자동 생성)
    - DB에 이미 있는 uid는 nickname과 last_updated_at을 갱신
    """
    if not users_data:
        return

    now = datetime.utcnow()
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
    """특정 uid의 is_active를 False로 설정"""
    stmt = update(User).where(User.uid == uid).values(is_active=False, last_updated_at=datetime.utcnow())
    with engine.begin() as conn:
        conn.execute(stmt)
    logger.warning(f"Deactivated user with uid: {uid}")

def update_user_last_match(engine: Engine, uid: str, last_match_id: int):
    """특정 유저의 마지막 매치 ID를 갱신"""
    stmt = update(User).where(User.uid == uid).values(last_match_id=last_match_id, last_updated_at=datetime.utcnow())
    with engine.begin() as conn:
        conn.execute(stmt)
    logger.info(f"Updated last_match_id for user {uid} to {last_match_id}")

def update_user_last_match_bulk(engine: Engine, user_updates: List[Dict[str, Any]]):
    """
    여러 유저의 마지막 매치 ID를 일괄 갱신(Batch Update)
    :param user_updates: [{'uid': str, 'last_match_id': int}, ...]
    """
    if not user_updates:
        return

    now = datetime.utcnow()
    with engine.begin() as conn:
        for update_data in user_updates:
            stmt = update(User).where(User.uid == update_data['uid']).values(
                last_match_id=update_data['last_match_id'],
                last_updated_at=now
            )
            conn.execute(stmt)
            
    logger.info(f"Bulk updated last_match_id for {len(user_updates)} users.")