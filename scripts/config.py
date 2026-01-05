import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
# 프로젝트 루트를 기준으로 .env 파일을 찾도록 경로 설정
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

# API Settings
API_KEY = os.getenv("API_KEY")

# Environment Settings
ENV = os.getenv("ENV", "dev")  # dev, prod

# AWS Settings (for prod)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# Version Settings
SEASON_ID = int(os.getenv("season_id", 35))
MATCHING_MODE = int(os.getenv("matching_mode", 3))
MAIN_VERSION = int(os.getenv("main_version", 7)) # 7
REGION_ID = int(os.getenv("region_id", 10))

# Path Settings
CODE_ROOT = Path(os.getenv("CODE_ROOT", os.getcwd()))
LOG_PATH = CODE_ROOT / "logs"
SCHEMA_PATH = CODE_ROOT / "db" / "schema_season9.sql"
URL_JSON_PATH = CODE_ROOT / "config" / "urls.json"
MAPPING_ROOT = CODE_ROOT / "scripts" / "mappings"
CREDIT_ACQUISITIONS_PATH = MAPPING_ROOT / "credit_acquisitions.json"
CREDIT_EXPENDITURES_PATH = MAPPING_ROOT / "credit_expenditures.json"
OBJECT_METRICS_PATH = MAPPING_ROOT / "object_metrics.json"
GAME_METADATA_PATH = MAPPING_ROOT / "game_metadata.json"

# DB Settings
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME", "erdb")

if ENV == "prod":
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # Production 환경 필수 변수 검증
    if not all([DB_HOST, DB_USER, DB_PASSWORD]):
        missing = [k for k, v in {"DB_HOST": DB_HOST, "DB_USER": DB_USER, "DB_PASSWORD": DB_PASSWORD}.items() if not v]
        raise EnvironmentError(f"Production database credentials ({', '.join(missing)}) must be set in environment variables.")
else:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

# SQLAlchemy Connection URL
if DB_USER and DB_PASSWORD and DB_HOST:
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
else:
    # URL이 생성되지 않을 경우
    DATABASE_URL = None
    if ENV == "prod":
         raise EnvironmentError("Failed to generate DATABASE_URL. Check DB settings.")

# Tuning Configuration
DB_CHUNK_SIZE = int(os.getenv("DB_CHUNK_SIZE", 5000))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 20))

# API Configuration

# Logging
LOG_PATH.mkdir(parents=True, exist_ok=True)