
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime
"""
시스템 초기화 및 DB 마이그레이션을 위한 DAG 정의
- 수동 실행 권장
"""
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
}

with DAG(
    'init_system',
    default_args=default_args,
    description='시스템 초기화 및 DB 마이그레이션 (수동 실행 권장)',
    schedule_interval='@once', 
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['system', 'maintenance', 'alembic'],
) as dag:

    # Alembic 마이그레이션 실행
    # Docker 환경에서 /opt/airflow가 프로젝트 루트이므로 cwd 설정
    t1_migrate_db = BashOperator(
        task_id='migrate_db',
        bash_command='alembic upgrade head',
        cwd='/opt/airflow', 
    )
