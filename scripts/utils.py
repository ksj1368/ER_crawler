from datetime import datetime
import asyncio
import logging
import os
from time import time, sleep
from dotenv import load_dotenv
from tqdm import tqdm
from typing import Optional
from multiprocessing import cpu_count
from crawler import (
    match_info, get_character, get_equipment, get_trait, get_l10n, 
    get_match_ids_async, get_match_infos_async
)
from parsing import parse_match_data
from db_utils import get_db_connection, insert_list, get_column_as_dict, is_table_empty, save_parsed_data_to_db, match_exists
from concurrent.futures import ProcessPoolExecutor
from parsing import parse_game_character, parse_equipment, parse_trait_info, parse_txt_to_dict

def setup_logger(LOG_DIR: str):
    """지정한 디렉토리에 로그 파일을 생성하고 파일 및 콘솔 로그를 동시에 출력하는 로거를 선언하는 함수

    Args:
        LOG_DIR (str): 로그 파일이 저장될 디렉토리 경로

    Returns:
        logging.Logger: 설정된 로거 객체
    """
    load_dotenv()
    start_time = time()
    start_dt_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d_%H-%M-%S')
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file_path = os.path.join(LOG_DIR, f"log_{start_dt_str}.txt")

    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )
    return logger

def split_into_chunks(lst, chunk_size):
    """리스트를 chunk_size 크기로 분할
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def fetch_match_data_with_retry(match_id: int, max_retries: int = 1) -> Optional[dict]:
    """_summary_

    Args:
        match_id (int): _description_
        max_retries (int, optional): _description_. Defaults to 1.

    Returns:
        Optional[dict]: _description_
    """
    logger = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        raw = match_info(match_id)
        if raw:
            return raw
        logger.warning(f"[RETRY] match_id {match_id} attempt {attempt+1}/{max_retries} failed.")
        time.sleep(1 + attempt)
    return None

def process_match_batch(batch_data):
    logger = logging.getLogger(__name__)
    """배치 단위로 매치 데이터를 처리"""
    results = []
    for match_id, match_data in batch_data:
        try:
            result = process_match_id(match_id, match_data)
            results.append((match_id, result))
        except Exception as e:
            logger.error(f"Error processing match {match_id}: {e}")
            results.append((match_id, False))
    return results

def process_match_id(match_id, match_data):
    """주어진 match_id와 match_data를 처리하여 데이터베이스에 저장

    Args:
        match_id (str): 경기 고유 ID
        match_data (dict): 경기 데이터 (없을 경우 None)

    Returns:
        bool: 처리 성공 시 True, 실패 시 False
    """
    logger = logging.getLogger(__name__)
    conn = None
    try:
        conn = get_db_connection()

        if match_exists(conn, match_id):
            logger.info(f"[SKIP] match_id {match_id} already exists.")
            conn.close()
            return True

        # 데이터 가져오기
        if match_data is None:
            raw = fetch_match_data_with_retry(match_id)
            if raw is None:
                logger.warning(f"[SKIP] match_id {match_id} returned None after retries.")
                conn.close()
                return False
        else:
            raw = match_data

        # 매치에 참여한 유저가 21명 미만일 경우 skip
        if len(raw["userGames"]) < 21:
            logger.info(f"[SKIP] match_id {match_id} userGames length < 21")
            conn.close()
            return False
        
        # 파싱
        try:
            parsed_data = parse_match_data(raw)
        except Exception as e:
            logger.error(f"[PARSE ERROR] match_id {match_id}: {e}", exc_info=True)
            conn.close()
            return False

        # 저장
        try:
            save_parsed_data_to_db(conn, parsed_data)
        except Exception as e:
            logger.error(f"[DB ERROR] match_id {match_id}: {e}")
            conn.close()
            return False

        logger.info(f"[SUCCESS] match_id {match_id} saved.")
        conn.close()
        return True

    except Exception as e:
        logger.error(f"[FATAL ERROR] match_id {match_id} failed: {e}")
        sleep(5.0)
        process_match_id(match_id, match_data)
        return False
    finally:
        if conn:
            conn.close()
            
def collect_data(users, main_version, batch_size, log_dir, start_date):
    """
    사용자 게임 데이터를 수집하고 처리
    
    Args:
        user_count: 수집할 상위 사용자 수
        main_version: 게임 버전
        batch_size: 배치 처리 크기
        log_dir: 로그 저장 경로
        start_date: 수집 시작 일자
    """
    logger = logging.getLogger(__name__)
    start_time = time()
    logger.info(f"Starting data collection with {len(users)} users")
    
    # 정적 데이터 먼저 처리
    conn = get_db_connection()
    
    # DB에 이미 있는 match_id 가져오기(중복 제거용)
    exist_match_ids = get_column_as_dict(conn, "match_info", ["match_id", "version_major"])
    exist_match_ids = exist_match_ids["match_id"]
    
    try:
        # 정적 데이터 가져오기
        logger.info("Fetching static data...")
        character_data, levelup_data = get_character()
        l10n = get_l10n()
        txt_mapping = parse_txt_to_dict(l10n)
        armor, weapon = get_equipment()
        trait = get_trait()

        # 정적 데이터 파싱 및 저장
        logger.info("Parsing and saving static data...")
        result = {
            "game_character": parse_game_character(character_data, levelup_data),
            "equipment": parse_equipment(armor, weapon),
            "trait_info": parse_trait_info(trait, txt_mapping),
        }

        for key, data in result.items():
            if is_table_empty(conn, key):
                logger.info(f"Inserting {len(data)} records into {key} (table is empty)")
                insert_list(conn, key, data)
            else:
                logger.info(f"Skipping {key}: table is not empty")
    finally:
        conn.close()
    
    # 비동기로 매치 ID 수집
    logger.info(f"Collecting match IDs for {len(users)} users...")
    match_ids = asyncio.run(get_match_ids_async(users, main_version))
    logger.info(f"Collected {len(match_ids)} unique match IDs")
    match_ids = list(set(match_ids) - set(exist_match_ids))
    logger.info(f"Drop exist match IDs in Database. {len(match_ids)} unique match IDs")
    
    # 비동기로 매치 데이터 수집
    logger.info(f"Fetching match data in batches of {batch_size}...")
    match_data_dict = asyncio.run(get_match_infos_async(match_ids, batch_size))
    logger.info(f"Successfully fetched {len(match_data_dict)} match data")
    
    # 처리를 위한 배치 생성
    batches = []
    current_batch = []
    
    for match_id in match_ids:
        match_data = match_data_dict.get(match_id)
        current_batch.append((match_id, match_data))
        
        if len(current_batch) >= batch_size:
            batches.append(current_batch)
            current_batch = []
    
    if current_batch:  # 남은 배치 처리
        batches.append(current_batch)

    async def process_batches_async(batches):
        loop = asyncio.get_running_loop()
        results = []
        with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
            tasks = [
                loop.run_in_executor(executor, process_match_batch, batch)
                for batch in batches
            ]
            for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing batches"):
                result = await f
                results.append(result)
        return results

    logger.info(f"Processing {len(batches)} batches with {cpu_count()} processes (async)...")
    results = asyncio.run(process_batches_async(batches))    
    
    # 처리 결과 요약
    flat_results = [item for sublist in results for item in sublist]
    success_count = sum(1 for _, success in flat_results if success)
    failures = [match_id for match_id, success in flat_results if not success]

    # 실패 match_id 저장
    if failures:
        fail_path = os.path.join(log_dir, f"failed_match_ids_{start_date}.txt")
        with open(fail_path, "w", encoding="utf-8") as f:
            for mid in failures:
                f.write(f"{mid}\n")
        logger.warning(f"{len(failures)} matches failed and were saved to: {fail_path}")

    # 소요 시간 계산
    elapsed_time = time() - start_time
    logger.info(f"Data collection completed in {elapsed_time:.2f} seconds")
    logger.info(f"Successfully processed {success_count} out of {len(match_ids)} matches")
    
    return success_count, len(match_ids)