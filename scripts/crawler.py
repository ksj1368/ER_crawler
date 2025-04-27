import os
import asyncio
import aiohttp
from dotenv import load_dotenv
import requests
from typing import List, Dict, Any
from functools import lru_cache
from tqdm import tqdm

# .env 파일에서 환경 변수 로드
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://open-api.bser.io"

HEADERS_WITH_KEY = {
    "accept": "application/json",
    "x-api-key": API_KEY
}

# 정적 데이터 캐싱
@lru_cache(maxsize=None)
def get_character():
    character_url = f'{BASE_URL}/v2/data/Character'
    character_levelup_url = f'{BASE_URL}/v2/data/CharacterLevelUpStat'
    response_c = requests.get(character_url, headers=HEADERS_WITH_KEY)
    response_cl = requests.get(character_levelup_url, headers=HEADERS_WITH_KEY)
    if response_c.status_code == 200 and response_cl.status_code == 200:
        return response_c.json(), response_cl.json()
    else:
        print(f"[Error] get_character - status_code: {response_c.status_code}")
        print(f"[Error] get_character - status_code: {response_cl.status_code}")
        return None

@lru_cache(maxsize=None)
def get_equipment():
    url_armor = f'{BASE_URL}/v2/data/ItemArmor'
    url_weapon = f'{BASE_URL}/v2/data/ItemWeapon'
    
    response_armor = requests.get(url_armor, headers=HEADERS_WITH_KEY)
    response_weapon = requests.get(url_weapon, headers=HEADERS_WITH_KEY)
    if response_armor.status_code == 200 and response_weapon.status_code == 200:
        return response_armor.json(), response_weapon.json()
    else:
        print(f"[Error] get_equipment armor - status_code: {response_armor.status_code}")
        print(f"[Error] get_equipment weapon - status_code: {response_weapon.status_code}")
        return None
    
@lru_cache(maxsize=None)
def get_trait() -> dict | None:
    """_summary_

    Returns:
        dict | None: _description_
    """
    url = f'{BASE_URL}/v2/data/Trait'
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[Error] get_trait - status_code: {response.status_code}")
        return None

@lru_cache(maxsize=None)
def get_l10n() -> str | None:
    """_summary_

    Returns:
        str | None: _description_
    """
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
    """특정 시즌, 지역, 매칭 모드에서의 상위 랭커 정보를 반환

    Args:
        season (int): 게임 시즌(예: 31 -> (7시즌), 32(7시즌 프리시즌))
        matching_mode (int): 게임 모드(1: 솔로, 2: 듀오, 3: 스쿼드)

    Returns:
         dict | None: 
        
    """
    url = f"{BASE_URL}/v1/rank/top/{season}/{matching_mode}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"[Error] get_top_ranker - status_code: {response.status_code}")
        return None

async def fetch_user_games(session, user_num: int) -> dict:
    """유저의 match 정보를 가져오는 함수

    Args:
        session (_type_): _description_
        user_num (_type_): _description_

    Returns:
        
    """
    url = f"{BASE_URL}/v1/user/games/{user_num}"
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"[Error] fetch_user_games - status_code: {response.status}")
            return None

async def get_match_ids_async(user_nums: List[int], main_version: int) -> List[int]:
    """비동기적으로 여러 사용자의 게임 ID를 수집합니다.
        각 사용자별로 수집 게임 수를 제한할 수 있습니다.

    Returns:
        _type_: _description_
    """
    match_ids_set = set()
    
    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        tasks = []
        for user_num in tqdm(user_nums):
            tasks.append(fetch_user_games(session, user_num))
        
        responses = await asyncio.gather(*tasks)
        for user_num, data in zip(user_nums, responses):
            while data and "userGames" in data:
                stop_crawling = False  # 중단 여부 플래그
                for game in data["userGames"]:
                    if game["versionMajor"] > main_version:
                        continue  # 그냥 무시하고 다음 게임
                    elif game["versionMajor"] == main_version:
                        if game["matchingMode"] == 3:
                            match_ids_set.add(game["gameId"])
                    else:  # game["versionMajor"] < main_version
                        stop_crawling = True
                        break  # 버전이 낮으면 바로 탐색 종료

                if stop_crawling or not data.get('next'):
                    break  # 크롤링 중단 또는 next 없으면 종료

                # 다음 페이지로 이동
                url = f"{BASE_URL}/v1/user/games/{user_num}?next={data['next']}"
                data = await fetch_user_games(session, url)

    return list(match_ids_set)

async def fetch_match_info(session, match_id):
    """비동기적으로 단일 게임 정보를 가져옵니다."""
    url = f"{BASE_URL}/v1/games/{match_id}"
    async with session.get(url) as response:
        if response.status == 200:
            return match_id, await response.json()
        else:
            print(f"[Error] fetch_match_info - match_id: {match_id}, status_code: {response.status}")
            return match_id, None

async def get_match_infos_async(match_ids: List[int], batch_size: int = 10) -> Dict[int, Any]:
    """
    비동기적으로 여러 게임의 정보를 배치 단위로 수집합니다.
    """
    result = {}
    
    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        # 배치 단위로 처리
        for i in range(0, len(match_ids), batch_size):
            batch = match_ids[i:i+batch_size]
            tasks = [fetch_match_info(session, match_id) for match_id in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for match_id, data in batch_results:
                if data:
                    result[match_id] = data
            
            # 배치 간 짧은 대기 시간 추가하여 API 서버 부하 방지
            if i + batch_size < len(match_ids):
                await asyncio.sleep(0.5)
    
    return result

def match_info(match_id: int) -> dict | None:
    """
    특정 게임 ID에 대한 상세 정보를 반환합니다.
    """
    url = f"{BASE_URL}/v1/games/{match_id}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"[Error] match_info - status_code: {response.status_code}")
        return None