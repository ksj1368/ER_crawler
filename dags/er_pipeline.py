from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import asyncio
import sys

# scripts 모듈을 임포트할 수 있도록 /opt/airflow를 sys.path에 추가
sys.path.append('/opt/airflow')

from scripts.main import run_full_process

# 기본 인자 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# PythonOperator를 위한 비동기 실행 래퍼
def run_task():
    """비동기 파이프라인 함수 실행을 위한 래퍼"""
    asyncio.run(run_full_process())

with DAG(
    'eternal_return_crawler_v1',
    default_args=default_args,
    description='Eternal Return Data Collection Pipeline',
    schedule_interval='0 * * * *', # 매일 정각에 실행
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['eternal_return', 'crawler', 'pipeline'],
    max_active_runs=1 # 동시에 하나의 DAG 실행만 허용
) as dag:

    t1_run_collection = PythonOperator(
        task_id='run_collection',
        python_callable=run_task,
        execution_timeout=timedelta(hours=12), # 데이터 양에 따라 유동적일 수 있으므로 넉넉하게 설정
    )
