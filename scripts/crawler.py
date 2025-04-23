import os
from dotenv import load_dotenv
import requests

# .env 파일에서 환경 변수 로드
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://open-api.bser.io/v1"


HEADERS_WITH_KEY = {
    "accept": "application/json",
    "x-api-key": API_KEY
}


def get_top_ranker(season: int, matching_mode: int) -> dict | None:
    """
    특정 시즌, 지역, 매칭 모드에서의 상위 랭커 정보를 반환합니다.
    """
    url = f"{BASE_URL}/rank/top/{season}/{matching_mode}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"[Error] get_top_ranker - status_code: {response.status_code}")
        return None


def get_match_id(match_ids: list, user_num: int, main_version: int) -> list:
    """
    사용자의 게임 기록 중, 특정 메이저 버전에 해당하고 랭크 모드(3)인 게임 ID를 수집합니다.
    """
    url = f"{BASE_URL}/user/games/{user_num}"
    while url:
        response = requests.get(url, headers=HEADERS_WITH_KEY)
        if response.status_code == 200:
            data = response.json()
            for game in data.get("userGames", []):
                if game["versionMajor"] == main_version:
                    if game["matchingMode"] == 3 and game["gameId"] not in match_ids:
                        match_ids.append(game["gameId"])
                elif game["versionMajor"] < main_version:
                    print(game["versionMajor"])
                    return match_ids
            if url and data.get('next'):
                url = f"{BASE_URL}/user/games/{user_num}?next={data['next']}"
        else:
            print(f"[Error] get_match_id - status_code: {response.status_code}")
    return match_ids


def match_info(match_id: int) -> dict | None:
    """
    특정 게임 ID에 대한 상세 정보를 반환합니다.
    """
    url = f"{BASE_URL}/games/{match_id}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"[Error] match_info - status_code: {response.status_code}")
        return None
