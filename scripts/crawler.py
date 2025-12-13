import os
import asyncio
import aiohttp
import random
from dotenv import load_dotenv
import json
from typing import List, Dict, Any, AsyncGenerator, Tuple
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

async def fetch_json(session: aiohttp.ClientSession, url: str) -> Any | None:
    """JSON 데이터를 가져옵니다."""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"fetch_json - url: {url}, status_code: {response.status}")
                return None
    except Exception as e:
        logger.error(f"fetch_json error - url: {url}, error: {e}")
        return None

async def get_character(session: aiohttp.ClientSession):
    character_url = f"{BASE_URL}{URLS['data']['character']}"
    character_levelup_url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"
    
    data_c = await fetch_json(session, character_url)
    data_cl = await fetch_json(session, character_levelup_url)
    
    if data_c and data_cl:
        return data_c, data_cl
    return None

async def get_equipment(session: aiohttp.ClientSession):
    url_armor = f"{BASE_URL}{URLS['data']['item_armor']}"
    url_weapon = f"{BASE_URL}{URLS['data']['item_weapon']}"
    
    data_armor = await fetch_json(session, url_armor)
    data_weapon = await fetch_json(session, url_weapon)
    
    if data_armor and data_weapon:
        return data_armor, data_weapon
    return None
    
async def get_trait(session: aiohttp.ClientSession) -> dict | None:
    url = f"{BASE_URL}{URLS['data']['trait']}"
    return await fetch_json(session, url)
    
async def get_monster(session: aiohttp.ClientSession) -> dict | None:
    url = f"{BASE_URL}{URLS['data']['monster']}"    
    return await fetch_json(session, url)
    
async def get_area(session: aiohttp.ClientSession) -> dict | None:
    url = f"{BASE_URL}{URLS['data']['area']}"    
    return await fetch_json(session, url)
        
async def get_char_lv(session: aiohttp.ClientSession) -> dict | None:
    url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"    
    return await fetch_json(session, url)

async def get_l10n(session: aiohttp.ClientSession) -> List[str] | None:
    url = f"{BASE_URL}{URLS['l10n']['korean']}"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                l10n = await response.json()
                l10n_url = l10n['data']["l10Path"]
                
                async with session.get(l10n_url) as file_response:
                    if file_response.status == 200:
                        text_content = await file_response.text()
                        return text_content.splitlines()
                    else:
                         logger.error(f"get ln10n text file - status_code: {file_response.status}")
            else:
                logger.error(f"get_l10n - status_code: {response.status}")
    except Exception as e:
        logger.error(f"get_l10n error: {e}")
    return None

async def get_user_by_nickname(session: aiohttp.ClientSession, nickname: str) -> dict | None:
    """닉네임으로 유저 정보를 조회합니다."""
    url = f"{BASE_URL}{URLS['user']['nickname']}"
    try:
        async with session.get(url, params={'query': nickname}) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("code") == 200 and "user" in data:
                    return data["user"]
            logger.error(f"get_user_by_nickname for {nickname} - status_code: {response.status}")
    except Exception as e:
        logger.error(f"get_user_by_nickname error: {e}")
    return None

async def get_top_ranker(session: aiohttp.ClientSession, season_id: int, matching_mode: int, server_code: int) -> dict | None:
    """상위 랭커 정보를 반환합니다."""
    url = f"{BASE_URL}{URLS['rank']['top'].format(season_id=season_id, matching_mode=matching_mode, server_code=server_code)}"
    return await fetch_json(session, url)

async def fetch_user_by_nickname_async(session, nickname: str, limiter: AsyncLimiter) -> Dict[str, Any] | None:
    """닉네임으로 유저 정보를 조회합니다.(비동기방식)"""
    url = f"{BASE_URL}{URLS['user']['nickname']}"
    async with limiter:
        try:
            async with session.get(url, params={'query': nickname}) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 200 and "user" in data:
                        user_obj = data["user"]
                        if user_obj and 'userId' in user_obj:
                            return user_obj
                        else:
                            logger.error(f"API returned a user object without a 'userId' for nickname '{nickname}': {user_obj}")
                            return None
                    else:
                        logger.warning(f"API returned a non-200 internal code for nickname '{nickname}'. Status: {response.status}, Data: {data}")
                        return None
                else:
                    logger.error(f"fetch_user_by_nickname_async for {nickname} - status: {response.status}, response: {await response.text()}")
                    return None
        except Exception as e:
            logger.error(f"An exception occurred in fetch_user_by_nickname_async for '{nickname}': {e}", exc_info=True)
            return None

async def get_users_by_nickname_async(nicknames: List[str]) -> List[Dict[str, Any]]:
    """비동기적으로 여러 닉네임에 대한 사용자 정보를 조회합니다."""
    limiter = AsyncLimiter(50, 1)  # API 속도 제한
    async with aiohttp.ClientSession(headers=HEADERS_WITH_KEY) as session:
        tasks = [fetch_user_by_nickname_async(session, nickname, limiter) for nickname in nicknames]
        results = await asyncio.gather(*tasks)
        return [user for user in results if user]

async def fetch_user_games(session, url: str, limiter: AsyncLimiter, max_retries: int = 5, delay: int = 1) -> Tuple[int, dict]:
    """유저의 match 정보를 가져옵니다.(비동기방식)"""
    for attempt in range(max_retries):
        try:
            async with limiter:
                async with session.get(url) as response:
                    if response.status == 200:
                        return 200, await response.json()
                    elif response.status == 404:
                        logger.warning(f"fetch_user_games - User not found (404) for url: {url}")
                        return 404, None # 유저를 찾을 수 없음
                    
                    retry_delay = delay + random.uniform(0, 1)
                    logger.warning(f"fetch_user_games - status_code: {response.status}. Retrying in {retry_delay:.2f}s... (Attempt {attempt + 1}/{max_retries}) for url: {url}")
        
        except aiohttp.client_exceptions.ClientPayloadError as e:
            retry_delay = delay + random.uniform(0, 1)
            logger.warning(f"Fetch failed with ClientPayloadError for url {url}: {e}. Retrying in {retry_delay:.2f}s... (Attempt {attempt + 1}/{max_retries})")

        await asyncio.sleep(retry_delay)

    logger.error(f"fetch_user_games - Failed to fetch after {max_retries} attempts for url: {url}")
    return 500, None # 모든 재시도 실패

async def get_user_games_by_uid_async(users: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
    """
    여러 사용자의 신규 게임 ID를 수집하고 생성합니다.(비동기방식)
    """
    limiter = AsyncLimiter(50, 1)

    async def process_user(session, user) -> dict:
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

async def match_info(session: aiohttp.ClientSession, match_id: int) -> dict | None:
    """
    특정 게임 ID에 대한 상세 정보를 반환합니다.
    """
    url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
    return await fetch_json(session, url)
