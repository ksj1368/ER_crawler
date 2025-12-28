from sqlalchemy import text
from scripts.db_utils import get_engine

def verify_data():
    engine = get_engine()
    tables = [
        "match_info", "match_team_info", "match_user_start", 
        "match_user_combat", "match_user_damage", 
        "match_user_credit_acquisitions", "match_user_credit_expenditures"
    ]
    
    with engine.connect() as conn:
        print(f"{'Table Name':<35} | {'Row Count':<10}")
        print("-" * 50)
        for table in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"{table:<35} | {count:<10}")

if __name__ == "__main__":
    verify_data()
