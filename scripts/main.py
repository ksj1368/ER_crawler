from scripts.config import SEASON_ID, MAIN_VERSION
from scripts.crawler import get_l10n
from scripts.hash_info_parsing import parse_all_meta_files, weapon_type, tactical_type
from scripts.db_utils import get_engine, save_dataframes_to_db
from scripts.logger import logger
from scripts.pipeline import run_pipeline
import pandas as pd
from sqlalchemy.exc import ProgrammingError


def populate_static_tables():
    """
    Fetches game data (characters, items, etc.), parses it,
    and saves it to the database if the tables are empty.
    """
    logger.info("--- Checking for static data ---")
    engine = get_engine()

    try:
        with engine.connect() as conn:
            # Check if a key static table is populated. If so, skip.
            result = conn.execute("SELECT 1 FROM character_info LIMIT 1").fetchone()
            if result:
                logger.info("Static data table 'character_info' is already populated. Skipping population.")
                return
    except ProgrammingError:
        # This likely means the table doesn't exist yet, so we should proceed.
        logger.info("'character_info' table not found, proceeding with population.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while checking for static data: {e}")
        # Decide if we should stop or continue. For now, we'll try to continue.
        logger.warning("Proceeding with static data population despite the error.")


    logger.info("--- Starting Static Data Population ---")
    # 1. Fetching l10n data
    logger.info("Fetching l10n data...")
    l10n_data = get_l10n()
    if not l10n_data:
        logger.error("Failed to get l10n data. Aborting static data population.")
        return

    # 2. 모든 메타 파일 파싱
    logger.info("Parsing all meta files...")
    try:
        # Using versions from config.py. Assuming minor_version = 0
        meta_dataframes = parse_all_meta_files(l10n_data, season=SEASON_ID, major_version=MAIN_VERSION, minor_version=0)
        
        # Add weapon_type and tactical_type to the dataframes
        weapon_df = pd.DataFrame(list(weapon_type().items()), columns=['weapon_id', 'weapon_name'])
        meta_dataframes['weapon_types'] = weapon_df

        tactical_df = pd.DataFrame(list(tactical_type().items()), columns=['tactical_skill_id', 'tactical_skill_name'])
        meta_dataframes['tactical_skills'] = tactical_df

        logger.info(f"Parsed {len(meta_dataframes)} meta tables.")
    except Exception as e:
        logger.error(f"Failed to parse meta files: {e}", exc_info=True)
        return

    # 3. Saving data to DB
    logger.info("Saving meta data to database...")
    try:
        save_dataframes_to_db(engine, meta_dataframes)
        logger.info("Successfully saved all meta data to the database.")
    except Exception as e:
        logger.error(f"Failed to save meta data to DB: {e}", exc_info=True)


if __name__ == "__main__":
    # 1. Populate static data tables if they are empty
    populate_static_tables()
    
    # 2. Run the main pipeline for match data
    logger.info("--- Starting Match Data Collection Pipeline ---")
    run_pipeline()
