import asyncio
import os
from time import time
from typing import List

import pandas as pd
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from scripts.config import SEASON_ID, MATCHING_MODE, MAIN_VERSION, REGION_ID
from scripts.crawler import get_top_ranker, get_match_ids_async, get_match_infos_async
from scripts.db_utils import get_engine, check_match_exists, save_dataframes_to_db
from scripts.match_info_parsing import top_ranker_id, parse_match_data
from scripts.logger import logger

async def test_pipeline(num_matches: int = 10, output_dir: str = "test_results"):
    """
    테스트용 파이프라인: 지정된 수의 매치 데이터를 수집하여 파일로 저장합니다.
    """
    logger.info(f"--- Starting Test Pipeline for {num_matches} matches ---")
    
    # 1. 상위 랭커 유저 목록 가져오기 (테스트를 위해 일부 유저만 사용)
    users_json = get_top_ranker(season=SEASON_ID, matching_mode=MATCHING_MODE, region=REGION_ID)
    if not users_json:
        logger.error("Failed to get top rankers for test. Exiting.")
        return
    user_ids, _ = top_ranker_id(users_json)
    
    # 2. 매치 ID 수집(10명)
    logger.info("Collecting match IDs for test...")
    match_ids = await get_match_ids_async(user_ids[:10], MAIN_VERSION)
    
    if not match_ids:
        logger.warning("No matches found for test run.")
        return

    test_match_ids = match_ids[:num_matches]
    logger.info(f"Processing {len(test_match_ids)} matches for test.")

    # 3. 매치 데이터 가져오기 및 파싱
    match_data_generator = get_match_infos_async(test_match_ids)
    
    all_parsed_data = []
    async for match_id, raw_data in tqdm(match_data_generator, total=len(test_match_ids), desc="Parsing test matches"):
        if raw_data:
            try:
                parsed_data = parse_match_data(raw_data)
                all_parsed_data.append(parsed_data)
            except Exception as e:
                logger.error(f"Failed to parse match {match_id}: {e}", exc_info=True)

    # 4. 결과 데이터프레임 병합 및 파일로 저장
    if not all_parsed_data:
        logger.info("No data was parsed.")
        return

    final_dfs = {}
    for parsed_data in all_parsed_data:
        for table_name, df in parsed_data.items():
            if table_name not in final_dfs:
                final_dfs[table_name] = []
            final_dfs[table_name].append(df)

    for table_name, dfs in final_dfs.items():
        if dfs:
            final_df = pd.concat(dfs, ignore_index=True)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{table_name}.csv")
            final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"Saved {len(final_df)} records to {output_path}")

    logger.info(f"--- Test Pipeline Finished ---")
    
async def process_matches_in_batches(match_ids: List[int], batch_size: int):
    """매치 데이터를 비동기적으로 가져와 배치 단위로 처리하고 DB에 저장합니다."""
    engine = get_engine()
    
    total_matches_to_process = len(match_ids)
    fetch_success_count = 0
    parse_success_count = 0
    db_saved_count = 0

    match_info_generator = get_match_infos_async(match_ids)
    
    batch_to_save = []
    
    async for match_id, raw_data in tqdm(match_info_generator, total=total_matches_to_process, desc="Processing matches"):
        if not raw_data:
            continue
        
        fetch_success_count += 1
        
        try:
            parsed_data = parse_match_data(raw_data)
            batch_to_save.append(parsed_data)
            parse_success_count += 1
        except Exception as e:
            logger.error(f"Failed to parse match {match_id}: {e}", exc_info=True)
            continue

        if len(batch_to_save) >= batch_size:
            combined_dfs = {}
            for item in batch_to_save:
                for table_name, df in item.items():
                    if table_name not in combined_dfs:
                        combined_dfs[table_name] = []
                    combined_dfs[table_name].append(df)
            
            for table_name, dfs in combined_dfs.items():
                if dfs:
                    combined_dfs[table_name] = pd.concat(dfs, ignore_index=True)
            
            try:
                # 저장 직전에 어떤 match_id들이 포함되어 있는지 확인
                if 'match_info' in combined_dfs and not combined_dfs['match_info'].empty:
                    batch_match_ids = combined_dfs['match_info']['match_id'].unique().tolist()
                    logger.info(f"Attempting to save batch with match_ids: {batch_match_ids}")

                save_dataframes_to_db(engine, combined_dfs)
                db_saved_count += len(batch_to_save)
            except Exception as e:
                logger.error(f"Failed to save batch to DB: {e}", exc_info=True)
                
                # 오류 발생 시, 어떤 데이터가 문제 탐색
                logger.error("--- STARTING INTEGRITY DEBUG ---")
                parent_df = combined_dfs.get('match_user_start')
                child_df = combined_dfs.get('match_user_end')

                if parent_df is not None and child_df is not None:
                    # 부모와 자식 테이블의 키를 set으로 생성
                    parent_keys = set(tuple(x) for x in parent_df[['match_id', 'user_id']].to_numpy())
                    child_keys = set(tuple(x) for x in child_df[['match_id', 'user_id']].to_numpy())                    
                    orphan_keys = child_keys - parent_keys
                    
                    if orphan_keys:
                        logger.error(f"Found {len(orphan_keys)} orphan rows in 'match_user_end'.")
                        for i, key in enumerate(list(orphan_keys)[:5]):
                            logger.error(f"  Orphan Key {i+1}: match_id={key[0]}, user_id={key[1]}")
                    else:
                        logger.error("No orphan keys found, there might be another issue.")
                logger.error("--- ENDING INTEGRITY DEBUG ---")
            
            batch_to_save = []

    # 마지막 남은 배치 처리
    if batch_to_save:
        combined_dfs = {}
        for item in batch_to_save:
            for table_name, df in item.items():
                if table_name not in combined_dfs:
                    combined_dfs[table_name] = []
                combined_dfs[table_name].append(df)
        
        for table_name, dfs in combined_dfs.items():
            if dfs:
                combined_dfs[table_name] = pd.concat(dfs, ignore_index=True)
        
        try:
            save_dataframes_to_db(engine, combined_dfs)
            db_saved_count += len(batch_to_save)
        except Exception as e:
            logger.error(f"Failed to save final batch to DB: {e}", exc_info=True)

    return {
        "total": total_matches_to_process,
        "fetch_success": fetch_success_count,
        "parse_success": parse_success_count,
        "db_saved": db_saved_count
    }

def run_pipeline():
    """전체 데이터 수집 및 처리 파이프라인 실행"""
    load_dotenv()
    start_time = time()
    
    logger.info("Starting data collection pipeline.")
    engine = get_engine()

    # 1. 상위 랭커 유저 목록 가져오기
    users_json = get_top_ranker(season=SEASON_ID, matching_mode=MATCHING_MODE, region=REGION_ID)
    if not users_json:
        logger.error("Failed to get top rankers. Exiting.")
        return
    user_ids, _ = top_ranker_id(users_json)
    
    # 2. API로부터 모든 매치 ID 수집
    logger.info(f"Collecting all match IDs for {len(user_ids)} users...")
    all_match_ids = asyncio.run(get_match_ids_async(user_ids, MAIN_VERSION))
    
    # 3. DB에 이미 존재하는 매치 ID 확인
    logger.info(f"Checking for existing matches in the database...")
    existing_match_ids = check_match_exists(engine, all_match_ids)
    new_match_ids = list(set(all_match_ids) - existing_match_ids)
    logger.info(f"Found {len(new_match_ids)} new match IDs to process.")

    if not new_match_ids:
        logger.info("No new matches to process. Collection complete.")
        return

    # 4. 새로운 매치 데이터 처리 및 저장
    stats = asyncio.run(process_matches_in_batches(new_match_ids, batch_size=100))
    
    elapsed_time = time() - start_time
    logger.info(f"Total data collection completed in {elapsed_time:.2f} seconds")
    
    total_matches = stats['total']
    fetch_success = stats['fetch_success']
    fetch_failed = total_matches - fetch_success
    parse_success = stats['parse_success']
    parse_failed = fetch_success - parse_success
    db_saved = stats['db_saved']
    db_failed = parse_success - db_saved

    logger.info("--- Crawling Summary ---")
    logger.info(f"Total new matches to process: {total_matches}")
    logger.info(f"API Fetch: {fetch_success} succeeded, {fetch_failed} failed.")
    logger.info(f"Data Parsing: {parse_success} succeeded, {parse_failed} failed.")
    logger.info(f"Database Save: {db_saved} processed, {db_failed} failed.")
    logger.info("------------------------")

if __name__ == '__main__':
    run_pipeline()