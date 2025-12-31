import asyncio
import os
import psutil
import gc
from time import time
from datetime import datetime
import pandas as pd

from scripts.config import SEASON_ID, MATCHING_MODE, REGION_ID, ENV
from scripts.crawler import ERAPIClient
from scripts.storage import get_storage
from scripts.db_utils import (
    get_engine, deactivate_user, get_active_users, upsert_users, 
    update_user_last_match_bulk, save_dataframes_to_db, check_match_exists, 
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
    3. 유저가 있으면 기존 크롤링(스노우볼링) 로직 수행
    """
    pipeline_start_time = time()
    logger.info("--- Start Pipeline ---")
    log_memory()
    
    # 스토리지 및 DB 초기화
    storage = get_storage(ENV)
    engine = get_engine()

    # 1. 활성 유저 확인
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
        logger.info(f"Found {total_matches} new unique matches to process. Starting batch processing...")

        # 배치 처리
        BATCH_SIZE = 100 # OOM 방지용

        # 배치별 매치 데이터 수집 및 저장
        for i in range(0, total_matches, BATCH_SIZE):
            batch_match_ids = final_match_ids_to_process[i:i + BATCH_SIZE]
            logger.info(f"--- Processing Batch {i // BATCH_SIZE + 1} / {(total_matches - 1) // BATCH_SIZE + 1} ({len(batch_match_ids)} matches) ---")
            
            batch_start_time = time()
            
            # 새로운 매치 데이터 수집
            raw_match_data_list = []
            batch_participant_nicknames = set()
            
            match_data_generator = client.get_match_infos_async(batch_match_ids)
            async for match_id, raw_data in match_data_generator:
                if raw_data and 'userGames' in raw_data:
                    raw_match_data_list.append((match_id, raw_data))
                    for user in raw_data['userGames']:
                        batch_participant_nicknames.add(user['nickname'])
            
            # 원본 매치데이터를 데이터 레이크에 저장
            if raw_match_data_list:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # 저장 경로 (S3 Key 또는 로컬 경로)
                # 예: data/raw/20231027/batch_0_123456.json 형태로 저장
                date_str = datetime.now().strftime("%Y%m%d")
                filename = f"data/raw/{date_str}/batch_{i}_{timestamp}.json"
                
                # 저장 데이터 준비
                data_to_save = [data for _, data in raw_match_data_list]
                
                # 스토리지 추상화를 통해 저장
                storage.save(data_to_save, filename)

            # uid 조회 로직(DB 우선 조회)
            all_nicknames_list = list(batch_participant_nicknames)
            existing_users_map = get_uids_by_nicknames(engine, all_nicknames_list)
            unknown_nicknames = [nick for nick in all_nicknames_list if nick not in existing_users_map]
            
            new_user_infos = []
            if unknown_nicknames:
                logger.info(f"Fetching {len(unknown_nicknames)} unknown nicknames from API...")
                new_user_infos = await client.get_users_by_nickname_async(unknown_nicknames)
            
            nickname_to_uid_map = existing_users_map.copy()
            for user in new_user_infos:
                nickname_to_uid_map[user['nickname']] = user['userId']

            # 파싱 데이터 정리
            all_new_participants = []
            all_parsed_data = []

            for match_id, raw_data in raw_match_data_list:
                try:
                    valid_user_games = []
                    for user_game in raw_data['userGames']:
                        nickname = user_game['nickname']
                        if nickname in nickname_to_uid_map:
                            user_game['uid'] = nickname_to_uid_map[nickname]
                            valid_user_games.append(user_game)
                    raw_data['userGames'] = valid_user_games
                    
                    # 신규 유저 정보 수집(DB Upsert용)
                    for user_info in new_user_infos:
                        if any(u['nickname'] == user_info['nickname'] for u in raw_data['userGames']):
                            all_new_participants.append({'uid': user_info['userId'], 'nickname': user_info['nickname']})
                    if raw_data['userGames']:
                        parsed_data = parse_match_data(raw_data)
                        all_parsed_data.append(parsed_data)
                except Exception as e:
                    logger.error(f"Failed to process match {match_id}: {e}")

            # 신규 유저 저장
            if all_new_participants:
                unique_participants = list({p['uid']: p for p in all_new_participants}.values())
                upsert_users(engine, unique_participants)

            # 현재 배치의 모든 유저 uid 수집
            batch_uids = set()
            for _, raw_data in raw_match_data_list:
                if 'userGames' in raw_data:
                    for user_game in raw_data['userGames']:
                        if 'uid' in user_game:
                            batch_uids.add(user_game['uid'])
            
            uid_to_user_num = get_user_num_map_by_uids(engine, list(batch_uids))

            # 매치 데이터 저장
            if all_parsed_data:
                combined_data = {}
                for parsed_data in all_parsed_data:
                    for table_name, df in parsed_data.items():
                        
                        if 'uid' in df.columns:
                            # 매핑 적용
                            df['user_num'] = df['uid'].map(uid_to_user_num)
                            
                            # 매핑 실패한 행 처리 (로깅 후 제거)
                            if df['user_num'].isnull().any():
                                missing_count = df['user_num'].isnull().sum()
                                logger.warning(f"Missing user_num mapping for {missing_count} rows in table {table_name}. Dropping them.")
                                df.dropna(subset=['user_num'], inplace=True)
                            
                            # 타입 변환 및 uid 제거
                            df['user_num'] = df['user_num'].astype(int)
                            df.drop(columns=['uid'], inplace=True)

                        if table_name not in combined_data:
                            combined_data[table_name] = []
                        combined_data[table_name].append(df)
                
                for table_name, df_list in combined_data.items():
                    if df_list:
                        combined_data[table_name] = pd.concat(df_list, ignore_index=True)

                save_dataframes_to_db(engine, combined_data)
            
            logger.info(f"Batch finished in {time() - batch_start_time:.2f}s")
            
            # 메모리 정리
            del raw_match_data_list, all_parsed_data, new_user_infos
            gc.collect()
            log_memory() 

    # 각 유저의 last_match_id 갱신(전체 루프 종료 후 한 번만)
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