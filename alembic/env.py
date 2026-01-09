import os
import sys
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# ----------------------------------------------------------------------
# 1. Project Path & Modules Setup
# ----------------------------------------------------------------------
# 프로젝트 루트 경로를 sys.path에 추가하여 scripts 모듈을 인식할 수 있게 함
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# 로컬 설정 모듈 임포트
try:
    from scripts.config import DATABASE_URL
    from scripts.models import Base
except ImportError as e:
    print(f"ERROR: 모듈 임포트 실패. 프로젝트 경로 설정을 확인하세요.\nDetails: {e}")
    sys.exit(1)

# ----------------------------------------------------------------------
# 2. Alembic Config Setup
# ----------------------------------------------------------------------
config = context.config

# loggers 설정을 alembic.ini에서 읽어옴
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic 내부 로거 생성 (print 대신 사용)
logger = logging.getLogger("alembic.env")

# Model의 MetaData 연결
target_metadata = Base.metadata

# [Critical] alembic.ini의 sqlalchemy.url을 환경변수(DATABASE_URL)로 덮어씀
# 이를 통해 소스코드 내의 환경 설정을 따르도록 강제함
if not DATABASE_URL:
    logger.error("DATABASE_URL이 설정되지 않았습니다. .env 파일이나 환경 변수를 확인하세요.")
    sys.exit(1)

config.set_main_option("sqlalchemy.url", DATABASE_URL)


# ----------------------------------------------------------------------
# 3. Migration Logic (Offline & Online)
# ----------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Offline 모드 실행:
    DB 연결 없이 SQL 스크립트만 생성할 때 사용합니다. (--sql 옵션 사용 시)
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online 모드 실행:
    실제 DB에 연결하여 마이그레이션을 수행합니다.
    """
    # 현업 Tip: 마이그레이션 스크립트는 Connection Pool을 유지할 필요가 없음.
    # NullPool을 사용하여 연결을 맺고 작업이 끝나면 즉시 연결을 닫도록 설정.
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # [중요] 컬럼의 타입 변경(String 50 -> 100 등)을 감지
            compare_type=True,
            # [중요] Default 값의 변경을 감지
            compare_server_default=True,
            # (옵션) Foreign Key 제약 조건 이름을 렌더링 시 포함 (Batch 모드 등에서 유리)
            render_as_batch=False 
        )

        with context.begin_transaction():
            logger.info("Migrating database changes...")
            context.run_migrations()


# ----------------------------------------------------------------------
# 4. Execution Entry Point
# ----------------------------------------------------------------------
if context.is_offline_mode():
    logger.info("Running in OFFLINE mode")
    run_migrations_offline()
else:
    logger.info("Running in ONLINE mode")
    run_migrations_online()