import asyncio
import aiohttp
import argparse
from scripts.config import SEASON_ID, MAIN_VERSION
from scripts.crawler import ERAPIClient
from scripts.hash_info_parsing import parse_all_meta_files, weapon_type, tactical_type
from scripts.db_utils import get_engine, save_data_to_db
from scripts.logger import logger
from scripts.pipeline import run_pipeline, seed_top_rankers
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import text


async def populate_static_tables(client: ERAPIClient):
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
    # l10n 데이터 가져오기
    logger.info("Fetching l10n data...")
    l10n_data = await client.get_l10n()
    if not l10n_data:
        logger.error("Failed to get l10n data. Aborting static data population.")
        return

    # 모든 메타 데이터 파싱
    logger.info("Parsing all meta files...")
    try:
        # config.py의 버전을 사용 minor_version은 0으로 고정
        meta_data = await parse_all_meta_files(client, l10n_data, season=SEASON_ID, major_version=MAIN_VERSION, minor_version=0)
        
        # weapon_type과 tactical_type을 리스트 딕셔너리로 변환하여 추가
        meta_data['weapon_types'] = [{'weapon_id': k, 'weapon_name': v} for k, v in weapon_type().items()]
        meta_data['tactical_skills'] = [{'tactical_skill_id': k, 'tactical_skill_name': v} for k, v in tactical_type().items()]

        logger.info(f"Parsed {len(meta_data)} meta tables.")
    except Exception as e:
        logger.error(f"Failed to parse meta files: {e}", exc_info=True)
        return

    # DB에 수집 데이터 저장하기
    logger.info("Saving meta data to database...")
    try:
        save_data_to_db(engine, meta_data)
        logger.info("Successfully saved all meta data to the database.")
    except Exception as e:
        logger.error(f"Failed to save meta data to DB: {e}", exc_info=True)


async def run_full_process():
    """
    전체 수집 프로세스 실행
    1. 정적 데이터(메타 데이터) 확인 및 보충
    2. 메인 파이프라인(매치 데이터 수집) 실행
    """
    async with ERAPIClient() as client:
        # 정적 데이터 테이블이 비어있으면 채우기
        await populate_static_tables(client)
        
    logger.info("--- Starting Match Data Collection ---")
    await run_pipeline()


async def main():
    parser = argparse.ArgumentParser(description="Eternal Return Data Crawler")
    parser.add_argument("command", choices=["run", "seed"], default="run", nargs="?", help="Command to execute: 'run' for full pipeline, 'seed' for top rankers only.")
    args = parser.parse_args()

    if args.command == "seed":
        await seed_top_rankers()
    elif args.command == "run":
        await run_full_process()

if __name__ == "__main__":
    asyncio.run(main())