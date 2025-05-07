from datetime import datetime
import logging
import os
from time import time
from dotenv import load_dotenv


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