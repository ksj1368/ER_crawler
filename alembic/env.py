import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__)))) # scripts 모듈을 찾을 수 있도록 경로 추가

from logging.config import fileConfig
from alembic import context
from scripts.config import DATABASE_URL
from scripts.models import Base # 모델의 메타데이터를 포함

config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic이 비교할 메타데이터 설정
target_metadata = Base.metadata # Alembic이 모델과 DB의 차이를 비교
config.set_main_option("sqlalchemy.url", DATABASE_URL)