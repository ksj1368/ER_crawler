import mysql.connector
from config_loader import load_config

def init_db():
    cfg = load_config()
    schema_path = cfg['db']['schema_path']
    conn = mysql.connector.connect(
        host=cfg['db']['host'],
        port=cfg['db']['port'],
        user=cfg['db']['user'],
        password=cfg['db']['password'],
        database=cfg['db']['database']
    )
    cursor = conn.cursor()
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_statements = f.read().split(';')
    for stmt in sql_statements:
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt + ';')
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_db()