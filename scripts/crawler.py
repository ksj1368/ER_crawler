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
def get_character():

    character_url = f'https://open-api.bser.io/v2/data/Character'
    character_levelup_url = f'https://open-api.bser.io/v2/data/CharacterLevelUpStat'
    response_c = requests.get(character_url, headers=HEADERS_WITH_KEY)
    response_cl = requests.get(character_levelup_url, headers=HEADERS_WITH_KEY)
    if response_c.status_code == 200 and response_cl.status_code == 200:
        return response_c.json(), response_cl.json()
    else:
        print(f"[Error] get_character - status_code: {response_c.status_code}")
        print(f"[Error] get_character - status_code: {response_cl.status_code}")
        return None

def get_equipment():

    url_armor = f'https://open-api.bser.io/v2/data/ItemArmor'
    url_weapon = f'https://open-api.bser.io/v2/data/ItemWeapon'
    
    response_armor = requests.get(url_armor, headers=HEADERS_WITH_KEY)
    response_weapon = requests.get(url_weapon, headers=HEADERS_WITH_KEY)
    if response_armor.status_code == 200 and response_weapon.status_code == 200:
        return response_armor.json(), response_weapon.json()
    else:
        print(f"[Error] get_equipment armor - status_code: {response_armor.status_code}")
        print(f"[Error] get_equipment weapon - status_code: {response_weapon.status_code}")
        return None
    
def get_trait():

    url = f'https://open-api.bser.io/v2/data/Trait'
    
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[Error] get_trait - status_code: {response.status_code}")
        return None
def get_l10n():
    url = 'https://d1wkxvul68bth9.cloudfront.net/l10n/l10n-Korean-20250417055750.txt'
    response = requests.get(url, headers=HEADERS_WITH_KEY)
        
    if response.status_code == 200:
        response.encoding = response.apparent_encoding
        l10n = response.text
        return l10n
    else:
        print(f"[Error] get_trait - status_code: {response.status_code}")
        return None

    
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
