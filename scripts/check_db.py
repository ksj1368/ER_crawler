from sqlalchemy import text
from scripts.db_utils import get_engine

def check_counts():
    engine = get_engine()
    with engine.connect() as conn:
        user_count = conn.execute(text("SELECT COUNT(*) FROM user")).scalar()
        active_user_count = conn.execute(text("SELECT COUNT(*) FROM user WHERE is_active = TRUE")).scalar()
        match_count = conn.execute(text("SELECT COUNT(*) FROM match_info")).scalar()
        
        print(f"--- Database Statistics ---")
        print(f"Total users: {user_count}")
        print(f"Active users: {active_user_count}")
        print(f"Total matches: {match_count}")

if __name__ == "__main__":
    check_counts()
