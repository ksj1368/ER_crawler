import os
import asyncio
import aiohttp
import random
from dotenv import load_dotenv
import requests
import json
from typing import List, Dict, Any, AsyncGenerator, Tuple
from functools import lru_cache
from tqdm import tqdm
from aiolimiter import AsyncLimiter
from scripts.logger import logger
from scripts.config import URL_JSON_PATH

# .env 파일에서 환경 변수 로드
load_dotenv()

API_KEY = os.getenv("API_KEY")

# URL 로드
with open(URL_JSON_PATH) as f:
    URLS = json.load(f)

BASE_URL = URLS['base_url']

HEADERS_WITH_KEY = {
    "accept": "application/json",
    "x-api-key": API_KEY
}

# 정적 데이터 캐싱
@lru_cache(maxsize=None)
def get_character():
    character_url = f"{BASE_URL}{URLS['data']['character']}"
    character_levelup_url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"
    response_c = requests.get(character_url, headers=HEADERS_WITH_KEY)
    response_cl = requests.get(character_levelup_url, headers=HEADERS_WITH_KEY)
    if response_c.status_code == 200 and response_cl.status_code == 200:
        return response_c.json(), response_cl.json()
    else:
        logger.error(f"get_character - status_code: {response_c.status_code}")
        logger.error(f"get_character - status_code: {response_cl.status_code}")
        return None

@lru_cache(maxsize=None)
def get_equipment():
    url_armor = f"{BASE_URL}{URLS['data']['item_armor']}"
    url_weapon = f"{BASE_URL}{URLS['data']['item_weapon']}"
    
    response_armor = requests.get(url_armor, headers=HEADERS_WITH_KEY)
    response_weapon = requests.get(url_weapon, headers=HEADERS_WITH_KEY)
    if response_armor.status_code == 200 and response_weapon.status_code == 200:
        return response_armor.json(), response_weapon.json()
    else:
        logger.error(f"get_equipment armor - status_code: {response_armor.status_code}")
        logger.error(f"get_equipment weapon - status_code: {response_weapon.status_code}")
        return None
    
@lru_cache(maxsize=None)
def get_trait() -> dict | None:
    url = f"{BASE_URL}{URLS['data']['trait']}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"get_trait - status_code: {response.status_code}")
        return None
    
@lru_cache(maxsize=None)
def get_monster() -> dict | None:
    url = f"{BASE_URL}{URLS['data']['monster']}"    
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"get_monster - status_code: {response.status_code}")
        return None
    
@lru_cache(maxsize=None)
def get_area() -> dict | None:
    url = f"{BASE_URL}{URLS['data']['area']}"    
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"get_area - status_code: {response.status_code}")
        return None
        
@lru_cache(maxsize=None)
def get_char_lv() -> dict | None:
    url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"    
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"get_char_lv - status_code: {response.status_code}")
        return None

@lru_cache(maxsize=None)
def get_l10n() -> str | None:
    url = f"{BASE_URL}{URLS['l10n']['korean']}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    if response.status_code == 200:
        response.encoding = response.apparent_encoding
        l10n = response.json()
        l10n_url = l10n['data']["l10Path"]
        
        response = requests.get(l10n_url, headers=HEADERS_WITH_KEY)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            l10n = response.text.splitlines()
            return l10n
        else:
            logger.error((f"get ln10n text file - status_code: {response.status_code}"))
    else:
        logger.error(f"get_l10n - status_code: {response.status_code}")
        return None

def get_top_ranker(season: int, region: int, matching_mode: int) -> dict | None:
    """특정 시즌, 지역, 매칭 모드에서의 상위 랭커 정보를 반환

    Args:
        season (int): 게임 시즌(예: 31: 7시즌, 32: 7시즌 프리시즌)
        region (int): 게임 서버 코드(10: asia(kr), 17: asia2(cn), 12: NorthAmerica)
        matching_mode (int): 게임 모드(1: 솔로, 2: 듀오, 3: 스쿼드)

    Returns:
         dict | None: 
        
    """
    url = f"{BASE_URL}/v1/rank/top/{season}/{matching_mode}/{region}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)
    
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"get_top_ranker - status_code: {response.status_code}")
        return None

async def fetch_user_games(session, url: str, limiter: AsyncLimiter, max_retries: int = 5, delay: int = 1) -> dict:
    """유저의 match 정보를 가져오는 함수

    Args:
        session (_type_): aiohttp client session
        url (str): url to fetch
        limiter (AsyncLimiter): API 호출 빈도를 제어합니다.
        max_retries (int): maximum number of retries
        delay (int): delay between retries in seconds

    Returns:
        dict: _description_
    """
    for attempt in range(max_retries):
        async with limiter:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                
                retry_delay = delay + random.uniform(0, 1)
                logger.warning(f"fetch_user_games - status_code: {response.status}. Retrying in {retry_delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")

        await asyncio.sleep(retry_delay)

    logger.error(f"fetch_user_games - Failed to fetch after {max_retries} attempts for url: {url}")
    return None

async def get_match_ids_async(user_ids: List[int], main_version: int) -> List[int]:
    """비동기적으로 여러 사용자의 게임 ID를 수집합니다.
    aiolimiter를 사용하여 API 호출 빈도를 제어합니다.
    """
    match_ids_set = set()
    limiter = AsyncLimiter(50, 1)
    failed_urls = []

    async def process_user(session, user_id):
        """한 명의 유저에 대한 모든 매치 기록을 페이지네이션하며 수집합니다."""
        next_page = None
        while True:
            url = f"{BASE_URL}/v1/user/games/{user_id}"
            if next_page:
                url += f"?next={next_page}"

            data = await fetch_user_games(session, url, limiter)
            
            if not data or "userGames" not in data:
                failed_urls.append(url)
                break

            stop_crawling = False
            for game in data["userGames"]:
                if game["versionMajor"] > main_version:
                    continue
                elif game["versionMajor"] == main_version:
                    if game["matchingMode"] == 3:
                        match_ids_set.add(game["gameId"])
                else:
                    stop_crawling = True
                    break
            
            if stop_crawling or not data.get('next'):
                break
            
            next_page = data['next']

    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        tasks = [process_user(session, user_id) for user_id in user_ids]
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching user games"):
            await f

        if failed_urls:
            logger.info(f"Retrying {len(failed_urls)} failed URLs...")
            
            async def process_failed_url(session, url):
                current_url = url
                while current_url:
                    data = await fetch_user_games(session, current_url, limiter)

                    if not data or "userGames" not in data:
                        logger.warning(f"Failed to fetch retried URL: {current_url}")
                        break

                    stop_crawling = False
                    for game in data["userGames"]:
                        if game["versionMajor"] > main_version:
                            continue
                        elif game["versionMajor"] == main_version:
                            if game["matchingMode"] == 3:
                                match_ids_set.add(game["gameId"])
                        else:
                            stop_crawling = True
                            break
                    
                    if stop_crawling or not data.get('next'):
                        break
                    
                    base_user_url = current_url.split('?')[0]
                    current_url = f"{base_user_url}?next={data['next']}"

            retry_tasks = [process_failed_url(session, url) for url in failed_urls]
            for f in tqdm(asyncio.as_completed(retry_tasks), total=len(retry_tasks), desc="Retrying failed URLs"):
                await f

    return list(match_ids_set)

async def fetch_match_info(session, match_id, limiter: AsyncLimiter, max_retries: int = 3, delay: int = 1):
    """비동기적으로 단일 게임 정보를 가져옵니다."""
    url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
    for attempt in range(max_retries):
        async with limiter:
            async with session.get(url) as response:
                if response.status == 200:
                    return match_id, await response.json()
                
                retry_delay = delay + random.uniform(0, 1)
                logger.warning(f"fetch_match_info - match_id: {match_id}, status_code: {response.status}. Retrying in {retry_delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")
        
        await asyncio.sleep(retry_delay)

    logger.error(f"fetch_match_info - Failed to fetch match {match_id} after {max_retries} attempts.")
    return match_id, None

async def get_match_infos_async(match_ids: List[int], batch_size: int = 100) -> AsyncGenerator[Tuple[int, Any], None]:
    """
    비동기적으로 여러 게임의 정보를 수집하고 yield합니다.
    aiolimiter를 사용하여 API 호출 빈도를 제어합니다.
    """
    limiter = AsyncLimiter(50, 1)
    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        for i in range(0, len(match_ids), batch_size):
            batch = match_ids[i:i + batch_size]
            tasks = [fetch_match_info(session, match_id, limiter) for match_id in batch]
            for future in asyncio.as_completed(tasks):
                match_id, data = await future
                yield match_id, data

def match_info(match_id: int) -> dict | None:
    """
    특정 게임 ID에 대한 상세 정보를 반환합니다.
    """
    url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"match_info - status_code: {response.status_code}")
        return None