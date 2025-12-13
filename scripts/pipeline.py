import asyncio
import aiohttp
from time import time
from typing import List, Dict, Any

import pandas as pd
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from scripts.config import SEASON_ID, MATCHING_MODE, REGION_ID
from scripts.crawler import get_top_ranker, get_users_by_nickname_async, get_user_games_by_uid_async, get_match_infos_async, HEADERS_WITH_KEY
from scripts.db_utils import get_engine, deactivate_user, get_active_users, upsert_users, update_user_last_match, save_dataframes_to_db, check_match_exists
from scripts.match_info_parsing import top_ranker_nicknames, parse_match_data, parse_match_user_start
from scripts.logger import logger

async def seed_top_rankers():
    """
    Top 1000 랭커를 가져와 DB에 시드 유저로 추가합니다.
    - 랭커 목록에서 닉네임을 가져옵니다.
    - 각 닉네임을 사용하여 uid를 조회합니다.
    - 조회된 유저 정보를 DB에 Upsert합니다.
    """
    logger.info("--- Starting to seed top rankers ---")
    engine = get_engine()
    
    # 1. 상위 랭커 닉네임 목록 가져오기
    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        rankers_json = await get_top_ranker(session, season_id=SEASON_ID, matching_mode=MATCHING_MODE, server_code=REGION_ID)
    
    if not rankers_json:
        logger.error("Failed to get top rankers. Exiting seeding.")
        return
    
    nicknames = top_ranker_nicknames(rankers_json)
    nicknames = nicknames[:100]
    logger.info(f"Found {len(nicknames)} top ranker nicknames.")
    
    # 2. 닉네임으로 uid 비동기 조회
    logger.info("Fetching uids for rankers concurrently...")
    user_infos = await get_users_by_nickname_async(nicknames)
    
    # 3. DB에 시드 유저 추가/업데이트
    if user_infos:
        # get_users_by_nickname_async는 user 객체 리스트를 반환하므로, 필요한 형태로 변환
        seed_users_data = [{'uid': user['userId'], 'nickname': user['nickname']} for user in user_infos]
        upsert_users(engine, seed_users_data)
        logger.info(f"Successfully upserted {len(seed_users_data)} seed users into the database.")
    
    logger.info("--- Seeding top rankers finished ---")


async def run_pipeline():
    """
    데이터 수집 및 처리 파이프라인 실행 (스노우볼링 방식)
    """
    pipeline_start_time = time()
    logger.info("--- Starting data collection pipeline (Snowballing) ---")
    engine = get_engine()

    # 1. DB에서 활성 유저 목록 가져오기
    step_start_time = time()
    active_users = get_active_users(engine)
    # 테스트용으로 상위 100명만 처리
    active_users = active_users[:100]  
    logger.info(f"Step 1: Fetching active users finished in {time() - step_start_time:.2f}s")
    
    if not active_users:
        logger.warning("No active users found in the database. Consider seeding first. Exiting.")
        return
    
    active_user_nicknames = {user['nickname'] for user in active_users}
    logger.info(f"Found {len(active_users)} active users to process. (e.g., {list(active_user_nicknames)[:5]})")

    # 2. 각 유저의 신규 게임 정보 비동기적으로 수집
    step_start_time = time()
    user_game_generator = get_user_games_by_uid_async(active_users)
    
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
    
    # 3. DB에 이미 있는 매치 ID 필터링
    step_start_time = time()
    if not all_new_match_ids:
        logger.info("No new matches found across all active users. Pipeline finished.")
        return
        
    existing_match_ids = check_match_exists(engine, list(all_new_match_ids))
    final_match_ids_to_process = list(all_new_match_ids - existing_match_ids)
    # 테스트용으로 최대 200개만 처리
    final_match_ids_to_process = final_match_ids_to_process[:1000]  
    logger.info(f"Step 3: Filtering new matches finished in {time() - step_start_time:.2f}s")
    
    if not final_match_ids_to_process:
        logger.info("No new matches to process after filtering existing ones. Collection complete.")
        return

    logger.info(f"Found {len(final_match_ids_to_process)} new unique matches to process. (Sample Match ID: {final_match_ids_to_process[0]})")

    # 4. 새로운 매치 데이터 상세 정보 처리 및 저장 (Batching)
    all_participant_nicknames = set()
    raw_match_data_list = []
    
    step_start_time = time()
    match_data_generator = get_match_infos_async(final_match_ids_to_process)
    logger.info("Fetching raw match data...")
    async for match_id, raw_data in tqdm(match_data_generator, total=len(final_match_ids_to_process), desc="Fetching raw match data"):
        if raw_data and 'userGames' in raw_data:
            raw_match_data_list.append((match_id, raw_data))
            for user in raw_data['userGames']:
                all_participant_nicknames.add(user['nickname'])
    logger.info(f"Step 4: Fetching raw match data finished in {time() - step_start_time:.2f}s")

    # [수정] 모든 닉네임에 대해 한번만 API 호출
    step_start_time = time()
    logger.info(f"Fetching UID for {len(all_participant_nicknames)} unique participants...")
    all_user_infos = await get_users_by_nickname_async(list(all_participant_nicknames))
    nickname_to_uid_map = {user['nickname']: user['userId'] for user in all_user_infos}
    logger.info(f"Resolved {len(nickname_to_uid_map)} nicknames to UIDs.")
    logger.info(f"Step 5: Fetching UIDs for participants finished in {time() - step_start_time:.2f}s")
    
    # [추적 로그] UID 조회 실패한 닉네임 확인
    unresolved_nicknames = all_participant_nicknames - set(nickname_to_uid_map.keys())
    if unresolved_nicknames:
        logger.warning(f"Could not resolve UIDs for {len(unresolved_nicknames)} nicknames (e.g., {list(unresolved_nicknames)[:5]}). These are likely 'Not Found' (404) cases.")

    # [수정] 수집된 raw data를 순회하며 파싱 진행
    step_start_time = time()
    all_new_participants = []
    all_parsed_data = []

    logger.info("Parsing all matches with resolved user IDs...")
    for match_id, raw_data in tqdm(raw_match_data_list, desc="Processing and Saving Matches"):
        try:
            # 4-1. raw_data의 userGames에 'uid' 필드 추가
            valid_user_games = []
            for user_game in raw_data['userGames']:
                nickname = user_game['nickname']
                if nickname in nickname_to_uid_map:
                    user_game['uid'] = nickname_to_uid_map[nickname]
                    valid_user_games.append(user_game)

            raw_data['userGames'] = valid_user_games
            
            # 4-2. 스노우볼링을 위한 새로운 참여자 정보 수집
            for user_info in all_user_infos:
                 if any(u['nickname'] == user_info['nickname'] for u in raw_data['userGames']):
                    all_new_participants.append({'uid': user_info['userId'], 'nickname': user_info['nickname']})

            # 4-3. 나머지 데이터 파싱
            if raw_data['userGames']:
                parsed_data = parse_match_data(raw_data)
                all_parsed_data.append(parsed_data)
            
        except Exception as e:
            logger.error(f"Failed to process or save match {match_id}: {e}", exc_info=True)
    logger.info(f"Step 6: Parsing matches and resolving UIDs finished in {time() - step_start_time:.2f}s")

    # 5. 수집된 데이터 일괄 저장
    # 5-1. 스노우볼링으로 수집된 신규 유저 일괄 upsert
    step_start_time = time()
    if all_new_participants:
        unique_participants = list({p['uid']: p for p in all_new_participants}.values())
        
        # [추적 로그] 진짜 새로운 유저 확인
        truly_new_users = [p for p in unique_participants if p['nickname'] not in active_user_nicknames]
        if truly_new_users:
            logger.info(f"[DIAGNOSIS] Found {len(truly_new_users)} new users to be added. (Sample: {truly_new_users[0]['nickname']})")
        
        logger.info(f"Upserting {len(unique_participants)} participants into the database...")
        upsert_users(engine, unique_participants)
        logger.info("Upsert complete.")
    logger.info(f"Step 7: Upserting new users finished in {time() - step_start_time:.2f}s")


    # 5-2. 파싱된 매치 데이터 일괄 저장
    step_start_time = time()
    if all_parsed_data:
        logger.info(f"Saving data from {len(all_parsed_data)} matches to database...")
        combined_data = {}
        for parsed_data in all_parsed_data:
            for table_name, df in parsed_data.items():
                if table_name not in combined_data:
                    combined_data[table_name] = []
                combined_data[table_name].append(df)
        
        for table_name, df_list in combined_data.items():
            if df_list:
                combined_data[table_name] = pd.concat(df_list, ignore_index=True)

        save_dataframes_to_db(engine, combined_data)
        logger.info("Saving match data complete.")
    logger.info(f"Step 8: Saving match data finished in {time() - step_start_time:.2f}s")


    # 6. 각 유저의 last_match_id 갱신
    step_start_time = time()
    logger.info("Updating last_match_id for processed users...")
    for uid, matches in user_match_map.items():
        if matches:
            latest_match_id = max(matches)
            update_user_last_match(engine, uid, latest_match_id)
    logger.info("Update complete.")
    logger.info(f"Step 9: Updating last match IDs finished in {time() - step_start_time:.2f}s")

    elapsed_time = time() - pipeline_start_time
    logger.info(f"--- Data collection pipeline finished in {elapsed_time:.2f} seconds ---")


async def main():
    """command에 알맞는 파이프라인 함수를 실행합니다."""
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'seed':
            await seed_top_rankers()
        elif command == 'run':
            await run_pipeline()
        else:
            print(f"Unknown command: {command}. Use 'seed' or 'run'.")
    else:
        print("Please provide a command: 'seed' or 'run'.")


if __name__ == '__main__':
    asyncio.run(main())