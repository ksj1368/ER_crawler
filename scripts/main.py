import asyncio
from scripts.config import SEASON_ID, MAIN_VERSION
from scripts.crawler import get_l10n
from scripts.hash_info_parsing import parse_all_meta_files, weapon_type, tactical_type
from scripts.db_utils import get_engine, save_dataframes_to_db
from scripts.logger import logger
from scripts import pipeline 
import pandas as pd
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import text


def populate_static_tables():
    """
    게임 정적 데이터(캐릭터, 아이템 등)를 가져와 파싱하고 테이블이 비어있는 경우 DB에 저장
    """
    logger.info("--- Checking for static data ---")
    engine = get_engine()

    try:
        with engine.connect() as conn:
            # 주요 정적 테이블에 데이터가 있는지 확인하고, 있으면 생략
            result = conn.execute(text("SELECT 1 FROM character_info LIMIT 1")).fetchone()
            if result:
                logger.info("Static data table 'character_info' is already populated. Skipping population.")
                return
    except ProgrammingError:
        # 테이블이 아직 존재하지 않음
        logger.info("'character_info' table not found, proceeding with population.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while checking for static data: {e}")
        # 계속 수집 진행
        logger.warning("Proceeding with static data population despite the error.")


    logger.info("--- Starting Static Data Population ---")
    # 1. l10n 데이터 가져오기
    logger.info("Fetching l10n data...")
    l10n_data = get_l10n()
    if not l10n_data:
        logger.error("Failed to get l10n data. Aborting static data population.")
        return

    # 2. 모든 메타 파일 파싱하기
    logger.info("Parsing all meta files...")
    try:
        # config.py의 버전을 사용 minor_version은 0으로 고정
        meta_dataframes = parse_all_meta_files(l10n_data, season=SEASON_ID, major_version=MAIN_VERSION, minor_version=0)
        
        # weapon_type과 tactical_type을 데이터프레임에 추가
        weapon_df = pd.DataFrame(list(weapon_type().items()), columns=['weapon_id', 'weapon_name'])
        meta_dataframes['weapon_types'] = weapon_df

        tactical_df = pd.DataFrame(list(tactical_type().items()), columns=['tactical_skill_id', 'tactical_skill_name'])
        meta_dataframes['tactical_skills'] = tactical_df

        logger.info(f"Parsed {len(meta_dataframes)} meta tables.")
    except Exception as e:
        logger.error(f"Failed to parse meta files: {e}", exc_info=True)
        return

    # 3. DB에 데이터 저장하기
    logger.info("Saving meta data to database...")
    try:
        save_dataframes_to_db(engine, meta_dataframes)
        logger.info("Successfully saved all meta data to the database.")
    except Exception as e:
        logger.error(f"Failed to save meta data to DB: {e}", exc_info=True)


if __name__ == "__main__":
    # 1. 정적 데이터 테이블이 비어있으면 채우기
    populate_static_tables()
    
    # 2. pipeline.py에 위임하여 매치 데이터 수집을 위한 메인 파이프라인을 실행
    logger.info("--- Starting Match Data Collection ---")
    logger.info("Delegating to pipeline.py. Use 'seed' or 'run' as a command-line argument.")
    
    # pipeline.main() 함수는 자체적으로 커맨드 라인 인자('seed' 또는 'run')를 처리
    asyncio.run(pipeline.main())
