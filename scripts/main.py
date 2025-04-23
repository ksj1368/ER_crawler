from parser import parse_match_data, top_ranker_id
from crawler import get_top_ranker, get_match_id, match_info
import json
from tqdm import tqdm


if __name__ == "__main__":
    # Load JSON data from file
    """
    with open("C:/Users/JSJ/ER_National_League/data/test/match_47425185_v145.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    """
    users = get_top_ranker(season = 31, matching_mode = 3)
    users = top_ranker_id(users)
    print(len(users))

    match_ids = []
    for u in tqdm(users[:3]):
        match_ids = get_match_id(match_ids, u, 44)
    print("A",len(match_ids))
    for match_id in tqdm(match_ids):
        
        parsed_data = parse_match_data(match_info(match_id))
        # parsed_data.items()에서 각 아이템을 DB에 옮기는 코드
    """# Parse all match data
    parsed_data = parse_match_data(data)
    
    # Print summary
    for table_name, table_data in parsed_data.items():
        if isinstance(table_data, list):
            print(f"{table_name}: {len(table_data)} records")
        else:
            print(f"{table_name}: 1 record")"""