import pymysql
from dbutils.pooled_db import PooledDB
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

pool = PooledDB(
    creator=pymysql,
    maxconnections=10,        # 최대 커넥션 수
    mincached=2,              # 시작 시 초기 커넥션 수
    blocking=True,            # 커넥션 부족 시 대기
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    charset='utf8mb4',
    autocommit=True
)
def get_db_connection():
    """커넥션 풀에서 커넥션 하나 반환"""
    return pool.connection()

def match_exists(conn, match_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM match_info WHERE match_id = %s LIMIT 1;", (match_id,))
        return cursor.fetchone() is not None

def insert_dict(conn, table, data):
    with conn.cursor() as cursor:
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({values});"
        cursor.execute(sql, tuple(data.values()))

def insert_list(conn, table, data_list):
    if not data_list:
        return
    for data in data_list:
        insert_dict(conn, table, data)