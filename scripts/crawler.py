import os
import asyncio
import aiohttp
import random
from dotenv import load_dotenv
import json
from typing import List, Dict, Any, AsyncGenerator, Tuple, Optional, Type, TypeVar
from tqdm.asyncio import tqdm
from aiolimiter import AsyncLimiter
from pydantic import BaseModel, ValidationError

from scripts.logger import logger
from scripts.config import URL_JSON_PATH
from scripts.schemas import UserBase, MatchResponse, TopRankerResponse

# .env 파일에서 환경 변수 로드
load_dotenv()

# URL 로드
with open(URL_JSON_PATH) as f:
    URLS = json.load(f)

BASE_URL = URLS['base_url']

T = TypeVar('T', bound=BaseModel)

class ERAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API Key is missing. Set API_KEY env var or pass it to constructor.")
        
        self.headers = {
            "accept": "application/json",
            "x-api-key": self.api_key
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.limiter = AsyncLimiter(50, 1)  # 50 requests per second

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _fetch_json(
        self,
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        response_model: Optional[Type[T]] = None
    ) -> Any | T | None:
        """
        재시도 로직과 API 호출 제한량을 포함하여 JSON을 가져오는 내부 메서드.
        """
        if not self.session:
            raise RuntimeError("Client session is not initialized. Use 'async with ERAPIClient() as client:'.")

        for attempt in range(max_retries):
            try:
                async with self.limiter:
                    pass

                async with self.session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        raw_data = await response.json()
                        
                        # 1. Pydantic Validation
                        if response_model:
                            try:
                                validated_data = response_model.parse_obj(raw_data)
                                return validated_data
                            except ValidationError as ve:
                                logger.error(f"Validation error for url {url}: {ve}")
                                return None
                        
                        # 2. Basic Validation
                        if raw_data.get("code") == 200:
                            return raw_data
                        elif raw_data.get("code") == 429:
                            logger.warning(f"API Rate limit (429 internal) hit for url: {url}. Retrying...")
                        else:
                            logger.error(f"API internal error - url: {url}, code: {raw_data.get('code')}, message: {raw_data.get('message')}")
                            return None
                    
                    elif response.status == 429:
                        logger.warning(f"HTTP 429 Rate limit hit for url: {url}. Retrying...")
                    elif response.status == 404:
                        return None
                    elif 500 <= response.status < 600:
                        logger.warning(f"Server error {response.status} for url: {url}. Retrying...")
                    else:
                        logger.error(f"HTTP error - url: {url}, status: {response.status}")
                        return None

                    delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Network error for url {url}: {e}. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error for url {url}: {e}", exc_info=True)
                return None

        logger.error(f"Failed to fetch after {max_retries} attempts for url: {url}")
        return None

    async def get_character(self):
        character_url = f"{BASE_URL}{URLS['data']['character']}"
        character_levelup_url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"
        
        data_c = await self._fetch_json(character_url)
        data_cl = await self._fetch_json(character_levelup_url)
        
        if data_c and data_cl:
            return data_c, data_cl
        return None

    async def get_equipment(self):
        url_armor = f"{BASE_URL}{URLS['data']['item_armor']}"
        url_weapon = f"{BASE_URL}{URLS['data']['item_weapon']}"
        
        data_armor = await self._fetch_json(url_armor)
        data_weapon = await self._fetch_json(url_weapon)
        
        if data_armor and data_weapon:
            return data_armor, data_weapon
        return None
        
    async def get_trait(self) -> dict | None:
        url = f"{BASE_URL}{URLS['data']['trait']}"
        return await self._fetch_json(url)
        
    async def get_monster(self) -> dict | None:
        url = f"{BASE_URL}{URLS['data']['monster']}"    
        return await self._fetch_json(url)
        
    async def get_area(self) -> dict | None:
        url = f"{BASE_URL}{URLS['data']['area']}"    
        return await self._fetch_json(url)
            
    async def get_char_lv(self) -> dict | None:
        url = f"{BASE_URL}{URLS['data']['character_level_up_stat']}"    
        return await self._fetch_json(url)

    async def get_l10n(self) -> List[str] | None:
        url = f"{BASE_URL}{URLS['l10n']['korean']}"
        data = await self._fetch_json(url)
        if data and 'data' in data and 'l10Path' in data['data']:
            l10n_url = data['data']['l10Path']
            try:
                async with self.session.get(l10n_url) as response:
                    if response.status == 200:
                        text_content = await response.text()
                        return text_content.splitlines()
            except Exception as e:
                logger.error(f"get_l10n text file error: {e}")
        return None

    async def get_user_by_nickname(self, nickname: str) -> dict | None:
        url = f"{BASE_URL}{URLS['user']['nickname']}"
        data = await self._fetch_json(url, params={'query': nickname})
        if data and "user" in data:
            return data["user"]
        return None

    async def get_top_ranker(self, season_id: int, matching_mode: int, server_code: int) -> dict | None:
        url = f"{BASE_URL}{URLS['rank']['top'].format(season_id=season_id, matching_mode=matching_mode, server_code=server_code)}"
        data = await self._fetch_json(url, response_model=TopRankerResponse)
        return data.dict() if data else None

    async def fetch_user_by_nickname_async(self, nickname: str) -> Dict[str, Any] | None:
        url = f"{BASE_URL}{URLS['user']['nickname']}"
        data = await self._fetch_json(url, params={'query': nickname})
        if data and "user" in data:
            user_obj = data["user"]
            try:
                UserBase.parse_obj(user_obj)
                return user_obj
            except ValidationError as ve:
                logger.error(f"User validation error for {nickname}: {ve}")
        return None

    async def get_users_by_nickname_async(self, nicknames: List[str]) -> List[Dict[str, Any]]:
        tasks = [self.fetch_user_by_nickname_async(nickname) for nickname in nicknames]
        results = await asyncio.gather(*tasks)
        return [user for user in results if user]

    async def fetch_user_games(self, url: str) -> Tuple[int, dict]:
        data = await self._fetch_json(url, response_model=MatchResponse)
        if data:
            return 200, data.dict()
        return 404, None 

    async def get_user_games_by_uid_async(self, users: List[Dict[str, Any]]) -> AsyncGenerator[Dict[str, Any], None]:
        async def process_user(user) -> dict:
            uid = user['uid']
            last_match_id = user['last_match_id']
            new_match_ids = []
            next_page = None
            
            while True:
                url = f"{BASE_URL}{URLS['user']['games'].format(uid=uid)}"
                if next_page:
                    url += f"?next={next_page}"

                status, data = await self.fetch_user_games(url)

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

        tasks = [process_user(user) for user in users]
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching user games"):
            user_result = await future
            yield user_result

    async def fetch_match_info(self, match_id: int):
        url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
        data = await self._fetch_json(url, response_model=MatchResponse)
        return match_id, data.dict() if data else None

    async def get_match_infos_async(self, match_ids: List[int], batch_size: int = 100) -> AsyncGenerator[Tuple[int, Any], None]:
        for i in range(0, len(match_ids), batch_size):
            batch = match_ids[i:i + batch_size]
            tasks = [self.fetch_match_info(match_id) for match_id in batch]
            for future in asyncio.as_completed(tasks):
                match_id, data = await future
                if data:
                    yield match_id, data

    async def match_info(self, match_id: int) -> dict | None:
        url = f"{BASE_URL}{URLS['games']['details'].format(match_id=match_id)}"
        data = await self._fetch_json(url, response_model=MatchResponse)
        return data.dict() if data else None
