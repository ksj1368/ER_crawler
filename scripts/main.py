from time import time
from multiprocessing import cpu_count
from parsing import top_ranker_id
from crawler import get_top_ranker
from utils import setup_logger, split_into_chunks, collect_data
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

if __name__ == "__main__":
    # logging
    LOG_DIR = os.getenv("log_path")
    logger = setup_logger(LOG_DIR)
    start_time = time()
    start_dt_str = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d_%H-%M-%S")
    
    users = get_top_ranker(season=31, matching_mode=3)
    #users = get_top_ranker(season=29, matching_mode=3)
    users, nicknames = top_ranker_id(users)
    user_chunks = split_into_chunks(users[:2], 100) # 100개씩 분할
    
    # 데이터 수집 실행
    # 각 chunk별로 collect_data 실행
    sum_success_count = 0
    sum_total_count = 0
    for idx, user_chunk in enumerate(user_chunks):
        logger.info(f"Processing user batch {idx+1}/{len(user_chunks)} ({len(user_chunk)} users)")
        success_count, total_count = collect_data(
            users=user_chunk,
            # main_version=45,
            main_version=46,
            batch_size=100,
            log_dir = LOG_DIR,
            start_date = start_dt_str
        )
        logger.info(f"Batch {idx+1} Summary: {success_count}/{total_count} matches processed successfully")
        sum_success_count += success_count
        sum_total_count += total_count
        
    # 처리 결과 요약
    elapsed_time = time() - start_time
    logger.info(f"Total Data collection completed in {elapsed_time:.2f} seconds")
    logger.info(f"Collection Summary: {sum_success_count}/{sum_total_count} matches processed successfully")