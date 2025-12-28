from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import asyncio
import sys

# scripts 모듈을 임포트할 수 있도록 /opt/airflow를 sys.path에 추가
sys.path.append('/opt/airflow')

from scripts.pipeline import seed_top_rankers, run_pipeline
from scripts.verify_storage import verify_data
from scripts.db_utils import get_engine
from sqlalchemy import text

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# PythonOperator를 위한 비동기 실행
def run_async_task(async_func):
    asyncio.run(async_func())

def check_db_connection():
    """MySQL 데이터베이스 연결 가능 여부 확인"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        if result != 1:
            raise Exception("Database connection failed")
        print("Database connection successful")

def run_seed_task():
    """비동기 seed 함수 실행"""
    asyncio.run(seed_top_rankers())

def run_pipeline_task():
    """비동기 파이프라인 함수 실행"""
    asyncio.run(run_pipeline())

def run_verify_task():
    """데이터 검증 함수 실행"""
    verify_data()

with DAG(
    'eternal_return_crawler_v1',
    default_args=default_args,
    description='Eternal Return Data Collection Pipeline',
    schedule_interval='0 4 * * *', # 매일 새벽 4시에 실행
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['eternal_return', 'crawler'],
) as dag:

    t1_check_db = PythonOperator(
        task_id='check_db_connection',
        python_callable=check_db_connection,
    )

    t2_migrate_db = BashOperator(
        task_id='migrate_db',
        bash_command='alembic upgrade head',
        cwd='/opt/airflow', # alembic.ini가 위치한 프로젝트 루트에서 실행
    )

    t3_seed_rankers = PythonOperator(
        task_id='seed_top_rankers',
        python_callable=run_seed_task,
    )

    t4_run_pipeline = PythonOperator(
        task_id='run_crawler_pipeline',
        python_callable=run_pipeline_task,
        execution_timeout=timedelta(hours=2), # 2시간 이상 실행될 경우 실패 처리
    )

    t5_verify_data = PythonOperator(
        task_id='verify_data_storage',
        python_callable=run_verify_task,
    )

    # 작업 의존성 설정
    t1_check_db >> t2_migrate_db >> t3_seed_rankers >> t4_run_pipeline >> t5_verify_data