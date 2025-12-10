import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
# 프로젝트 루트를 기준으로 .env 파일을 찾도록 경로 설정
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

# API Settings
API_KEY = os.getenv("API_KEY")

# Version Settings
SEASON_ID = int(os.getenv("season_id", 35))
MATCHING_MODE = int(os.getenv("matching_mode", 3))
MAIN_VERSION = int(os.getenv("main_version", 7)) # 7
REGION_ID = int(os.getenv("region_id", 10))

# Path Settings
CODE_ROOT = Path(os.getenv("code_root"))
LOG_PATH = CODE_ROOT / "logs"
SCHEMA_PATH = CODE_ROOT / "db" / "schema_season9.sql"
URL_JSON_PATH = CODE_ROOT / "config" / "urls.json"

# DB Settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME", "erdb")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# SQLAlchemy Connection URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Logging
LOG_PATH.mkdir(parents=True, exist_ok=True)