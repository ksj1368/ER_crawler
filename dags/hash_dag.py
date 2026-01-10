from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import asyncio
import sys

# scripts 모듈을 임포트할 수 있도록 /opt/airflow를 sys.path에 추가
sys.path.append('/opt/airflow')

# 기본 인자 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_hash_task():
    """정적 데이터 수집 프로세스 실행을 위한 래퍼"""
    from scripts.main import run_hash_process
    asyncio.run(run_hash_process())

with DAG(
    'eternal_return_hash_v1',
    default_args=default_args,
    description='장비, 실험체 능력치 등 정적 데이터 수집 및 해시 생성 DAG',
    schedule_interval='@once',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['eternal_return', 'crawler', 'hash', 'static'],
    max_active_runs=1
) as dag:

    t1_run_hash_collection = PythonOperator(
        task_id='run_hash_collection',
        python_callable=run_hash_task,
        execution_timeout=timedelta(minutes=10),
    )
