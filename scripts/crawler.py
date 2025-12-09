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

def get_user_by_nickname(nickname: str) -> dict | None:
    """닉네임으로 유저 정보를 조회합니다."""
    url = f"{BASE_URL}{URLS['user']['nickname']}"
    response = requests.get(url, headers=HEADERS_WITH_KEY, params={'query': nickname})
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 200 and "user" in data:
            return data["user"]
    logger.error(f"get_user_by_nickname for {nickname} - status_code: {response.status_code}, response: {response.text}")
    return None

async def fetch_user_by_nickname_async(session, nickname: str, limiter: AsyncLimiter) -> Dict[str, Any] | None:
    """닉네임으로 유저 정보를 조회합니다.(비동기방식)"""
    url = f"{BASE_URL}{URLS['user']['nickname']}"
    async with limiter:
        try:
            async with session.get(url, params={'query': nickname}) as response:
                if response.status == 200:
                    data = await response.json()
                    # API가 200을 반환했으나, 내부적으로 에러 코드(e.g., 404)를 포함할 수 있음
                    if data.get("code") == 200 and "user" in data:
                        user_obj = data["user"]
                        if user_obj and 'userId' in user_obj:
                            return user_obj
                        else:
                            logger.error(f"API returned a user object without a 'userId' for nickname '{nickname}': {user_obj}")
                            return None
                    else:
                        # 200이지만, 내용이 에러인 경우 로깅
                        logger.warning(f"API returned a non-200 internal code for nickname '{nickname}'. Status: {response.status}, Data: {data}")
                        return None
                else:
                    # HTTP 상태 코드가 200이 아닌 경우 로깅
                    logger.error(f"fetch_user_by_nickname_async for {nickname} - status: {response.status}, response: {await response.text()}")
                    return None
        except Exception as e:
            # aiohttp, json 디코딩 등 모든 예외 처리
            logger.error(f"An exception occurred in fetch_user_by_nickname_async for '{nickname}': {e}", exc_info=True)
            return None

async def get_users_by_nickname_async(nicknames: List[str]) -> List[Dict[str, Any]]:
    """비동기적으로 여러 닉네임에 대한 사용자 정보를 조회합니다."""
    limiter = AsyncLimiter(50, 1)  # API 속도 제한
    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        tasks = [fetch_user_by_nickname_async(session, nickname, limiter) for nickname in nicknames]
        results = await asyncio.gather(*tasks)
        return [user for user in results if user]

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

async def get_user_games_by_uid_async(users: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    여러 사용자의 신규 게임 ID를 수집하고 생성합니다.(비동기방식)
    - 404 에러 발생 시 해당 유저를 비활성화 대상으로 표시합니다.
    - last_match_id 이후의 게임만 수집합니다.
    """
    limiter = AsyncLimiter(50, 1)

    async def process_user(session, user) -> dict:
        """한 명의 유저에 대한 모든 신규 매치 기록을 페이지네이션하며 수집합니다."""
        uid = user['uid']
        last_match_id = user['last_match_id']
        new_match_ids = []
        next_page = None
        
        while True:
            url = f"{BASE_URL}{URLS['user']['games'].format(uid=uid)}"
            if next_page:
                url += f"?next={next_page}"

            status, data = await fetch_user_games(session, url, limiter)

            if status == 404:
                return {'uid': uid, 'status': 'deactivated'}
            
            if status != 200 or not data or "userGames" not in data:
                break 

            stop_crawling = False
            for game in data["userGames"]:
                if game["gameId"] <= last_match_id:
                    stop_crawling = True
                    break
                if game.get("matchingMode") == 3:
                    new_match_ids.append(game["gameId"])
            
            if stop_crawling or not data.get('next'):
                break
            
            next_page = data['next']
        
        return {'uid': uid, 'status': 'success', 'matches': new_match_ids}

    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        tasks = [process_user(session, user) for user in users]
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching user games"):
            user_result = await future
            yield user_result


async def fetch_match_info(session, match_id, limiter: AsyncLimiter, max_retries: int = 3, delay: int = 1):
    """비동기적으로 단일 게임 정보를 가져옵니다."""
    url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
    for attempt in range(max_retries):
        async with limiter:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 200:
                        return match_id, data
                
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
                if data:
                    yield match_id, data


def match_info(match_id: int) -> dict | None:
    """
    특정 게임 ID에 대한 상세 정보를 반환합니다.
    """
    url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
    response = requests.get(url, headers=HEADERS_WITH_KEY)

    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 200:
            return data
    logger.error(f"match_info - match_id: {match_id}, status_code: {response.status_code}, response: {response.text}")
    return None