from dotenv import load_dotenv
import pymysql
import os

def check_db_folder():
    '''
    Check the folder to store the data exists.
    '''
    load_dotenv()
    db_folder = os.getenv("db_root")
    data_raw_folder = os.getenv("data_raw")
    data_proc_folder = os.getenv("data_proc")
    
    for folder in [db_folder, data_raw_folder, data_proc_folder]:
        if not os.path.exists(folder):
            print(f"'{folder}' does not exist. Creating now...")
            os.makedirs(folder)   
                 
def init_db():
    '''
    
    '''  
    load_dotenv()
    schema_path = os.getenv("schema_path")
    
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        #db=os.getenv("DB_NAME"),
        charset='utf8mb4',
        autocommit=True
    )
    
    cursor = conn.cursor()
    
    # Create database if not exists
    cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = 'ER_Dataset';")
    result = cursor.fetchone()

    if result:
        cursor.execute("DROP DATABASE ER_Dataset;")
        print("Existing database 'ER_Dataset' has been deleted. Creating a new database.")
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS ER_Dataset CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print("Database 'ER_Dataset' is ensured.")
        cursor.execute("USE ER_Dataset;")
    except Exception as e:
        print(f"[DB CREATE ERROR] → {e}")

    # Select the database to use
    try:
        cursor.execute(f"USE ER_Dataset;")
    except Exception as e:
        print(f"[DB USE ERROR] → {e}")
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_statements = f.read().split(';')
        
    for stmt in sql_statements:
        stmt = stmt.strip()
        if stmt:
            try:
                cursor.execute(stmt + ';')
            except Exception as e:
                print(f"[SQL ERROR] {stmt}\n→ {e}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_db_folder()
    init_db()