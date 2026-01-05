import asyncio
import os
import psutil
import gc
from time import time
from datetime import datetime

from scripts.config import SEASON_ID, MATCHING_MODE, REGION_ID, ENV, BATCH_SIZE
from scripts.crawler import ERAPIClient
from scripts.storage import get_storage
from scripts.db_utils import (
    get_engine, deactivate_user, get_active_users, upsert_users, 
    update_user_last_match_bulk, save_data_to_db, check_match_exists, 
    get_uids_by_nicknames, get_user_num_map_by_uids
)
from scripts.match_info_parsing import top_ranker_nicknames, parse_match_data
from scripts.logger import logger

def log_memory():
    """현재 프로세스의 메모리 사용량을 로깅합니다."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logger.info(f"[Memory] RSS: {mem_info.rss / 1024 / 1024:.2f} MB")

async def seed_top_rankers():
    """
    Top 1000 랭커를 가져와 DB에 시드 유저로 추가합니다.
    - 랭커 목록에서 닉네임을 가져옵니다.
    - 각 닉네임을 사용하여 uid를 조회합니다.
    - 조회된 유저 정보를 DB에 Upsert합니다.
    """
    logger.info("--- Starting to seed top rankers ---")
    engine = get_engine()
    
    # 상위 랭커 닉네임 목록 가져오기
    async with ERAPIClient() as client:
        rankers_json = await client.get_top_ranker(season_id=SEASON_ID, matching_mode=MATCHING_MODE, server_code=REGION_ID)
        
        if not rankers_json:
            logger.error("Failed to get top rankers. Exiting seeding.")
            return
        
        nicknames = top_ranker_nicknames(rankers_json)
        # nicknames = nicknames[:1000] # 디버그용 샘플링
        logger.info(f"Found {len(nicknames)} top ranker nicknames.")
        
        # 닉네임으로 uid 조회
        logger.info("Fetching uids for rankers concurrently...")
        user_infos = await client.get_users_by_nickname_async(nicknames)
    
    # DB에 시드 유저 추가/업데이트
    if user_infos:
        seed_users_data = [{'uid': user['userId'], 'nickname': user['nickname']} for user in user_infos]
        upsert_users(engine, seed_users_data)
        logger.info(f"Successfully upserted {len(seed_users_data)} seed users into the database.")
    
    logger.info("--- Seeding top rankers finished ---")


async def run_pipeline():
    """
    데이터 수집 파이프라인
    1. 활성 유저 유무 확인
    2. 유저가 없으면(초기 상태) 자동으로 시드 데이터(Top Rankers) 수집
    3. 유저가 있으면 기존 크롤링(스노우볼링) 로직 수행(Queue 기반 비동기 처리)
    """
    pipeline_start_time = time()
    logger.info("--- Start Pipeline (Async Queue) ---")
    log_memory()
    
    # 스토리지 및 DB 초기화
    storage = get_storage(ENV)
    engine = get_engine()

    # 1. 활성 유저 확인 / 시드 데이터 수집
    step_start_time = time()
    active_users = get_active_users(engine)
    logger.info(f"Initial Check: Found {len(active_users)} active users.")

    # 2. 유저가 없으면 Auto-Seeding 수행
    if not active_users:
        logger.info("No active users found. Initiating Auto-Seeding...")
        await seed_top_rankers()
        
        # 재확인
        active_users = get_active_users(engine)
        if not active_users:
            logger.error("Auto-Seeding failed. No users found even after seeding. Exiting.")
            return
        logger.info(f"Auto-Seeding complete. Found {len(active_users)} active users.")
    else:
        logger.info("Active users exist. Proceeding to crawling...")

    # active_users 제한 (디버그/테스트용, 필요시 주석 해제 또는 환경변수 처리)
    # active_users = active_users[:1000] 

    logger.info(f"Step 1: User check/seeding finished in {time() - step_start_time:.2f}s")
    log_memory()

    logger.info(f"Processing {len(active_users)} active users.")

    async with ERAPIClient() as client:
        # 각 유저의 신규 게임 정보 수집
        step_start_time = time()
        user_game_generator = client.get_user_games_by_uid_async(active_users)
        
        all_new_match_ids = set()
        user_match_map = {}

        async for user_result in user_game_generator:
            uid = user_result['uid']
            
            if user_result['status'] == 'deactivated':
                deactivate_user(engine, uid)
                continue
            
            if user_result['status'] != 'success' or not user_result.get('matches'):
                continue

            new_matches = user_result['matches']
            user_match_map[uid] = new_matches
            all_new_match_ids.update(new_matches)
        
        logger.info(f"Step 2: Collecting user games finished in {time() - step_start_time:.2f}s")
        log_memory()
        
        # DB에 이미 있는 매치 ID 필터링
        step_start_time = time()
        if not all_new_match_ids:
            logger.info("No new matches found across all active users. Pipeline finished.")
            return
        
        
        existing_match_ids = check_match_exists(engine, list(all_new_match_ids)) # 기존 매치 ID 조회
        final_match_ids_to_process = list(all_new_match_ids - existing_match_ids) # 신규 매치 ID 필터링
        # final_match_ids_to_process = final_match_ids_to_process[:1000] # 디버그용 샘플링
        logger.info(f"Step 3: Filtering new matches finished in {time() - step_start_time:.2f}s")
        
        if not final_match_ids_to_process:
            logger.info("No new matches to process after filtering existing ones. Collection complete.")
            return

        total_matches = len(final_match_ids_to_process)
        logger.info(f"Found {total_matches} new unique matches to process. Starting Queue Processing...")

        # 3. 큐 기반 처리(Producer-Consumer 패턴)
        queue = asyncio.Queue(maxsize=3) # 버퍼 크기: 배치 3개
        
        producer_task = asyncio.create_task(produce_batches(
            client, final_match_ids_to_process, queue, engine, storage
        ))
        consumer_task = asyncio.create_task(consume_batches(engine, queue))
        
        # 생산자 작업 완료 대기
        await producer_task
        
        # 큐의 모든 작업이 처리될 때까지 대기
        await queue.join()
        
        # 소비자 작업 종료
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    # 4. 각 유저의 last_match_id 갱신(전체 루프 종료 후 한 번만)
    step_start_time = time()
    logger.info("Updating last_match_id for processed users...")
    
    user_updates = []
    for uid, matches in user_match_map.items():
        if matches:
            latest_match_id = max(matches)
            user_updates.append({'uid': uid, 'last_match_id': latest_match_id})
    
    if user_updates:
        update_user_last_match_bulk(engine, user_updates)
        
    logger.info("Update complete.")
    logger.info(f"Step 9: Updating last match IDs finished in {time() - step_start_time:.2f}s")

    elapsed_time = time() - pipeline_start_time
    logger.info(f"--- Data collection pipeline finished in {elapsed_time:.2f} seconds ---")