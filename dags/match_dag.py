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

# PythonOperator를 위한 비동기 실행 래퍼
def run_match_task():
    """비동기 매치 수집 프로세스 실행을 위한 래퍼"""
    from scripts.main import run_match_process
    asyncio.run(run_match_process())

with DAG(
    'eternal_return_match_v1',
    default_args=default_args,
    description='Eternal Return Match Data Collection Pipeline (Hourly)',
    schedule_interval='0 * * * *', # 매 시간 정각 실행
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['eternal_return', 'crawler', 'match'],
    max_active_runs=1
) as dag:

    t1_run_match_collection = PythonOperator(
        task_id='run_match_collection',
        python_callable=run_match_task,
        execution_timeout=timedelta(hours=1), # 시간 단위 실행이므로 타임아웃 1시간
    )
